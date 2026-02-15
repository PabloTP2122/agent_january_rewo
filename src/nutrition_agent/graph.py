"""LangGraph StateGraph for the Nutrition Agent (Batch Architecture).

This module defines the graph structure for the Plan-and-Execute nutrition agent:
- 6 nodes: data_collection, calculation, recipe_generation_batch,
           recipe_generation_single, validation, meal_review_batch
- Conditional edges for routing based on state
- HITL support via interrupt() in meal_review_batch
- Validation runs BEFORE HITL so humans only review validated meals

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
           validation ─────────────────────────┤ (multi-fail → batch)
                │           │                  │
                │      (single fail)           │
                │           ↓                  │
                │   recipe_generation_single ──┘
                │
                ▼  (pass / retries exceeded)
       meal_review_batch
                │
        ┌───────┼──────────────────────┐
        │       │                      │
     approve  change_meal        regenerate_all
        │       ↓                      │
        ▼   recipe_gen_single    recipe_gen_batch
       END
"""

from ag_ui_langgraph.agent import CompiledStateGraph
from langgraph.graph import END, StateGraph
from langgraph.types import Checkpointer

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
    if state.get("user_profile") is None or state.get("missing_fields", []):
        return "data_collection"
    return "calculation"


MAX_VALIDATION_RETRIES = 2


def route_after_validation(state: NutritionAgentState) -> str:
    """Route after validation: pass → HITL, fail → targeted regen.

    Returns:
        - "meal_review_batch" if valid or retries exceeded
        - "recipe_generation_single" if exactly 1 meal failed
        - "recipe_generation_batch" if multiple failures
    """
    errors = state.get("validation_errors", [])
    retry_count = state.get("validation_retry_count", 0)

    if not errors:
        return "meal_review_batch"

    if retry_count >= MAX_VALIDATION_RETRIES:
        return "meal_review_batch"

    if state.get("selected_meal_to_change"):
        return "recipe_generation_single"

    return "recipe_generation_batch"


def route_after_meal_review_batch(state: NutritionAgentState) -> str:
    """Route based on user's HITL review decision.

    Returns:
        - END if approved
        - "recipe_generation_single" if changing one meal
        - "recipe_generation_batch" if regenerating all
    """
    routes = {
        "approve": str(END),
        "change_meal": "recipe_generation_single",
        "regenerate_all": "recipe_generation_batch",
    }
    return routes.get(state.get("review_decision") or "", str(END))


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

# Both generation nodes route to validation (validation before HITL)
builder.add_edge("recipe_generation_batch", "validation")
builder.add_edge("recipe_generation_single", "validation")

builder.add_conditional_edges(
    "validation",
    route_after_validation,
    {
        "meal_review_batch": "meal_review_batch",
        "recipe_generation_single": "recipe_generation_single",
        "recipe_generation_batch": "recipe_generation_batch",
    },
)

builder.add_conditional_edges(
    "meal_review_batch",
    route_after_meal_review_batch,
    {
        END: END,
        "recipe_generation_single": "recipe_generation_single",
        "recipe_generation_batch": "recipe_generation_batch",
    },
)


def make_graph(checkpointer: Checkpointer = None) -> CompiledStateGraph:
    """Compile the nutrition agent graph with an optional checkpointer."""
    return builder.compile(checkpointer=checkpointer)


# Default for langgraph dev / CLI (mode 1: no checkpointer needed)
graph = make_graph()
