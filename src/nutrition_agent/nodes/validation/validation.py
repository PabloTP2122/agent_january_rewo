"""Validation node for the nutrition agent.

This node performs deterministic validation (NO LLM) to:
1. Sum total calories from daily_meals
2. Verify global total against target (±5% tolerance)
3. Verify per-meal ingredient kcal sum against budget from meal_distribution (±5%)
4. Output routing hints for targeted single-meal regeneration
5. Build final DietPlan with consolidated shopping list

Uses tools: consolidate_shopping_list
"""

from __future__ import annotations

import re
from typing import Any

from src.nutrition_agent.models import (
    DietPlan,
    Ingredient,
    Macronutrients,
    Meal,
    NutritionalTargets,
    ShoppingListItem,
    UserProfile,
)
from src.nutrition_agent.state import NutritionAgentState

from .tools import consolidate_shopping_list

# Tolerance for calorie validation
CALORIE_TOLERANCE = 0.05  # ±5%


def _ingredients_to_raw_strings(
    ingredients: list[Ingredient],
) -> list[str]:
    """Convert structured Ingredients to raw strings for consolidate_shopping_list.

    Uses cantidad_display to preserve the correct unit (g, ml, unidades)
    instead of hardcoding grams. Strips parenthetical weight context
    (e.g. "3 unidades (150g)" → "3 unidades") so the consolidation regex
    matches the first qty+unit cleanly.

    Args:
        ingredients: List of Ingredient objects

    Returns:
        List of strings like "200g Espinaca", "200ml Leche", "3 unidades Huevo"
    """
    result = []
    for ing in ingredients:
        display = re.sub(r"\s*\([^)]*\)", "", ing.cantidad_display).strip()
        result.append(f"{display} {ing.nombre}")
    return result


