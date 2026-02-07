"use client";

import { useState, useCallback } from "react";
import {
  MOCK_AGENT_STATE,
  MOCK_EMPTY_STATE,
  MOCK_HITL_STATE,
  MOCK_DIET_PLAN,
} from "@/lib/mock-data";
import type { NutritionAgentState, UserProfile } from "@/lib/types";

export type MockScenario = "complete" | "empty" | "hitl";

/**
 * Mock data hook for Phase 1 development.
 * Replace with useNutritionAgent in Phase 3.
 */
export function useMockData(scenario: MockScenario = "complete") {
  const getInitialState = () => {
    switch (scenario) {
      case "empty":
        return MOCK_EMPTY_STATE;
      case "hitl":
        return MOCK_HITL_STATE;
      case "complete":
      default:
        return MOCK_AGENT_STATE;
    }
  };

  const [state, setState] = useState<Partial<NutritionAgentState>>(getInitialState());
  const [running, setRunning] = useState(false);

  const start = useCallback(() => setRunning(true), []);
  const stop = useCallback(() => setRunning(false), []);

  const userProfile = state.user_profile ?? null;

  const setUserProfile = useCallback((profile: UserProfile) => {
    setState((prev) => ({ ...prev, user_profile: profile }));
  }, []);

  const setScenario = useCallback((newScenario: MockScenario) => {
    switch (newScenario) {
      case "empty":
        setState(MOCK_EMPTY_STATE);
        break;
      case "hitl":
        setState(MOCK_HITL_STATE);
        break;
      case "complete":
      default:
        setState(MOCK_AGENT_STATE);
        break;
    }
  }, []);

  return {
    state,
    setState,
    running,
    start,
    stop,
    userProfile,
    setUserProfile,
    setScenario,
    dietPlan: state.final_diet_plan ?? (scenario === "complete" ? MOCK_DIET_PLAN : null),
  };
}
