"use client";

import { useState } from "react";
import { Card, Badge, Button } from "@/components/ui";
import type { Meal } from "@/lib/types";

export interface MealReviewCardProps {
  meal: Meal;
  isSelected?: boolean;
  onSelect?: (mealTime: string) => void;
  error?: string | null;
}

export function MealReviewCard({
  meal,
  isSelected = false,
  onSelect,
  error = null,
}: MealReviewCardProps) {
  const [expanded, setExpanded] = useState(false);

  const handleSelect = () => {
    if (onSelect) {
      onSelect(meal.meal_time);
    }
  };

  return (
    <Card
      className={`
        transition-all duration-200
        ${isSelected ? "ring-2 ring-blue-500 bg-blue-50" : "hover:shadow-md"}
        ${error ? "border-amber-300 bg-amber-50" : ""}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="default" size="sm">
              {meal.meal_time}
            </Badge>
            <Badge variant="success" size="sm">
              {meal.total_calories.toFixed(0)} kcal
            </Badge>
          </div>
          <h4 className="font-semibold text-gray-900 truncate">{meal.title}</h4>
          <p className="text-sm text-gray-600 line-clamp-2">{meal.description}</p>
        </div>

        {onSelect && (
          <Button
            type="button"
            variant={isSelected ? "primary" : "outline"}
            size="sm"
            onClick={handleSelect}
          >
            {isSelected ? "Seleccionado" : "Cambiar"}
          </Button>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-3 p-2 bg-amber-100 border border-amber-200 rounded-md">
          <p className="text-sm text-amber-800">
            <span className="font-medium">Advertencia:</span> {error}
          </p>
        </div>
      )}

      {/* Expandable Details */}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
        >
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {expanded ? "Ocultar detalles" : "Ver detalles"}
        </button>

        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
            {/* Ingredients */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-1">Ingredientes:</h5>
              <ul className="text-sm text-gray-600 space-y-0.5">
                {meal.ingredients.map((ingredient, index) => (
                  <li key={index} className="flex items-start gap-1">
                    <span className="text-gray-400">•</span>
                    {ingredient}
                  </li>
                ))}
              </ul>
            </div>

            {/* Preparation */}
            {meal.preparation && meal.preparation.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-1">Preparacion:</h5>
                <ol className="text-sm text-gray-600 space-y-1">
                  {meal.preparation.map((step, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="font-medium text-gray-400">{index + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Alternative */}
            {meal.alternative && (
              <div className="p-2 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Alternativa:</span> {meal.alternative}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
