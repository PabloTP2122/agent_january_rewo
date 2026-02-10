// File: ui/lib/mock-data.ts
/**
 * Mock data for Phase 1 development.
 * Replace with real agent state in Phase 3.
 */

import type {
  DietPlan,
  Meal,
  NutritionAgentState,
  NutritionalTargets,
  UserProfile,
} from "./types";

export const MOCK_MEAL_DESAYUNO: Meal = {
  meal_time: "Desayuno",
  title: "Omelet de Proteína con Aguacate",
  description:
    "Omelet de 3 huevos con espinaca, queso bajo en grasa y aguacate fresco",
  total_calories: 450,
  ingredients: [
    { "nombre": "huevos enteros", "cantidad_display": "3", "peso_gramos": 150, "kcal": 429 },
    {
      "nombre": "espinaca fresca",
      "cantidad_display": "50g",
      "peso_gramos": 50,
      "kcal": 12
    },
    {
      "nombre": "queso bajo en grasa",
      "cantidad_display": "30g",
      "peso_gramos": 30,
      "kcal": 60
    },
    {
      "nombre": "aguacate",
      "cantidad_display": "50g",
      "peso_gramos": 50,
      "kcal": 80
    },
    {
      "nombre": "aceite de oliva",
      "cantidad_display": "5ml",
      "peso_gramos": 5,
      "kcal": 45
    }
  ],
  preparation: [
    "Batir los huevos en un bowl",
    "Calentar el aceite en sartén antiadherente",
    "Agregar los huevos y cocinar a fuego medio",
    "Añadir espinaca y queso cuando esté medio cocido",
    "Doblar el omelet y servir con aguacate en rodajas",
  ],
  alternative: "Pancakes proteicos si no hay huevos disponibles",
};

export const MOCK_MEAL_COMIDA: Meal = {
  meal_time: "Comida",
  title: "Pechuga de Pollo Asada con Quinoa",
  description: "Pechuga de pollo al horno con quinoa y vegetales salteados",
  total_calories: 550,
  ingredients: [
    {
      "nombre": "pechuga de pollo",
      "cantidad_display": "200g",
      "peso_gramos": 200,
      "kcal": 330
    },
    {
      "nombre": "quinoa cocida",
      "cantidad_display": "150g",
      "peso_gramos": 150,
      "kcal": 180
    },
    {
      "nombre": "brócoli",
      "cantidad_display": "100g",
      "peso_gramos": 100,
      "kcal": 34
    },
    {
      "nombre": "zanahoria",
      "cantidad_display": "50g",
      "peso_gramos": 50,
      "kcal": 20
    },
    {
      "nombre": "aceite de oliva",
      "cantidad_display": "10ml",
      "peso_gramos": 10,
      "kcal": 90
    },
  ],
  preparation: [
    "Sazonar la pechuga con sal, pimienta y hierbas",
    "Hornear a 200°C por 25 minutos",
    "Cocinar la quinoa según instrucciones",
    "Saltear los vegetales con aceite de oliva",
    "Servir todo junto en un plato",
  ],
  alternative: "Filete de tilapia si no hay pollo",
};

export const MOCK_MEAL_CENA: Meal = {
  meal_time: "Cena",
  title: "Ensalada César con Proteína",
  description: "Ensalada césar con pollo a la plancha y aderezo ligero",
  total_calories: 400,
  ingredients: [
    {
      "nombre": "lechuga romana",
      "cantidad_display": "150g",
      "peso_gramos": 150,
      "kcal": 25
    },
    {
      "nombre": "pechuga de pollo",
      "cantidad_display": "150g",
      "peso_gramos": 150,
      "kcal": 248
    },
    {
      "nombre": "queso parmesano",
      "cantidad_display": "20g",
      "peso_gramos": 20,
      "kcal": 86
    },
    {
      "nombre": "aderezo césar ligero",
      "cantidad_display": "30ml",
      "peso_gramos": 30,
      "kcal": 90
    },
    {
      "nombre": "crutones integrales",
      "cantidad_display": "30g",
      "peso_gramos": 30,
      "kcal": 120
    },
  ],
  preparation: [
    "Cortar la lechuga y colocar en un bowl grande",
    "Cocinar el pollo a la plancha y cortarlo en tiras",
    "Agregar el pollo sobre la lechuga",
    "Añadir parmesano rallado y crutones",
    "Aliñar con aderezo césar ligero",
  ],
  alternative: null,
};

