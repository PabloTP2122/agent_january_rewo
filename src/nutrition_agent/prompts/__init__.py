"""Prompt templates for nutrition agent LLM nodes.

Exports:
    DATA_COLLECTION_PROMPT: For conversational UserProfile extraction
    RECIPE_GENERATION_PROMPT: For parallel batch meal generation
    LAST_MEAL_INSTRUCTION: For last meal with exact budget (stricter tolerance)
    REGULAR_MEAL_INSTRUCTION: For regular meals (standard tolerance)

Architecture: Parallel Batch Generation (v2)
- Prompts optimized for independent parallel generation
- No sequential context accumulation (O(n) vs O(n²) tokens)
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
