"""LangGraph StateGraph for the Nutrition Agent (Batch Architecture).

This module defines the graph structure for the Plan-and-Execute nutrition agent:
- 6 nodes: data_collection, calculation, recipe_generation_batch,
           recipe_generation_single, meal_review_batch, validation
- Conditional edges for routing based on state
- HITL support via interrupt() in meal_review_batch

Graph Flow:
    START → data_collection ←──┐ (loop if missing fields)
                │               │
                ▼               │
           calculation ─────────┘
                │
                ▼
    recipe_generation_batch ◄──────────────────┐
                │                              │
                ▼                              │
       meal_review_batch ──────────────────────┤ (regenerate_all)
                │           │                  │
                │           └──────────────────┤ (change_meal)
                │                              │
                ▼         recipe_generation_single
           validation ─────────────────────────┘ (validation_errors)
                │
                ▼
               END
"""

from langgraph.graph import END, StateGraph

from src.nutrition_agent.nodes import (
    calculation,
    data_collection,
    meal_review_batch,
    recipe_generation_batch,
    recipe_generation_single,
    validation,
)
from src.nutrition_agent.state import NutritionAgentState


def route_after_data_collection(state: NutritionAgentState) -> str:
    """Decide whether to continue collecting data or proceed to calculation.

    Returns:
        "data_collection" if profile incomplete, "calculation" otherwise
    """
    if state.user_profile is None or state.missing_fields:
        return "data_collection"
    return "calculation"


def route_after_meal_review_batch(state: NutritionAgentState) -> str:
    """Route based on user's HITL review decision.

    Returns:
        - "validation" if approved
        - "recipe_generation_single" if changing one meal
        - "recipe_generation_batch" if regenerating all
    """
    routes = {
        "approve": "validation",
        "change_meal": "recipe_generation_single",
        "regenerate_all": "recipe_generation_batch",
    }
    return routes.get(state.review_decision or "", "validation")


def route_after_validation(state: NutritionAgentState) -> str:
    """Decide if plan is valid or needs correction.

    Returns:
        "__end__" if valid, "recipe_generation_batch" if validation errors
    """
    if state.validation_errors:
        return "recipe_generation_batch"
    return str(END)


# Build the graph
builder = StateGraph(NutritionAgentState)

# Add nodes (6 total for batch architecture)
builder.add_node("data_collection", data_collection)
builder.add_node("calculation", calculation)
builder.add_node("recipe_generation_batch", recipe_generation_batch)
builder.add_node("recipe_generation_single", recipe_generation_single)
builder.add_node("meal_review_batch", meal_review_batch)
builder.add_node("validation", validation)

# Set entry point
builder.set_entry_point("data_collection")

# Add edges
builder.add_conditional_edges(
    "data_collection",
    route_after_data_collection,
    {"data_collection": "data_collection", "calculation": "calculation"},
)

builder.add_edge("calculation", "recipe_generation_batch")

builder.add_edge("recipe_generation_batch", "meal_review_batch")

# Returns to review after single meal change
builder.add_edge("recipe_generation_single", "meal_review_batch")

builder.add_conditional_edges(
    "meal_review_batch",
    route_after_meal_review_batch,
    {
        "validation": "validation",
        "recipe_generation_single": "recipe_generation_single",
        "recipe_generation_batch": "recipe_generation_batch",
    },
)

builder.add_conditional_edges(
    "validation",
    route_after_validation,
    {"recipe_generation_batch": "recipe_generation_batch", END: END},
)

# Compile the graph
graph = builder.compile()
