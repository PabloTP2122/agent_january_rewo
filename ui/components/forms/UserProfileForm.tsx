"use client";

import { useCallback, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { DEFAULT_USER_PROFILE } from "@/lib/constants";
import { userProfileSchema, type UserProfileSchemaType } from "@/lib/validations";
import type { UserProfile } from "@/lib/types";
import { UserProfileFormView } from "./UserProfileFormView";

export interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  isSubmitting?: boolean;
}

export function UserProfileForm({ onSubmit, isSubmitting = false }: UserProfileFormProps) {
  const [excludedFoods, setExcludedFoods] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting: formSubmitting, isDirty },
  } = useForm<UserProfileSchemaType>({
    resolver: zodResolver(userProfileSchema),
    defaultValues: DEFAULT_USER_PROFILE,
    mode: "onBlur",
  });

  const handleAddExcludedFood = useCallback((food: string) => {
    const normalizedFood = food.toLowerCase().trim();
    setExcludedFoods((prev) => {
      if (prev.includes(normalizedFood)) return prev;
      return [...prev, normalizedFood];
    });
  }, []);

  const handleRemoveExcludedFood = useCallback((index: number) => {
    setExcludedFoods((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleFormSubmit = useCallback(
    (data: UserProfileSchemaType) => {
      const profile: UserProfile = {
        ...data,
        excluded_foods: excludedFoods,
      };
      onSubmit(profile);
    },
    [excludedFoods, onSubmit]
  );

  return (
    <UserProfileFormView
      register={register}
      errors={errors}
      onSubmit={handleSubmit(handleFormSubmit)}
      isSubmitting={isSubmitting || formSubmitting}
      isDirty={isDirty}
      excludedFoods={excludedFoods}
      onAddExcludedFood={handleAddExcludedFood}
      onRemoveExcludedFood={handleRemoveExcludedFood}
    />
  );
}
