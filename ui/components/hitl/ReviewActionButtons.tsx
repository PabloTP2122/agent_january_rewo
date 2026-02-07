"use client";

import { Button } from "@/components/ui";
import type { ReviewDecision } from "@/lib/types";

export interface ReviewActionButtonsProps {
  onAction: (decision: ReviewDecision, mealTime?: string, feedback?: string) => void;
  isLoading?: boolean;
  selectedMealTime?: string | null;
  feedbackText?: string;
  showChangeMealForm?: boolean;
}

export function ReviewActionButtons({
  onAction,
  isLoading = false,
  selectedMealTime = null,
  feedbackText = "",
  showChangeMealForm = false,
}: ReviewActionButtonsProps) {
  const handleApprove = () => {
    onAction("approve");
  };

  const handleRegenerateAll = () => {
    onAction("regenerate_all");
  };

  const handleChangeMeal = () => {
    if (selectedMealTime) {
      onAction("change_meal", selectedMealTime, feedbackText);
    }
  };

  if (showChangeMealForm && selectedMealTime) {
    return (
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          type="button"
          variant="primary"
          size="md"
          onClick={handleChangeMeal}
          loading={isLoading}
          disabled={!selectedMealTime}
        >
          Cambiar Comida
        </Button>
        <Button
          type="button"
          variant="outline"
          size="md"
          onClick={() => onAction("approve")}
          disabled={isLoading}
        >
          Cancelar
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <Button
        type="button"
        variant="primary"
        size="lg"
        onClick={handleApprove}
        loading={isLoading}
        leftIcon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        }
      >
        Aprobar Plan
      </Button>

      <Button
        type="button"
        variant="outline"
        size="lg"
        onClick={handleRegenerateAll}
        disabled={isLoading}
        leftIcon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        }
      >
        Regenerar Todo
      </Button>
    </div>
  );
}
