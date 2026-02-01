"""Calculation node for the nutrition agent.

This node performs deterministic calculations (NO LLM) to compute:
1. BMR, TDEE, target calories (via generate_nutritional_plan tool)
2. Macronutrient distribution (protein, carbs, fat)
3. Meal calorie distribution

Uses shared tools: generate_nutritional_plan, get_meal_distribution
"""

from typing import Any

from src.nutrition_agent.models import NutritionalTargets, UserProfile
from src.nutrition_agent.state import NutritionAgentState

from .tools import generate_nutritional_plan, get_meal_distribution


def calculation(state: NutritionAgentState) -> dict[str, Any]:
    """Calculate nutritional targets and meal distribution.

    This node is deterministic (NO LLM). It delegates calculations to
    the shared generate_nutritional_plan tool for consistency and DRY.

    Args:
        state: Current agent state with user_profile

    Returns:
        dict with:
        - nutritional_targets: NutritionalTargets model
        - meal_distribution: dict mapping meal names to calories
    """
    profile_data = state.get("user_profile")
    if profile_data is None:
        raise ValueError("user_profile is required for calculation")

    # Handle dict from LangGraph state serialization
    if isinstance(profile_data, dict):
        profile = UserProfile(**profile_data)
    else:
        profile = profile_data

    # 1. Calculate BMR, TDEE, target calories, and macros using shared tool
    plan_result: dict[str, Any] = generate_nutritional_plan.invoke(
        {
            "age": profile.age,
            "gender": profile.gender,
            "weight": profile.weight,
            "height": profile.height,
            "activity_level": profile.activity_level,
            "objective": profile.objective,
            "diet_type": profile.diet_type,
        }
    )

    # 2. Handle potential errors from the tool
    if "error" in plan_result:
        raise ValueError(f"Nutritional plan calculation failed: {plan_result['error']}")

    # 3. Build NutritionalTargets from tool output
    nutritional_targets = NutritionalTargets(
        bmr=plan_result["bmr"],
        tdee=plan_result["tdee"],
        target_calories=plan_result["target_calories"],
        protein_grams=plan_result["protein_grams"],
        protein_percentage=plan_result["protein_percentage"],
        carbs_grams=plan_result["carbs_grams"],
        carbs_percentage=plan_result["carbs_percentage"],
        fat_grams=plan_result["fat_grams"],
        fat_percentage=plan_result["fat_percentage"],
    )

    # 4. Calculate meal distribution using shared tool
    meal_distribution: dict[str, float] = get_meal_distribution.invoke(
        {
            "total_calories": plan_result["target_calories"],
            "number_of_meals": profile.number_of_meals,
        }
    )

    return {
        "nutritional_targets": nutritional_targets,
        "meal_distribution": meal_distribution,
    }
