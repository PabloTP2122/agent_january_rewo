"use client";

import { useState, useCallback } from "react";
import type { Meal, NutritionalTargets, ReviewDecision } from "@/lib/types";
import { MealPlanReviewView } from "./MealPlanReviewView";

export interface MealPlanReviewProps {
  meals: Meal[];
  nutritionalTargets: NutritionalTargets | null;
  errors?: Record<string, string>;
  onReviewComplete: (decision: ReviewDecision, mealTime?: string, feedback?: string) => void;
  isSubmitting?: boolean;
}

export function MealPlanReview({
  meals,
  nutritionalTargets,
  errors = {},
  onReviewComplete,
  isSubmitting = false,
}: MealPlanReviewProps) {
  const [selectedMealTime, setSelectedMealTime] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const handleMealSelect = useCallback((mealTime: string) => {
    setSelectedMealTime((prev) => (prev === mealTime ? null : mealTime));
    setFeedbackText("");
  }, []);

  const handleFeedbackChange = useCallback((feedback: string) => {
    setFeedbackText(feedback);
  }, []);

  const handleAction = useCallback(
    (decision: ReviewDecision, mealTime?: string, feedback?: string) => {
      // Reset selection state
      setSelectedMealTime(null);
      setFeedbackText("");

      // Notify parent
      onReviewComplete(decision, mealTime, feedback);
    },
    [onReviewComplete]
  );

  return (
    <MealPlanReviewView
      meals={meals}
      nutritionalTargets={nutritionalTargets}
      errors={errors}
      selectedMealTime={selectedMealTime}
      feedbackText={feedbackText}
      isLoading={isSubmitting}
      onMealSelect={handleMealSelect}
      onFeedbackChange={handleFeedbackChange}
      onAction={handleAction}
    />
  );
}