def validation(state: NutritionAgentState) -> dict[str, Any]:
    """Validate the complete meal plan and build final DietPlan.

    This node is deterministic (NO LLM). It:
    1. Sums calories from all daily_meals
    2. Compares against target_calories (±5% tolerance)
    3. Builds DietPlan with consolidated shopping list if valid
    4. Returns validation_errors if calorie mismatch

    Args:
        state: Current agent state with daily_meals, nutritional_targets,
               and user_profile

    Returns:
        dict with:
        - validation_errors: List of error messages (empty if valid)
        - final_diet_plan: DietPlan if valid, None otherwise
        - validation_retry_count: Incremented on failure, reset to 0 on success
        - selected_meal_to_change: meal_time if exactly 1 meal failed budget
        - user_feedback: Feedback string for targeted regeneration
    """
    # Handle LangGraph serialization: Pydantic models become dicts after checkpointing
    daily_meals_data = state.get("daily_meals", [])
    if not daily_meals_data:
        return {
            "validation_errors": ["No meals to validate"],
            "final_diet_plan": None,
        }
    daily_meals = [Meal(**m) if isinstance(m, dict) else m for m in daily_meals_data]

    nutritional_targets_data = state.get("nutritional_targets")
    if nutritional_targets_data is None:
        return {
            "validation_errors": ["Missing nutritional targets"],
            "final_diet_plan": None,
        }
    nutritional_targets = (
        NutritionalTargets(**nutritional_targets_data)
        if isinstance(nutritional_targets_data, dict)
        else nutritional_targets_data
    )

    user_profile_data = state.get("user_profile")
    if user_profile_data is None:
        return {
            "validation_errors": ["Missing user profile"],
            "final_diet_plan": None,
        }
    user_profile = (
        UserProfile(**user_profile_data)
        if isinstance(user_profile_data, dict)
        else user_profile_data
    )

    validation_errors: list[str] = []

    # 1. Calculate total calories from all meals
    total_calories = sum(meal.total_calories for meal in daily_meals)
    target_calories = nutritional_targets.target_calories

    # 2. Check calorie tolerance
    error_pct = abs(total_calories - target_calories) / target_calories
    if error_pct > CALORIE_TOLERANCE:
        validation_errors.append(
            f"Total calories ({total_calories:.1f}) differ from target "
            f"({target_calories:.1f}) by {error_pct * 100:.1f}% (max allowed: 5%)"
        )

    # 3. Per-meal ingredient kcal sum vs budget from meal_distribution
    failed_meals: list[tuple[str, str]] = []  # (meal_time, feedback_msg)
    meal_distribution = state.get("meal_distribution")
    if meal_distribution:
        for meal in daily_meals:
            budget = meal_distribution.get(meal.meal_time.value)
            if budget is None:
                validation_errors.append(
                    f"Meal '{meal.title}' ({meal.meal_time.value}): "
                    f"no budget found in meal_distribution"
                )
                continue
            ingredient_kcals_sum = sum(ing.kcal for ing in meal.ingredients)
            meal_error_pct = abs(ingredient_kcals_sum - budget) / budget
            if meal_error_pct > CALORIE_TOLERANCE:
                direction = "below" if ingredient_kcals_sum < budget else "above"
                pct = meal_error_pct * 100
                feedback = (
                    f"ingredient kcal sum {ingredient_kcals_sum:.1f} vs "
                    f"budget {budget:.1f} kcal "
                    f"({pct:.1f}% {direction} target). "
                    f"Adjust portions to reach {budget:.1f} kcal."
                )
                validation_errors.append(
                    f"Meal '{meal.title}' ({meal.meal_time.value}): {feedback}"
                )
                failed_meals.append((meal.meal_time.value, feedback))

    # 4. Check meal count matches expected
    expected_meals = user_profile.number_of_meals
    actual_meals = len(daily_meals)
    if actual_meals != expected_meals:
        validation_errors.append(
            f"Expected {expected_meals} meals but got {actual_meals}"
        )

    # If validation errors, return with routing hints for targeted regeneration
    if validation_errors:
        retry_count = state.get("validation_retry_count", 0)
        result: dict[str, Any] = {
            "validation_errors": validation_errors,
            "final_diet_plan": None,
            "validation_retry_count": retry_count + 1,
        }
        # Targeted regeneration: exactly 1 meal failed budget check
        if len(failed_meals) == 1:
            result["selected_meal_to_change"] = failed_meals[0][0]
            result["user_feedback"] = failed_meals[0][1]
        else:
            result["selected_meal_to_change"] = None
            result["user_feedback"] = None
        return result

    # 5. Consolidate shopping list from all meals
    all_ingredients: list[str] = []
    for meal in daily_meals:
        all_ingredients.extend(_ingredients_to_raw_strings(meal.ingredients))

    shopping_list_raw = consolidate_shopping_list.invoke(
        {"ingredients_raw": all_ingredients}
    )

    # Parse shopping list result (tool returns string with consolidated items)
    shopping_list = _parse_shopping_list(shopping_list_raw)

    # 6. Build final DietPlan
    diet_type_label = (
        "Cetogénica"
        if user_profile.diet_type.value == "keto"
        else "Alta en Proteína"
        if user_profile.objective.value in ["muscle_gain", "fat_loss"]
        else "Balanceada"
    )

    macronutrients = Macronutrients(
        protein_percentage=nutritional_targets.protein_percentage,
        protein_grams=nutritional_targets.protein_grams,
        carbs_percentage=nutritional_targets.carbs_percentage,
        carbs_grams=nutritional_targets.carbs_grams,
        fat_percentage=nutritional_targets.fat_percentage,
        fat_grams=nutritional_targets.fat_grams,
    )

    final_diet_plan = DietPlan(
        diet_type=diet_type_label,
        total_calories=total_calories,
        macronutrients=macronutrients,
        daily_meals=list(daily_meals),
        shopping_list=shopping_list,
        day_identifier=1,  # Single day plan
    )

    return {
        "validation_errors": [],
        "final_diet_plan": final_diet_plan,
        "validation_retry_count": 0,
        "selected_meal_to_change": None,
        "user_feedback": None,
    }


def _parse_shopping_list(raw_result: str) -> list[ShoppingListItem]:
    """Parse consolidated shopping list string into ShoppingListItem list.

    Args:
        raw_result: String from consolidate_shopping_list tool
                   Format: "- Item: quantity\\n- Item: quantity\\n..."

    Returns:
        List of ShoppingListItem objects
    """
    items: list[ShoppingListItem] = []

    if not raw_result or raw_result.startswith("Error"):
        return items

    for line in raw_result.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("- "):
            continue

        # Remove "- " prefix
        line = line[2:]

        # Try to split by ": " to get food and quantity
        if ": " in line:
            parts = line.split(": ", 1)
            food = parts[0].strip()
            quantity = (
                parts[1].strip() if len(parts) > 1 else "cantidad no especificada"
            )
        else:
            # No separator, use entire line as food
            food = line
            quantity = "cantidad no especificada"

        if food:
            items.append(ShoppingListItem(food=food, quantity=quantity))

    return items