export const MOCK_NUTRITIONAL_TARGETS: NutritionalTargets = {
  bmr: 1750,
  tdee: 2712.5,
  target_calories: 2170,
  protein_grams: 162.75,
  protein_percentage: 30,
  carbs_grams: 217,
  carbs_percentage: 40,
  fat_grams: 72.33,
  fat_percentage: 30,
};

export const MOCK_USER_PROFILE: UserProfile = {
  age: 30,
  gender: "male",
  weight: 75,
  height: 175,
  activity_level: "moderately_active",
  objective: "fat_loss",
  diet_type: "normal",
  excluded_foods: ["mariscos"],
  number_of_meals: 3,
};

export const MOCK_DIET_PLAN: DietPlan = {
  diet_type: "Alta en Proteína",
  total_calories: 1400,
  macronutrients: {
    protein_percentage: 35,
    protein_grams: 122.5,
    carbs_percentage: 40,
    carbs_grams: 140,
    fat_percentage: 25,
    fat_grams: 38.9,
  },
  daily_meals: [MOCK_MEAL_DESAYUNO, MOCK_MEAL_COMIDA, MOCK_MEAL_CENA],
  shopping_list: [
    { food: "Huevo", quantity: "6 unidades" },
    { food: "Pechuga de pollo", quantity: "350g" },
    { food: "Espinaca fresca", quantity: "50g" },
    { food: "Queso bajo en grasa", quantity: "30g" },
    { food: "Aguacate", quantity: "1 unidad" },
    { food: "Quinoa", quantity: "150g" },
    { food: "Brócoli", quantity: "100g" },
    { food: "Lechuga romana", quantity: "150g" },
    { food: "Queso parmesano", quantity: "20g" },
  ],
  day_identifier: 1,
};

export const MOCK_AGENT_STATE: Partial<NutritionAgentState> = {
  user_profile: MOCK_USER_PROFILE,
  missing_fields: [],
  nutritional_targets: MOCK_NUTRITIONAL_TARGETS,
  meal_distribution: {
    Desayuno: 542.5,
    Comida: 868,
    Cena: 759.5,
  },
  daily_meals: [MOCK_MEAL_DESAYUNO, MOCK_MEAL_COMIDA, MOCK_MEAL_CENA],
  meal_generation_errors: {},
  review_decision: null,
  user_feedback: null,
  selected_meal_to_change: null,
  validation_errors: [],
  final_diet_plan: MOCK_DIET_PLAN,
};

// Empty state for testing data collection phase
export const MOCK_EMPTY_STATE: Partial<NutritionAgentState> = {
  user_profile: null,
  missing_fields: ["age", "gender", "weight", "height"],
  nutritional_targets: null,
  meal_distribution: null,
  daily_meals: [],
  meal_generation_errors: {},
  review_decision: null,
  user_feedback: null,
  selected_meal_to_change: null,
  validation_errors: [],
  final_diet_plan: null,
};

// State for testing HITL review
export const MOCK_HITL_STATE: Partial<NutritionAgentState> = {
  user_profile: MOCK_USER_PROFILE,
  missing_fields: [],
  nutritional_targets: MOCK_NUTRITIONAL_TARGETS,
  meal_distribution: {
    Desayuno: 450,
    Comida: 550,
    Cena: 400,
  },
  daily_meals: [MOCK_MEAL_DESAYUNO, MOCK_MEAL_COMIDA, MOCK_MEAL_CENA],
  meal_generation_errors: {},
  review_decision: null, // null = waiting for user decision
  user_feedback: null,
  selected_meal_to_change: null,
  validation_errors: [],
  final_diet_plan: null,
};
