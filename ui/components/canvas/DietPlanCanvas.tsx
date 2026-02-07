"use client";

import type { DietPlan, DebugInfo, AgentPhase } from "@/lib/types";
import { DietInfoHeader } from "./DietInfoHeader";
import { MacrosTable } from "./MacrosTable";
import { MealCard } from "./MealCard";
import { ShoppingList } from "./ShoppingList";
import { EmptyCanvas } from "./EmptyCanvas";
import { CanvasDebugPanel } from "./CanvasDebugPanel";

export interface DietPlanCanvasProps {
  dietPlan: DietPlan | null;
  phase: AgentPhase;
  debug?: DebugInfo;
  showDebug?: boolean;
}

export function DietPlanCanvas({
  dietPlan,
  phase,
  debug,
  showDebug = false,
}: DietPlanCanvasProps) {
  // Show empty state if no plan
  if (!dietPlan) {
    return (
      <div className="h-full flex flex-col">
        {showDebug && debug && (
          <div className="p-4 border-b border-gray-200">
            <CanvasDebugPanel debug={debug} />
          </div>
        )}
        <div className="flex-1">
          <EmptyCanvas phase={phase} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Debug Panel */}
      {showDebug && debug && <CanvasDebugPanel debug={debug} />}

      {/* Header: Diet Type & Calories */}
      <div className="bg-white rounded-2xl p-6 shadow-md">
        <DietInfoHeader
          dietType={dietPlan.diet_type}
          totalCalories={dietPlan.total_calories}
        />
        <MacrosTable
          macros={dietPlan.macronutrients}
          totalCalories={dietPlan.total_calories}
        />
      </div>

      {/* Meals */}
      {dietPlan.daily_meals.map((meal, index) => (
        <MealCard key={`${meal.meal_time}-${index}`} meal={meal} />
      ))}

      {/* Shopping List */}
      {dietPlan.shopping_list.length > 0 && (
        <ShoppingList items={dietPlan.shopping_list} />
      )}
    </div>
  );
}
