# File: src/shared/__init__.py
"""Shared utilities for nutrition agents."""

from src.shared.enums import ActivityLevel, DietType, MealTime, Objective
from src.shared.llm import get_llm
from src.shared.tools import (
    sum_ingredients_kcal,
)

__all__ = [
    # Enums
    "ActivityLevel",
    "Objective",
    "DietType",
    "MealTime",
    # LLM
    "get_llm",
    # Tools
    "sum_ingredients_kcal",
    # Auxiliary classes
]
