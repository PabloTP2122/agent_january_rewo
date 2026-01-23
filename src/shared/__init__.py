# File: src/shared/__init__.py
"""Shared utilities for nutrition agents."""

from src.shared.enums import ActivityLevel, DietType, MealTime, Objective
from src.shared.llm import get_llm
from src.shared.tools import (
    NutriFacts,
    NutritionResult,
    ProcessedItem,
    ResourceLoader,
    StrictBaseModel,
    calculate_recipe_nutrition,
    consolidate_shopping_list,
    generate_nutritional_plan,
    get_meal_distribution,
    sum_ingredients_kcal,
    sum_total_kcal,
    tools,
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
    "generate_nutritional_plan",
    "sum_total_kcal",
    "sum_ingredients_kcal",
    "get_meal_distribution",
    "consolidate_shopping_list",
    "calculate_recipe_nutrition",
    "tools",
    # Auxiliary classes
    "StrictBaseModel",
    "ResourceLoader",
    "NutriFacts",
    "ProcessedItem",
    "NutritionResult",
]
