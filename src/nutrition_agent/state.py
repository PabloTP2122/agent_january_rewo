"""State definition for the Nutrition Agent (Plan-and-Execute architecture).

This module defines NutritionAgentState, which tracks the agent's progress
through all 5 phases of the nutrition planning workflow:
1. Data Collection - Conversational extraction of UserProfile
2. Calculation - Deterministic TDEE and macro computation
3. Recipe Generation - LLM-generated meals with pre-validation
4. HITL Review - Human approval/rejection per meal
5. Validation - Final calorie verification and DietPlan assembly
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from copilotkit.langgraph import CopilotKitState
from pydantic import Field

from src.nutrition_agent.models import (
    DietPlan,
    Meal,
    NutritionalTargets,
    UserProfile,
)


class NutritionAgentState(CopilotKitState):
    """State for the Plan-and-Execute Nutrition Agent.

    Inherits from CopilotKitState which provides:
    - messages: list[BaseMessage] - Conversation history
    - copilotkit: dict - Frontend actions and context

    Attributes:
        user_profile: Collected user data (age, weight, goals, etc.)
        missing_fields: Fields still needed from user
        nutritional_targets: Calculated TDEE and macros
        meal_distribution: Calorie budget per meal time
        current_meal_index: Index of meal being generated (0-based)
        meals_completed: Accumulator for generated meals (uses reducer)
        review_decision: User's HITL decision for current meal
        user_feedback: Optional feedback when user requests changes
        skip_remaining_reviews: Flag to auto-approve remaining meals
        meals_approved: Indices of approved meals
        validation_errors: Errors found during final validation
        final_diet_plan: The complete validated plan
    """

    # Phase 1: Data Collection
    user_profile: UserProfile | None = None
    missing_fields: list[str] = Field(default_factory=list)

    # Phase 2: Calculation
    nutritional_targets: NutritionalTargets | None = None
    meal_distribution: dict[str, float] | None = None

    # Phase 3: Recipe Generation
    # current_meal_index tracks which meal we're generating (0 to N-1)
    current_meal_index: int = 0
    # meals_completed uses operator.add reducer to accumulate across nodes
    meals_completed: Annotated[list[Meal], operator.add] = Field(default_factory=list)

    # Phase 4: HITL Review
    review_decision: Literal["approve", "change", "skip_all"] | None = None
    user_feedback: str | None = None
    skip_remaining_reviews: bool = False
    meals_approved: list[int] = Field(default_factory=list)

    # Phase 5: Validation
    validation_errors: list[str] = Field(default_factory=list)
    final_diet_plan: DietPlan | None = None
