"use client";

import type { UseFormRegister, FieldErrors } from "react-hook-form";
import {
  ACTIVITY_LEVEL_OPTIONS,
  CONSTRAINTS,
  DIET_TYPE_OPTIONS,
  GENDER_OPTIONS,
  MEALS_OPTIONS,
  OBJECTIVE_OPTIONS,
} from "@/lib/constants";
import type { UserProfileSchemaType } from "@/lib/validations";
import { Button, FormField, Select } from "@/components/ui";
import { ExcludedFoodInput } from "./ExcludedFoodInput";

export interface UserProfileFormViewProps {
  register: UseFormRegister<UserProfileSchemaType>;
  errors: FieldErrors<UserProfileSchemaType>;
  onSubmit: (e: React.FormEvent) => void;
  isSubmitting: boolean;
  isDirty: boolean;
  excludedFoods: string[];
  onAddExcludedFood: (food: string) => void;
  onRemoveExcludedFood: (index: number) => void;
}

export function UserProfileFormView({
  register,
  errors,
  onSubmit,
  isSubmitting,
  isDirty,
  excludedFoods,
  onAddExcludedFood,
  onRemoveExcludedFood,
}: UserProfileFormViewProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-8">
      {/* Section: Personal Data */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Datos Personales
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField
            label="Edad"
            type="number"
            placeholder="30"
            suffix="años"
            error={errors.age?.message}
            hint={`${CONSTRAINTS.age.min}-${CONSTRAINTS.age.max} años`}
            required
            {...register("age", { valueAsNumber: true })}
          />

          <Select
            label="Género"
            options={GENDER_OPTIONS}
            error={errors.gender?.message}
            required
            {...register("gender")}
          />

          <FormField
            label="Peso"
            type="number"
            placeholder="70"
            suffix="kg"
            error={errors.weight?.message}
            hint={`${CONSTRAINTS.weight.min}-${CONSTRAINTS.weight.max} kg`}
            required
            {...register("weight", { valueAsNumber: true })}
          />

          <FormField
            label="Altura"
            type="number"
            placeholder="170"
            suffix="cm"
            error={errors.height?.message}
            hint={`${CONSTRAINTS.height.min}-${CONSTRAINTS.height.max} cm`}
            required
            {...register("height", { valueAsNumber: true })}
          />
        </div>
      </section>

      {/* Section: Lifestyle */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Estilo de Vida
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Nivel de Actividad"
            options={ACTIVITY_LEVEL_OPTIONS}
            error={errors.activity_level?.message}
            required
            {...register("activity_level")}
          />

          <Select
            label="Objetivo"
            options={OBJECTIVE_OPTIONS}
            error={errors.objective?.message}
            required
            {...register("objective")}
          />
        </div>
      </section>

      {/* Section: Preferences */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Preferencias
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Tipo de Dieta"
            options={DIET_TYPE_OPTIONS}
            error={errors.diet_type?.message}
            {...register("diet_type")}
          />

          <Select
            label="Comidas por Día"
            options={MEALS_OPTIONS}
            error={errors.number_of_meals?.message}
            {...register("number_of_meals", { valueAsNumber: true })}
          />
        </div>

        {/* Excluded Foods */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Alimentos Excluidos
          </label>
          <p className="text-sm text-gray-500 mb-2">
            Alergias, intolerancias o preferencias (opcional)
          </p>

          {/* Tags display */}
          {excludedFoods.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {excludedFoods.map((food, index) => (
                <span
                  key={`${food}-${index}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {food}
                  <button
                    type="button"
                    onClick={() => onRemoveExcludedFood(index)}
                    className="ml-1 text-gray-400 hover:text-gray-600"
                    aria-label={`Eliminar ${food}`}
                  >
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Add food input */}
          <ExcludedFoodInput onAdd={onAddExcludedFood} />
        </div>
      </section>

      {/* Submit Button */}
      <div className="pt-4 border-t border-gray-200">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={isSubmitting}
          disabled={!isDirty && excludedFoods.length === 0}
          rightIcon={
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          }
        >
          Generar Plan Nutricional
        </Button>
      </div>
    </form>
  );
}
