"""Validation node for the nutrition agent.

This node performs deterministic validation (NO LLM) to:
1. Sum total calories from daily_meals
2. Verify against target (±5% tolerance)
3. Build final DietPlan with consolidated shopping list

Uses shared tools: sum_total_kcal, consolidate_shopping_list
"""

from __future__ import annotations

from typing import Any

from src.nutrition_agent.models import (
    DietPlan,
    Macronutrients,
    ShoppingListItem,
)
from src.nutrition_agent.state import NutritionAgentState
from src.shared import consolidate_shopping_list

# Tolerance for calorie validation
CALORIE_TOLERANCE = 0.05  # ±5%


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
    """
    if state.daily_meals is None or len(state.daily_meals) == 0:
        return {
            "validation_errors": ["No meals to validate"],
            "final_diet_plan": None,
        }
    if state.nutritional_targets is None:
        return {
            "validation_errors": ["Missing nutritional targets"],
            "final_diet_plan": None,
        }
    if state.user_profile is None:
        return {
            "validation_errors": ["Missing user profile"],
            "final_diet_plan": None,
        }

    validation_errors: list[str] = []

    # 1. Calculate total calories from all meals
    total_calories = sum(meal.total_calories for meal in state.daily_meals)
    target_calories = state.nutritional_targets.target_calories

    # 2. Check calorie tolerance
    error_pct = abs(total_calories - target_calories) / target_calories
    if error_pct > CALORIE_TOLERANCE:
        validation_errors.append(
            f"Total calories ({total_calories:.1f}) differ from target "
            f"({target_calories:.1f}) by {error_pct * 100:.1f}% (max allowed: 5%)"
        )

    # 3. Check meal count matches expected
    expected_meals = state.user_profile.number_of_meals
    actual_meals = len(state.daily_meals)
    if actual_meals != expected_meals:
        validation_errors.append(
            f"Expected {expected_meals} meals but got {actual_meals}"
        )

    # If validation errors, return early
    if validation_errors:
        return {
            "validation_errors": validation_errors,
            "final_diet_plan": None,
        }

    # 4. Consolidate shopping list from all meals
    all_ingredients: list[str] = []
    for meal in state.daily_meals:
        all_ingredients.extend(meal.ingredients)

    shopping_list_raw = consolidate_shopping_list.invoke(
        {"ingredients_raw": all_ingredients}
    )

    # Parse shopping list result (tool returns string with consolidated items)
    shopping_list = _parse_shopping_list(shopping_list_raw)

    # 5. Build final DietPlan
    diet_type_label = (
        "Cetogénica"
        if state.user_profile.diet_type.value == "keto"
        else "Alta en Proteína"
        if state.user_profile.objective.value in ["muscle_gain", "fat_loss"]
        else "Balanceada"
    )

    macronutrients = Macronutrients(
        protein_percentage=state.nutritional_targets.protein_percentage,
        protein_grams=state.nutritional_targets.protein_grams,
        carbs_percentage=state.nutritional_targets.carbs_percentage,
        carbs_grams=state.nutritional_targets.carbs_grams,
        fat_percentage=state.nutritional_targets.fat_percentage,
        fat_grams=state.nutritional_targets.fat_grams,
    )

    final_diet_plan = DietPlan(
        diet_type=diet_type_label,
        total_calories=total_calories,
        macronutrients=macronutrients,
        daily_meals=list(state.daily_meals),
        shopping_list=shopping_list,
        day_identifier=1,  # Single day plan
    )

    return {
        "validation_errors": [],
        "final_diet_plan": final_diet_plan,
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
