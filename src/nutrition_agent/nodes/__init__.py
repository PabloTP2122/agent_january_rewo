"""All nodes for nutrition_agent graph (Batch Architecture).

Node 1: data_collection - LLM extraction of UserProfile
Node 2: calculation - Deterministic TDEE/Macro computation
Node 3: recipe_generation_batch - Parallel batch meal generation
Node 3b: recipe_generation_single - Single meal regeneration for HITL
Node 4: meal_review_batch - HITL batch review
Node 5: validation - Final calorie verification and DietPlan assembly
"""

from src.nutrition_agent.nodes.calculation import calculation
from src.nutrition_agent.nodes.data_collection import data_collection
from src.nutrition_agent.nodes.meal_review_batch import meal_review_batch
from src.nutrition_agent.nodes.recipe_generation_batch import recipe_generation_batch
from src.nutrition_agent.nodes.recipe_generation_single import recipe_generation_single
from src.nutrition_agent.nodes.validation import validation

__all__ = [
    "data_collection",
    "calculation",
    "recipe_generation_batch",
    "recipe_generation_single",
    "meal_review_batch",
    "validation",
]
