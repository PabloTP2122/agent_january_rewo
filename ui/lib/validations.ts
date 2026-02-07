// File: ui/lib/validations.ts
/**
 * Zod validation schemas for forms.
 * Constraints must match Python Pydantic models.
 */

import { z } from "zod";
import { ActivityLevel, DietType, Gender, Objective } from "./types";

export const userProfileSchema = z.object({
  age: z
    .number({ message: "La edad debe ser un número válido" })
    .int({ message: "La edad debe ser un número entero" })
    .min(18, { message: "Debes tener al menos 18 años" })
    .max(100, { message: "La edad máxima es 100 años" }),

  gender: z.enum([Gender.MALE, Gender.FEMALE], {
    message: "El género es requerido",
  }),

  weight: z
    .number({ message: "El peso debe ser un número válido" })
    .int({ message: "El peso debe ser un número entero" })
    .min(30, { message: "El peso mínimo es 30 kg" })
    .max(300, { message: "El peso máximo es 300 kg" }),

  height: z
    .number({ message: "La altura debe ser un número válido" })
    .int({ message: "La altura debe ser un número entero" })
    .min(100, { message: "La altura mínima es 100 cm" })
    .max(250, { message: "La altura máxima es 250 cm" }),

  activity_level: z.enum(
    [
      ActivityLevel.SEDENTARY,
      ActivityLevel.LIGHTLY_ACTIVE,
      ActivityLevel.MODERATELY_ACTIVE,
      ActivityLevel.VERY_ACTIVE,
      ActivityLevel.EXTRA_ACTIVE,
    ],
    { message: "El nivel de actividad es requerido" }
  ),

  objective: z.enum(
    [Objective.FAT_LOSS, Objective.MUSCLE_GAIN, Objective.MAINTENANCE],
    { message: "El objetivo es requerido" }
  ),

  diet_type: z.enum([DietType.NORMAL, DietType.KETO], {
    message: "Tipo de dieta inválido",
  }),

  excluded_foods: z.array(z.string().trim()),

  number_of_meals: z
    .number({ message: "El número de comidas debe ser un número" })
    .int({ message: "El número de comidas debe ser entero" })
    .min(1, { message: "Mínimo 1 comida por día" })
    .max(6, { message: "Máximo 6 comidas por día" }),
});

export type UserProfileSchemaType = z.infer<typeof userProfileSchema>;
