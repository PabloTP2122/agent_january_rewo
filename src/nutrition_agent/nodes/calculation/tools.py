"""get_meal_distribution, generate_nutritional_plan"""

from typing import Any

from langchain_core.tools import tool

from ...models.tools import (
    ActivityLevel,
    DietType,
    MealDistInput,
    NutritionalInput,
    NutritionalPlanOutput,
    Objective,
)


# Business Logic (Encapsulation)
def _calculate_bmr_mifflin(
    weight: int,
    height: int,
    age: int,
    gender: str,
) -> float:
    """Internal deterministic BMR calculation."""
    base = (10 * weight) + (6.25 * height) - (5 * age)
    return base + 5 if gender.lower() in ["male", "masculine"] else base - 161


def _get_activity_multiplier(level: ActivityLevel) -> float:
    """Get TDEE multiplier for activity level."""
    mapping = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHTLY_ACTIVE: 1.375,
        ActivityLevel.MODERATELY_ACTIVE: 1.55,
        ActivityLevel.VERY_ACTIVE: 1.725,
        ActivityLevel.EXTRA_ACTIVE: 1.9,
    }
    return mapping[level]


@tool("generate_nutritional_plan", args_schema=NutritionalInput)  # type: ignore [misc]
def generate_nutritional_plan(
    age: int,
    gender: str,
    weight: int,
    height: int,
    activity_level: ActivityLevel,
    objective: Objective,
    diet_type: DietType = DietType.NORMAL,
) -> dict[str, Any]:
    """
    Calculates daily caloric needs and macronutrient distribution.

    Use this tool when the user provides their physical data
    and wants a diet plan or to know how many calories to consume.
    DO NOT use if data like weight or height is missing.

    Returns:
        dict with nutritional data: bmr, tdee, target_calories,
        protein/carbs/fat grams and percentages, diet_type, objective.
        On error, returns dict with "error" and "message" keys.
    """
    try:
        # 1. "Hands": Pure mathematical calculations
        bmr = _calculate_bmr_mifflin(weight, height, age, gender)
        tdee = bmr * _get_activity_multiplier(activity_level)

        # Objective adjustment mapping (hidden from LLM)
        objective_adjustments = {
            Objective.FAT_LOSS: 0.83,
            Objective.MUSCLE_GAIN: 1.15,
            Objective.MAINTENANCE: 1.0,
        }

        target_calories = round(tdee * objective_adjustments[objective])

        # Macro logic
        if diet_type == DietType.KETO:
            p_grams = (target_calories * 0.25) / 4
            f_grams = (target_calories * 0.70) / 9
            c_grams = (target_calories * 0.05) / 4

            # Percentages for keto (fixed)
            p_pct = 25.0
            c_pct = 5.0
            f_pct = 70.0
        else:
            # Normal logic: Protein indexed to weight, rest adjusts
            p_mult = (
                2.2 if objective in [Objective.FAT_LOSS, Objective.MUSCLE_GAIN] else 1.6
            )
            p_grams = weight * p_mult
            f_grams = weight * 0.9  # 0.9g/kg fat base

            remaining_cals = target_calories - (p_grams * 4) - (f_grams * 9)
            c_grams = max(0, remaining_cals / 4)

            # Calculate percentages from actual macro grams
            total_macro_cals = (p_grams * 4) + (c_grams * 4) + (f_grams * 9)
            if total_macro_cals > 0:
                p_pct = (p_grams * 4 / total_macro_cals) * 100
                c_pct = (c_grams * 4 / total_macro_cals) * 100
                f_pct = (f_grams * 9 / total_macro_cals) * 100
            else:
                p_pct = c_pct = f_pct = 0.0

        # 2. Structured output (validated by Pydantic)
        output = NutritionalPlanOutput(
            bmr=round(bmr, 2),
            tdee=round(tdee, 2),
            target_calories=round(target_calories, 2),
            protein_grams=round(p_grams, 2),
            protein_percentage=round(p_pct, 2),
            carbs_grams=round(c_grams, 2),
            carbs_percentage=round(c_pct, 2),
            fat_grams=round(f_grams, 2),
            fat_percentage=round(f_pct, 2),
            diet_type=diet_type,
            objective=objective,
        )

        result: dict[str, Any] = output.model_dump()
        return result

    except Exception as e:
        # 3. Instructive error message (as dict for consistency)
        return {
            "error": str(e),
            "message": "Calculation error. Verify numeric data is logical.",
        }


@tool("get_meal_distribution", args_schema=MealDistInput)  # type: ignore [misc]
def get_meal_distribution(
    total_calories: float, number_of_meals: int
) -> dict[str, float]:
    """
    Calculates exact caloric distribution per meal.

    Use this tool to know how many calories to assign to Breakfast,
    Lunch, Dinner, etc. based on the user's eating frequency.
    """
    # 1. Distribution patterns (percentages)
    distributions = {
        1: {"Comida Unica (OMAD)": 1.0},
        2: {"Brunch": 0.5, "Cena": 0.5},
        3: {"Desayuno": 0.3, "Comida": 0.4, "Cena": 0.3},
        4: {"Desayuno": 0.25, "Comida": 0.35, "Snack PM": 0.15, "Cena": 0.25},
        5: {
            "Desayuno": 0.25,
            "Snack AM": 0.10,
            "Comida": 0.35,
            "Snack PM": 0.10,
            "Cena": 0.20,
        },
        6: {
            "Desayuno": 0.20,
            "Snack AM": 0.10,
            "Comida": 0.30,
            "Snack PM": 0.10,
            "Cena": 0.20,
            "Recena": 0.10,
        },
    }

    # 2. Strategy selection
    selected_dist = distributions.get(number_of_meals, distributions[6])

    # 3. Calorie calculation
    result = {}
    accumulated = 0

    keys = list(selected_dist.keys())

    for i, meal_name in enumerate(keys):
        percentage = selected_dist[meal_name]

        # Last meal gets remainder to handle decimals
        if i == len(keys) - 1:
            kcal_val = total_calories - accumulated
        else:
            kcal_val = round(total_calories * percentage)
            accumulated += kcal_val

        result[meal_name] = round(kcal_val, 1)

    return result


tools = [
    get_meal_distribution,
    generate_nutritional_plan,
]
