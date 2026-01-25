"""Calculation node for the nutrition agent.

This node performs deterministic calculations (NO LLM) to compute:
1. BMR using Mifflin-St Jeor formula
2. TDEE using activity multipliers
3. Target calories adjusted by objective
4. Macronutrient distribution (protein, carbs, fat)
5. Meal calorie distribution

Uses shared tools: get_meal_distribution
"""

from src.nutrition_agent.models import NutritionalTargets
from src.nutrition_agent.state import NutritionAgentState
from src.shared import get_meal_distribution
from src.shared.enums import ActivityLevel, DietType, Objective

# Activity multipliers for TDEE calculation (aligned with tools.py)
ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}

# Objective adjustments (aligned with tools.py: 0.83, 1.15, 1.0)
OBJECTIVE_ADJUSTMENTS: dict[Objective, float] = {
    Objective.FAT_LOSS: 0.83,  # ~17% deficit
    Objective.MUSCLE_GAIN: 1.15,  # 15% surplus
    Objective.MAINTENANCE: 1.0,
}


def _calculate_bmr(weight: int, height: int, age: int, gender: str) -> float:
    """Calculate BMR using Mifflin-St Jeor formula (aligned with tools.py).

    Args:
        weight: Weight in kg
        height: Height in cm
        age: Age in years
        gender: "male" or "female"

    Returns:
        BMR in kcal/day
    """
    base = (10 * weight) + (6.25 * height) - (5 * age)
    return base + 5 if gender.lower() in ["male", "masculine"] else base - 161


def _calculate_macros(
    target_calories: float,
    diet_type: DietType,
    objective: Objective,
    weight: int,
) -> tuple[float, float, float, float, float, float]:
    """Calculate macronutrient distribution (aligned with tools.py).

    Args:
        target_calories: Daily calorie target
        diet_type: normal or keto
        objective: fat_loss, muscle_gain, or maintenance
        weight: User weight in kg

    Returns:
        Tuple of (protein_g, protein_pct, carbs_g, carbs_pct, fat_g, fat_pct)
    """
    if diet_type == DietType.KETO:
        # Keto: 25% protein, 5% carbs, 70% fat (aligned with tools.py)
        protein_pct = 25.0
        carbs_pct = 5.0
        fat_pct = 70.0
        protein_g = (target_calories * 0.25) / 4
        fat_g = (target_calories * 0.70) / 9
        carbs_g = (target_calories * 0.05) / 4
    else:
        # Normal: protein indexed to weight (aligned with tools.py)
        p_mult = (
            2.2 if objective in [Objective.FAT_LOSS, Objective.MUSCLE_GAIN] else 1.6
        )
        protein_g = weight * p_mult
        fat_g = weight * 0.9  # 0.9g/kg fat base

        remaining_cals = target_calories - (protein_g * 4) - (fat_g * 9)
        carbs_g = max(0, remaining_cals / 4)

        # Calculate percentages from grams
        total_macro_cals = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
        protein_pct = (protein_g * 4 / total_macro_cals) * 100
        carbs_pct = (carbs_g * 4 / total_macro_cals) * 100
        fat_pct = (fat_g * 9 / total_macro_cals) * 100

    return protein_g, protein_pct, carbs_g, carbs_pct, fat_g, fat_pct


def calculation(state: NutritionAgentState) -> dict:
    """Calculate nutritional targets and meal distribution.

    This node is deterministic (NO LLM). It computes:
    1. BMR using Mifflin-St Jeor formula
    2. TDEE = BMR × activity multiplier
    3. Target calories = TDEE × objective adjustment
    4. Macronutrient grams and percentages
    5. Meal calorie distribution

    Args:
        state: Current agent state with user_profile

    Returns:
        dict with:
        - nutritional_targets: NutritionalTargets model
        - meal_distribution: dict mapping meal names to calories
    """
    profile = state.user_profile
    if profile is None:
        raise ValueError("user_profile is required for calculation")

    # 1. Calculate BMR (Mifflin-St Jeor)
    bmr = _calculate_bmr(
        weight=profile.weight,
        height=profile.height,
        age=profile.age,
        gender=profile.gender,
    )

    # 2. Calculate TDEE
    activity_mult = ACTIVITY_MULTIPLIERS[profile.activity_level]
    tdee = bmr * activity_mult

    # 3. Calculate target calories (adjusted by objective)
    objective_adj = OBJECTIVE_ADJUSTMENTS[profile.objective]
    target_calories = tdee * objective_adj

    # 4. Calculate macros
    protein_g, protein_pct, carbs_g, carbs_pct, fat_g, fat_pct = _calculate_macros(
        target_calories=target_calories,
        diet_type=profile.diet_type,
        objective=profile.objective,
        weight=profile.weight,
    )

    # 5. Build NutritionalTargets
    nutritional_targets = NutritionalTargets(
        bmr=bmr,
        tdee=tdee,
        target_calories=target_calories,
        protein_grams=protein_g,
        protein_percentage=protein_pct,
        carbs_grams=carbs_g,
        carbs_percentage=carbs_pct,
        fat_grams=fat_g,
        fat_percentage=fat_pct,
    )

    # 6. Calculate meal distribution using shared tool
    meal_distribution = get_meal_distribution.invoke(
        {"total_calories": target_calories, "number_of_meals": profile.number_of_meals}
    )

    return {
        "nutritional_targets": nutritional_targets,
        "meal_distribution": meal_distribution,
    }
