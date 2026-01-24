"""Prompt templates for nutrition agent LLM nodes.

Exports:
    DATA_COLLECTION_PROMPT: For conversational UserProfile extraction
    RECIPE_GENERATION_PROMPT: For single meal generation
    LAST_MEAL_INSTRUCTION: Appended when generating the last meal
    REGULAR_MEAL_INSTRUCTION: Appended for non-last meals
"""

from src.nutrition_agent.prompts.data_collection import DATA_COLLECTION_PROMPT
from src.nutrition_agent.prompts.recipe_generation import (
    LAST_MEAL_INSTRUCTION,
    RECIPE_GENERATION_PROMPT,
    REGULAR_MEAL_INSTRUCTION,
)

__all__ = [
    "DATA_COLLECTION_PROMPT",
    "RECIPE_GENERATION_PROMPT",
    "LAST_MEAL_INSTRUCTION",
    "REGULAR_MEAL_INSTRUCTION",
]
