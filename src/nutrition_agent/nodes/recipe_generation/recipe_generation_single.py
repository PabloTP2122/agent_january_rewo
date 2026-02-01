"""Recipe generation single node for the nutrition agent.

This node regenerates a SINGLE specific meal after the user requests
a change during HITL review. It replaces the meal in the daily_meals list
and returns control to meal_review_batch for re-review.

Used when: review_decision == "change_meal"
"""

from __future__ import annotations

from typing import Any

from src.nutrition_agent.models import Meal, NutritionalTargets, UserProfile
from src.nutrition_agent.prompts import (
    RECIPE_GENERATION_PROMPT,
    REGULAR_MEAL_INSTRUCTION,
)
from src.nutrition_agent.state import NutritionAgentState
from src.shared import get_llm

from .tool import calculate_recipe_nutrition

# Constants for pre-validation (same as batch)
MAX_ATTEMPTS = 3
REGULAR_TOLERANCE = 0.05  # ±5%


async def _generate_single_meal_with_feedback(
    meal_time: str,
    target_calories: float,
    user_profile: UserProfile,
    nutritional_targets: NutritionalTargets,
    total_meals: int,
    current_meal_number: int,
    user_feedback: str | None = None,
) -> tuple[Meal | None, str | None]:
    """Generate a single meal with optional user feedback for guidance.

    Similar to the helper in recipe_generation_batch, but incorporates
    user feedback into the prompt when regenerating.

    Args:
        meal_time: The meal time (e.g., "Desayuno", "Comida", "Cena")
        target_calories: Target calories for this meal
        user_profile: User's dietary profile
        nutritional_targets: Calculated nutritional targets
        total_meals: Total number of meals in the day
        current_meal_number: 1-indexed position of this meal
        user_feedback: Optional user feedback to guide regeneration

    Returns:
        Tuple of (Meal or None, error message or None)
    """
    best_meal: Meal | None = None
    best_error = float("inf")

    # Build special instructions with user feedback
    base_instruction = REGULAR_MEAL_INSTRUCTION.format(
        current_meal_number=current_meal_number,
        total_meals=total_meals,
        target_calories=round(target_calories, 1),
    )

    if user_feedback:
        special_instructions = (
            f"{base_instruction}\n\n"
            f"USER FEEDBACK (must be incorporated):\n{user_feedback}"
        )
    else:
        special_instructions = base_instruction

    excluded_foods_str = ", ".join(user_profile.excluded_foods) or "ninguno"
    prompt = RECIPE_GENERATION_PROMPT.format(
        objective=user_profile.objective.value,
        diet_type=user_profile.diet_type.value,
        excluded_foods=excluded_foods_str,
        daily_target_calories=round(nutritional_targets.target_calories, 1),
        daily_protein_grams=round(nutritional_targets.protein_grams, 1),
        daily_carbs_grams=round(nutritional_targets.carbs_grams, 1),
        daily_fat_grams=round(nutritional_targets.fat_grams, 1),
        meal_time=meal_time,
        target_calories=round(target_calories, 1),
        total_meals=total_meals,
        special_instructions=special_instructions,
    )

    llm = get_llm("gpt-4o")
    structured_llm = llm.with_structured_output(Meal)

    for attempt in range(MAX_ATTEMPTS):
        try:
            # 1. Generate meal via LLM
            meal: Meal = await structured_llm.ainvoke(prompt)

            # 2. Validate via RAG (calculate_recipe_nutrition)
            try:
                ingredient_inputs = _parse_ingredients_for_rag(meal.ingredients)
                nutrition_result = await calculate_recipe_nutrition.ainvoke(
                    {"ingredientes": ingredient_inputs}
                )
                actual_kcal = nutrition_result.get(
                    "total_recipe_kcal", meal.total_calories
                )
            except Exception:
                # Fallback to LLM estimate if RAG fails
                actual_kcal = meal.total_calories

            # 3. Check tolerance
            error_pct = abs(actual_kcal - target_calories) / target_calories
            if error_pct <= REGULAR_TOLERANCE:
                meal.total_calories = actual_kcal
                return (meal, None)  # Success

            # Track best attempt
            if error_pct < best_error:
                best_error = error_pct
                best_meal = meal
                best_meal.total_calories = actual_kcal

        except Exception as e:
            if attempt == MAX_ATTEMPTS - 1 and best_meal is None:
                return (None, f"Generation failed: {str(e)}")

    # Return best attempt with error message
    error_msg = (
        f"Failed after {MAX_ATTEMPTS} attempts. Best error: {best_error * 100:.1f}%"
    )
    return (best_meal, error_msg)


