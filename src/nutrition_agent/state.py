"""State definition for the Nutrition Agent (Plan-and-Execute architecture).

This module defines NutritionAgentState, which tracks the agent's progress
through all 5 phases of the nutrition planning workflow:
1. Data Collection - Conversational extraction of UserProfile
2. Calculation - Deterministic TDEE and macro computation
3. Recipe Generation - Parallel batch generation of all daily meals
4. HITL Review - Single human review of complete daily plan
5. Validation - Final calorie verification and DietPlan assembly

Architecture: Parallel Batch Generation (v2)
- All meals generated in parallel via asyncio.gather()
- Single HITL review point for complete plan
- ~60% latency reduction vs sequential approach
"""

from __future__ import annotations

from typing import Literal

from copilotkit.langgraph import CopilotKitState
from pydantic import Field

from src.nutrition_agent.models import (
    DietPlan,
    Meal,
    MealNotice,
    NutritionalTargets,
    UserProfile,
)


class NutritionAgentState(CopilotKitState):
    """State for the Plan-and-Execute Nutrition Agent (Batch Architecture).

    Inherits from CopilotKitState which provides:
    - messages: list[BaseMessage] - Conversation history
    - copilotkit: dict - Frontend actions and context

    Attributes:
        user_profile: Collected user data (age, weight, goals, etc.)
        missing_fields: Fields still needed from user
        nutritional_targets: Calculated TDEE and macros
        meal_distribution: Calorie budget per meal time
        daily_meals: All meals generated in parallel batch
        meal_generation_errors: Errors per meal_time during generation
        review_decision: User's HITL decision for complete plan
        user_feedback: Optional feedback when user requests meal change
        selected_meal_to_change: MealTime to regenerate (if change_meal)
        validation_errors: Errors found during final validation
        validation_retry_count: Auto-fix attempts before routing to HITL
        final_diet_plan: The complete validated plan
    """

    # Phase 1: Data Collection
    user_profile: UserProfile | None = None
    missing_fields: list[str] = Field(default_factory=list)

    # Phase 2: Calculation
    nutritional_targets: NutritionalTargets | None = None
    meal_distribution: dict[str, float] | None = None

    # Phase 3: Recipe Generation (PARALLEL BATCH)
    # All meals generated in a single parallel batch via asyncio.gather()
    daily_meals: list[Meal] = Field(default_factory=list)
    # Errors per meal_time if pre-validation fails after max attempts
    meal_generation_errors: dict[str, str] = Field(default_factory=dict)

    # Phase 4: HITL Review (BATCH REVIEW - single review of complete plan)
    # User reviews ALL meals at once and decides:
    # - approve: Accept entire plan, proceed to validation
    # - change_meal: Regenerate one specific meal
    # - regenerate_all: Discard and regenerate all meals
    review_decision: Literal["approve", "change_meal", "regenerate_all"] | None = None
    user_feedback: str | None = None
    # Which meal_time to change (only used if review_decision == "change_meal")
    selected_meal_to_change: str | None = None

    # Phase 5: Validation
    validation_errors: list[str] = Field(default_factory=list)
    validation_retry_count: int = 0
    meal_notices: dict[str, MealNotice] = Field(default_factory=dict)
    final_diet_plan: DietPlan | None = None
