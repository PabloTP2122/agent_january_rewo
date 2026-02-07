"use client";

import type { Meal, NutritionalTargets, ReviewDecision } from "@/lib/types";
import { Card, Badge } from "@/components/ui";
import { MealReviewCard } from "./MealReviewCard";
import { ReviewActionButtons } from "./ReviewActionButtons";

export interface MealPlanReviewViewProps {
  meals: Meal[];
  nutritionalTargets: NutritionalTargets | null;
  errors: Record<string, string>;
  selectedMealTime: string | null;
  feedbackText: string;
  isLoading: boolean;
  onMealSelect: (mealTime: string) => void;
  onFeedbackChange: (feedback: string) => void;
  onAction: (decision: ReviewDecision, mealTime?: string, feedback?: string) => void;
}

export function MealPlanReviewView({
  meals,
  nutritionalTargets,
  errors,
  selectedMealTime,
  feedbackText,
  isLoading,
  onMealSelect,
  onFeedbackChange,
  onAction,
}: MealPlanReviewViewProps) {
  const showChangeMealForm = selectedMealTime !== null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900">Revisar Plan de Comidas</h2>
        <p className="text-sm text-gray-600 mt-1">
          Revisa las comidas generadas y aprueba o solicita cambios
        </p>
      </div>

      {/* Nutritional Summary */}
      {nutritionalTargets && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-sm text-gray-600">Objetivo Calorico</p>
              <p className="text-2xl font-bold text-gray-900">
                {nutritionalTargets.target_calories.toFixed(0)} kcal
              </p>
            </div>
            <div className="flex gap-3">
              <Badge variant="info" size="md">
                P: {nutritionalTargets.protein_grams.toFixed(0)}g
              </Badge>
              <Badge variant="warning" size="md">
                C: {nutritionalTargets.carbs_grams.toFixed(0)}g
              </Badge>
              <Badge variant="error" size="md">
                G: {nutritionalTargets.fat_grams.toFixed(0)}g
              </Badge>
            </div>
          </div>
        </Card>
      )}

      {/* Errors Summary */}
      {Object.keys(errors).length > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <h4 className="font-medium text-amber-800 mb-2">
            Advertencias en la generacion
          </h4>
          <ul className="text-sm text-amber-700 space-y-1">
            {Object.entries(errors).map(([mealTime, error]) => (
              <li key={mealTime}>
                <span className="font-medium">{mealTime}:</span> {error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Meal Cards */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Comidas del Dia</h3>
        <div className="grid gap-4">
          {meals.map((meal) => (
            <MealReviewCard
              key={meal.meal_time}
              meal={meal}
              isSelected={selectedMealTime === meal.meal_time}
              onSelect={onMealSelect}
              error={errors[meal.meal_time] || null}
            />
          ))}
        </div>
      </div>

      {/* Change Meal Feedback */}
      {showChangeMealForm && (
        <Card className="bg-blue-50 border-blue-200">
          <h4 className="font-medium text-gray-900 mb-2">
            Cambiar: {selectedMealTime}
          </h4>
          <p className="text-sm text-gray-600 mb-3">
            Describe que cambios te gustaria (opcional)
          </p>
          <textarea
            value={feedbackText}
            onChange={(e) => onFeedbackChange(e.target.value)}
            placeholder="Ej: Quiero algo mas ligero, sin lacteos..."
            className="
              w-full rounded-lg border border-gray-300 px-3 py-2
              text-sm text-gray-900 placeholder:text-gray-400
              focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500
              resize-none
            "
            rows={3}
          />
        </Card>
      )}

      {/* Action Buttons */}
      <div className="pt-4 border-t border-gray-200">
        <ReviewActionButtons
          onAction={onAction}
          isLoading={isLoading}
          selectedMealTime={selectedMealTime}
          feedbackText={feedbackText}
          showChangeMealForm={showChangeMealForm}
        />
      </div>

      {/* Help Text */}
      <p className="text-xs text-gray-500 text-center">
        Selecciona una comida para cambiarla individualmente, o usa los botones para aprobar o regenerar todo el plan.
      </p>
    </div>
  );
}