def _parse_ingredients_for_rag(ingredients: list[str]) -> list[dict[str, Any]]:
    """Parse ingredient strings to format expected by calculate_recipe_nutrition."""
    import re

    parsed = []
    for ing in ingredients:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gr|gramos)", ing.lower())
        if match:
            peso = float(match.group(1))
            nombre = re.sub(r"\d+(?:\.\d+)?\s*(?:g|gr|gramos)", "", ing).strip()
            nombre = re.sub(r"[()]", "", nombre).strip()
        else:
            nombre = ing.strip()
            peso = 100.0

        if nombre:
            parsed.append({"nombre": nombre, "peso_gramos": peso})

    return parsed


async def recipe_generation_single(state: NutritionAgentState) -> dict[str, Any]:
    """Regenerate a single meal after user requests a change.

    This node is used when the user selects "change_meal" during HITL review.
    It regenerates the specified meal using user feedback as guidance,
    replaces it in the daily_meals list, and resets review_decision to None
    so the user can re-review the updated plan.

    Args:
        state: Current agent state with daily_meals, selected_meal_to_change,
               user_feedback, meal_distribution, user_profile, nutritional_targets

    Returns:
        dict with:
        - daily_meals: Updated list with regenerated meal
        - review_decision: None (reset for re-review)
        - meal_generation_errors: Updated errors dict
    """
    selected_meal_to_change = state.get("selected_meal_to_change")
    if selected_meal_to_change is None:
        raise ValueError("selected_meal_to_change is required")
    meal_distribution = state.get("meal_distribution")
    if meal_distribution is None:
        raise ValueError("meal_distribution is required")

    # Handle LangGraph serialization: Pydantic models become dicts after checkpointing
    user_profile_data = state.get("user_profile")
    if user_profile_data is None:
        raise ValueError("user_profile is required")
    user_profile = (
        UserProfile(**user_profile_data)
        if isinstance(user_profile_data, dict)
        else user_profile_data
    )

    nutritional_targets_data = state.get("nutritional_targets")
    if nutritional_targets_data is None:
        raise ValueError("nutritional_targets is required")
    nutritional_targets = (
        NutritionalTargets(**nutritional_targets_data)
        if isinstance(nutritional_targets_data, dict)
        else nutritional_targets_data
    )

    meal_time_to_change = selected_meal_to_change
    meal_times = list(meal_distribution.keys())
    total_meals = len(meal_times)

    # Find the index of the meal to change
    try:
        meal_index = meal_times.index(meal_time_to_change)
    except ValueError as e:
        raise ValueError(
            f"Meal time '{meal_time_to_change}' not found in distribution"
        ) from e

    # Get target calories for this meal
    target_calories = meal_distribution[meal_time_to_change]

    # Generate new meal with user feedback
    user_feedback = state.get("user_feedback")
    new_meal, error = await _generate_single_meal_with_feedback(
        meal_time=meal_time_to_change,
        target_calories=target_calories,
        user_profile=user_profile,
        nutritional_targets=nutritional_targets,
        total_meals=total_meals,
        current_meal_number=meal_index + 1,
        user_feedback=user_feedback,
    )

    # Update daily_meals list
    # Handle LangGraph serialization: Pydantic models become dicts after checkpointing
    daily_meals_data = state.get("daily_meals", [])
    updated_meals = [Meal(**m) if isinstance(m, dict) else m for m in daily_meals_data]
    if new_meal is not None:
        # Find and replace the meal in the list
        for i, meal in enumerate(updated_meals):
            if meal.meal_time.value == meal_time_to_change:
                updated_meals[i] = new_meal
                break
        else:
            # Meal not found (shouldn't happen), append
            updated_meals.append(new_meal)

    # Update errors
    updated_errors = dict(state.get("meal_generation_errors", {}))  # Copy
    if error:
        updated_errors[meal_time_to_change] = error
    elif meal_time_to_change in updated_errors:
        del updated_errors[meal_time_to_change]

    return {
        "daily_meals": updated_meals,
        "review_decision": None,  # Reset for re-review
        "meal_generation_errors": updated_errors,
        "selected_meal_to_change": None,  # Clear selection
        "user_feedback": None,  # Clear feedback
    }
