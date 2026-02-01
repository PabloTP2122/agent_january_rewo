"""Meal review batch node for the nutrition agent.

This node implements HITL (Human-in-the-Loop) for batch review of the
complete daily meal plan. The user can:
- Approve the entire plan
- Request to change a specific meal
- Request to regenerate all meals

Uses LangGraph's interrupt() to pause execution and wait for user input.
"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from src.nutrition_agent.models import Meal, NutritionalTargets
from src.nutrition_agent.state import NutritionAgentState


def meal_review_batch(state: NutritionAgentState) -> dict[str, Any]:
    """Review the complete daily meal plan via HITL.

    This node pauses the graph execution and presents the complete
    meal plan to the user for review. The user can:
    - approve: Accept the entire plan and proceed to validation
    - change_meal: Select a specific meal to regenerate with feedback
    - regenerate_all: Discard all meals and regenerate from scratch

    Args:
        state: Current agent state with daily_meals, nutritional_targets,
               and meal_generation_errors

    Returns:
        dict with:
        - review_decision: "approve" | "change_meal" | "regenerate_all"
        - selected_meal_to_change: meal_time if change_meal, else None
        - user_feedback: feedback text if change_meal, else None
    """
    # Get state values using dict access
    # Handle LangGraph serialization: Pydantic models become dicts after checkpointing
    daily_meals_data = state.get("daily_meals", [])
    daily_meals = [Meal(**m) if isinstance(m, dict) else m for m in daily_meals_data]

    nutritional_targets_data = state.get("nutritional_targets")
    nutritional_targets = (
        NutritionalTargets(**nutritional_targets_data)
        if isinstance(nutritional_targets_data, dict) and nutritional_targets_data
        else nutritional_targets_data
    )

    meal_generation_errors = state.get("meal_generation_errors", {})

    # Build interrupt payload with all relevant information
    interrupt_payload = {
        "type": "meal_plan_review",
        "daily_meals": [meal.model_dump() for meal in daily_meals],
        "nutritional_targets": (
            nutritional_targets.model_dump() if nutritional_targets else None
        ),
        "meal_generation_errors": meal_generation_errors,
        "options": [
            {"action": "approve", "label": "Approve Entire Plan"},
            {
                "action": "change_meal",
                "label": "Change Specific Meal",
                "requires": ["meal_time", "feedback"],
            },
            {"action": "regenerate_all", "label": "Regenerate All Meals"},
        ],
    }

    # Pause execution and wait for user decision
    # The interrupt() call will pause the graph and return control to the client
    # The client will resume with a Command containing the user's decision
    user_response = interrupt(interrupt_payload)

    # Parse user response
    # Expected format: {"action": str, "meal_time": str?, "feedback": str?}
    action = user_response.get("action", "approve")

    if action == "approve":
        return {
            "review_decision": "approve",
            "selected_meal_to_change": None,
            "user_feedback": None,
        }
    elif action == "change_meal":
        return {
            "review_decision": "change_meal",
            "selected_meal_to_change": user_response.get("meal_time"),
            "user_feedback": user_response.get("feedback"),
        }
    elif action == "regenerate_all":
        return {
            "review_decision": "regenerate_all",
            "selected_meal_to_change": None,
            "user_feedback": None,
        }
    else:
        # Unknown action, default to approve
        return {
            "review_decision": "approve",
            "selected_meal_to_change": None,
            "user_feedback": None,
        }
