"use client";

import { useState, useCallback, useMemo } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { MainLayout } from "@/components/layout";
import { DietPlanCanvas, EmptyCanvas, CanvasDebugPanel } from "@/components/canvas";
import { UserProfileForm } from "@/components/forms";
import { MealPlanReview } from "@/components/hitl";
import { useMockData, useAgentPhase, type MockScenario } from "@/hooks";
import type { UserProfile, ReviewDecision, DebugInfo } from "@/lib/types";

export default function Page() {
  const [showDebug, setShowDebug] = useState(false);
  const [scenario, setScenario] = useState<MockScenario>("empty");
  const [elapsedTime, setElapsedTime] = useState(0);

  const {
    state,
    running,
    start,
    userProfile,
    setUserProfile,
    dietPlan,
    setScenario: changeMockScenario,
  } = useMockData(scenario);

  const phase = useAgentPhase(state);

  const debugInfo: DebugInfo = useMemo(
    () => ({
      phase,
      elapsed_seconds: elapsedTime,
      tools_invoked: [],
      last_error: null,
    }),
    [phase, elapsedTime]
  );

  const handleScenarioChange = useCallback(
    (newScenario: MockScenario) => {
      setScenario(newScenario);
      changeMockScenario(newScenario);
    },
    [changeMockScenario]
  );

  const handleProfileSubmit = useCallback(
    (profile: UserProfile) => {
      setUserProfile(profile);
      start();
      // Simulate transition to complete state after form submission
      setTimeout(() => {
        handleScenarioChange("complete");
      }, 1500);
    },
    [setUserProfile, start, handleScenarioChange]
  );

  const handleReviewComplete = useCallback(
    (decision: ReviewDecision, mealTime?: string, feedback?: string) => {
      console.log("Review decision:", { decision, mealTime, feedback });
      // In Phase 3, this will call the CopilotKit resumeAgent
      if (decision === "approve") {
        handleScenarioChange("complete");
      }
    },
    [handleScenarioChange]
  );

  // Render canvas content based on phase
  const renderCanvasContent = () => {
    switch (phase) {
      case "idle":
      case "data_collection":
        return (
          <div className="max-w-2xl mx-auto py-8 px-4">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Plan Nutricional Personalizado
              </h1>
              <p className="text-gray-600">
                Completa tu perfil para generar un plan adaptado a tus objetivos
              </p>
            </div>
            <UserProfileForm
              onSubmit={handleProfileSubmit}
              isSubmitting={running}
            />
          </div>
        );

      case "calculation":
      case "recipe_generation":
        return <EmptyCanvas phase={phase} />;

      case "meal_review":
        return (
          <div className="max-w-3xl mx-auto py-8 px-4">
            <MealPlanReview
              meals={state.daily_meals ?? []}
              nutritionalTargets={state.nutritional_targets ?? null}
              errors={state.meal_generation_errors ?? {}}
              onReviewComplete={handleReviewComplete}
              isSubmitting={running}
            />
          </div>
        );

      case "validation":
        return <EmptyCanvas phase={phase} />;

      case "complete":
        return (
          <DietPlanCanvas
            dietPlan={dietPlan}
            phase={phase}
            debug={debugInfo}
            showDebug={showDebug}
          />
        );

      case "error":
        return <EmptyCanvas phase="error" />;

      default:
        return <EmptyCanvas phase="idle" />;
    }
  };

  // Canvas content with debug controls
  const canvasContent = (
    <>
      {/* Debug Toggle - Development only */}
      <div className="fixed top-4 right-4 z-50 flex gap-2">
        <select
          value={scenario}
          onChange={(e) => handleScenarioChange(e.target.value as MockScenario)}
          className="text-xs px-2 py-1 rounded border border-gray-300 bg-gray-600"
        >
          <option value="empty">Empty State</option>
          <option value="hitl">HITL Review</option>
          <option value="complete">Complete</option>
        </select>
        <button
          onClick={() => setShowDebug(!showDebug)}
          className="text-xs px-2 py-1 rounded bg-gray-600 hover:bg-gray-800"
        >
          {showDebug ? "Hide" : "Show"} Debug
        </button>
      </div>

      {/* Debug Panel */}
      {showDebug && <CanvasDebugPanel debug={debugInfo} />}

      {/* Main Canvas Content */}
      {renderCanvasContent()}
    </>
  );

  // Chat content
  const chatContent = (
    <div className="h-full flex flex-col">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="font-semibold text-gray-900">Asistente Nutricional</h2>
        <p className="text-sm text-gray-500">
          {running ? "Procesando..." : "Listo para ayudarte"}
        </p>
      </div>

      {/* CopilotKit Chat - Phase 3 integration */}
      {/* <div className="flex-1 overflow-hidden">
        <CopilotSidebar
          defaultOpen={true}
          clickOutsideToClose={false}
          className="h-full"
        />
      </div> */}
    </div>
  );

  return (
    <MainLayout
      canvasContent={canvasContent}
      chatContent={chatContent}
    />
  );
}
