"use client";

import type { AgentPhase, NutritionAgentState } from "@/lib/types";

/**
 * Derives current phase from agent state fields.
 */
export function useAgentPhase(state: Partial<NutritionAgentState>): AgentPhase {
  // Error state
  if (state.validation_errors && state.validation_errors.length > 0) {
    return "error";
  }

  // Complete
  if (state.final_diet_plan) {
    return "complete";
  }

  // HITL Review (meals exist but no decision yet)
  if (state.daily_meals?.length && state.review_decision === null) {
    return "meal_review";
  }

  // Validation (after approval)
  if (state.review_decision === "approve") {
    return "validation";
  }

  // Recipe Generation
  if (state.meal_distribution && !state.daily_meals?.length) {
    return "recipe_generation";
  }

  // Calculation
  if (state.user_profile && !state.nutritional_targets) {
    return "calculation";
  }

  // Data Collection
  if (!state.user_profile || (state.missing_fields && state.missing_fields.length > 0)) {
    return "data_collection";
  }

  return "idle";
}
