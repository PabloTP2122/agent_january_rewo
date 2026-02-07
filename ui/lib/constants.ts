// File: ui/lib/constants.ts
/**
 * UI constants for form select options.
 * Labels in Spanish for target audience.
 */

import { ActivityLevel, DietType, Gender, Objective } from "./types";

export interface SelectOption<T> {
  value: T;
  label: string;
  description?: string;
}

export const GENDER_OPTIONS: SelectOption<Gender>[] = [
  { value: Gender.MALE, label: "Masculino" },
  { value: Gender.FEMALE, label: "Femenino" },
];

export const ACTIVITY_LEVEL_OPTIONS: SelectOption<ActivityLevel>[] = [
  {
    value: ActivityLevel.SEDENTARY,
    label: "Sedentario",
    description: "Poco o ningún ejercicio",
  },
  {
    value: ActivityLevel.LIGHTLY_ACTIVE,
    label: "Ligeramente activo",
    description: "Ejercicio 1-3 días/semana",
  },
  {
    value: ActivityLevel.MODERATELY_ACTIVE,
    label: "Moderadamente activo",
    description: "Ejercicio 3-5 días/semana",
  },
  {
    value: ActivityLevel.VERY_ACTIVE,
    label: "Muy activo",
    description: "Ejercicio 6-7 días/semana",
  },
  {
    value: ActivityLevel.EXTRA_ACTIVE,
    label: "Extra activo",
    description: "Ejercicio muy intenso + trabajo físico",
  },
];

export const OBJECTIVE_OPTIONS: SelectOption<Objective>[] = [
  {
    value: Objective.FAT_LOSS,
    label: "Pérdida de grasa",
    description: "Déficit calórico del 20%",
  },
  {
    value: Objective.MUSCLE_GAIN,
    label: "Ganancia muscular",
    description: "Superávit calórico del 10%",
  },
  {
    value: Objective.MAINTENANCE,
    label: "Mantenimiento",
    description: "Mantener peso actual",
  },
];

export const DIET_TYPE_OPTIONS: SelectOption<DietType>[] = [
  { value: DietType.NORMAL, label: "Normal", description: "Dieta balanceada" },
  {
    value: DietType.KETO,
    label: "Cetogénica",
    description: "Alta en grasas, baja en carbos",
  },
];

export const MEALS_OPTIONS: SelectOption<number>[] = [
  { value: 1, label: "1 comida", description: "Ayuno OMAD" },
  { value: 2, label: "2 comidas", description: "Ayuno 16:8" },
  { value: 3, label: "3 comidas", description: "Tradicional" },
  { value: 4, label: "4 comidas", description: "Con merienda" },
  { value: 5, label: "5 comidas", description: "Con dos meriendas" },
  { value: 6, label: "6 comidas", description: "Comidas frecuentes" },
];

export const DEFAULT_USER_PROFILE = {
  age: 30,
  gender: Gender.MALE,
  weight: 70,
  height: 170,
  activity_level: ActivityLevel.MODERATELY_ACTIVE,
  objective: Objective.MAINTENANCE,
  diet_type: DietType.NORMAL,
  excluded_foods: [] as string[],
  number_of_meals: 3,
} as const;

export const CONSTRAINTS = {
  age: { min: 18, max: 100 },
  weight: { min: 30, max: 300 },
  height: { min: 100, max: 250 },
  meals: { min: 1, max: 6 },
} as const;
