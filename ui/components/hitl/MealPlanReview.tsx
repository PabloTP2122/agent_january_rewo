"use client";

import { useState, useCallback } from "react";
import type { Meal, MealNotice, NutritionalTargets, ReviewDecision } from "@/lib/types";
import { MealPlanReviewView } from "./MealPlanReviewView";

export interface MealPlanReviewProps {
  meals: Meal[];
  nutritionalTargets: NutritionalTargets | null;
  notices?: Record<string, MealNotice>;
  onReviewComplete: (decision: ReviewDecision, mealTime?: string, feedback?: string) => void;
  isSubmitting?: boolean;
}

export function MealPlanReview({
  meals,
  nutritionalTargets,
  notices = {},
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
      notices={notices}
      selectedMealTime={selectedMealTime}
      feedbackText={feedbackText}
      isLoading={isSubmitting}
      onMealSelect={handleMealSelect}
      onFeedbackChange={handleFeedbackChange}
      onAction={handleAction}
    />
  );
}
