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
    <main
      className="space-y-6"
      role="main"
      aria-label="Plan nutricional"
    >
      {/* Screen reader announcement for plan loaded */}
      <div className="sr-only" role="status" aria-live="polite">
        Plan nutricional cargado: {dietPlan.diet_type} con {dietPlan.total_calories} calorías
        y {dietPlan.daily_meals.length} comidas
      </div>

      {/* Debug Panel */}
      {showDebug && debug && <CanvasDebugPanel debug={debug} />}

      {/* Header: Diet Type & Calories */}
      <section
        className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow duration-300"
        aria-labelledby="diet-summary-heading"
      >
        <h1 id="diet-summary-heading" className="sr-only">
          Resumen del plan nutricional
        </h1>
        <DietInfoHeader
          dietType={dietPlan.diet_type}
          totalCalories={dietPlan.total_calories}
        />
        <MacrosTable
          macros={dietPlan.macronutrients}
          totalCalories={dietPlan.total_calories}
        />
      </section>

      {/* Meals with staggered entrance animation */}
      <section aria-label="Comidas del día">
        <h2 className="sr-only">Comidas del día</h2>
        {dietPlan.daily_meals.map((meal, index) => (
          <MealCard
            key={`${meal.meal_time}-${index}`}
            meal={meal}
            animationIndex={index + 1}
          />
        ))}
      </section>

      {/* Shopping List */}
      {dietPlan.shopping_list.length > 0 && (
        <section aria-label="Lista de compras">
          <ShoppingList items={dietPlan.shopping_list} />
        </section>
      )}
    </main>
  );
}
