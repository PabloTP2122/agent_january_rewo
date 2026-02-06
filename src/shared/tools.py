# File: src/shared/tools.py
"""Shared nutrition tools used by all agents."""

import math

from langchain_core.tools import tool

from src.nutrition_agent.models.tools import VerifyIngredientsInput


@tool("sum_ingredients_kcal", args_schema=VerifyIngredientsInput)  # type: ignore [misc]
def sum_ingredients_kcal(ingredients: list[float], expected_kcal_sum: float) -> str:
    """
    Verifies if ingredient sum matches expected total.

    If discrepancy found, returns the REAL value for immediate correction.
    """
    try:
        # 1. The Mathematical Truth
        calculated_sum = sum(ingredients)

        # 2. Anti-obsessive tolerance (0.5 kcal)
        if math.isclose(calculated_sum, expected_kcal_sum, abs_tol=0.5):
            return "Verification successful: ingredient sum matches total."

        # 3. Prescriptive correction protocol (anti-loop)
        real_total = round(calculated_sum, 2)
        diff = round(real_total - expected_kcal_sum, 2)

        return (
            f"Correction required: real sum is {real_total} kcal "
            f"(difference: {diff} kcal). "
            f"Use {real_total} kcal in your final response."
        )

    except Exception as e:
        return f"Technical error: {str(e)}"
