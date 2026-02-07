// File: ui/lib/types.ts
/**
 * TypeScript types mirroring Python Pydantic models.
 * MUST match: src/shared/enums.py + src/nutrition_agent/models/
 */

// =============================================================================
// ENUMS - Must match src/shared/enums.py
// =============================================================================

export const ActivityLevel = {
  SEDENTARY: "sedentary",
  LIGHTLY_ACTIVE: "lightly_active",
  MODERATELY_ACTIVE: "moderately_active",
  VERY_ACTIVE: "very_active",
  EXTRA_ACTIVE: "extra_active",
} as const;
export type ActivityLevel = (typeof ActivityLevel)[keyof typeof ActivityLevel];

export const Objective = {
  FAT_LOSS: "fat_loss",
  MUSCLE_GAIN: "muscle_gain",
  MAINTENANCE: "maintenance",
} as const;
export type Objective = (typeof Objective)[keyof typeof Objective];

export const DietType = {
  NORMAL: "normal",
  KETO: "keto",
} as const;
export type DietType = (typeof DietType)[keyof typeof DietType];

export const Gender = {
  MALE: "male",
  FEMALE: "female",
} as const;
export type Gender = (typeof Gender)[keyof typeof Gender];

export const MealTime = {
  DESAYUNO: "Desayuno",
  ALMUERZO: "Almuerzo",
  COMIDA: "Comida",
  CENA: "Cena",
  SNACK: "Snack",
} as const;
export type MealTime = (typeof MealTime)[keyof typeof MealTime];

// =============================================================================
// INTERFACES - Must match src/nutrition_agent/models/
// =============================================================================

/**
 * Maps to: src/nutrition_agent/models/user_profile.py
 */
export interface UserProfile {
  age: number;
  gender: Gender;
  weight: number;
  height: number;
  activity_level: ActivityLevel;
  objective: Objective;
  diet_type: DietType;
  excluded_foods: string[];
  number_of_meals: number;
}

/**
 * Maps to: src/nutrition_agent/models/nutritional_targets.py
 */
export interface NutritionalTargets {
  bmr: number;
  tdee: number;
  target_calories: number;
  protein_grams: number;
  protein_percentage: number;
  carbs_grams: number;
  carbs_percentage: number;
  fat_grams: number;
  fat_percentage: number;
}

/**
 * Maps to: src/nutrition_agent/models/diet_plan.py - Macronutrients
 */
export interface Macronutrients {
  protein_percentage: number;
  protein_grams: number;
  carbs_percentage: number;
  carbs_grams: number;
  fat_percentage: number;
  fat_grams: number;
}

/**
 * Maps to: src/nutrition_agent/models/diet_plan.py - Meal
 */
export interface Meal {
  meal_time: MealTime;
  title: string;
  description: string;
  total_calories: number;
  ingredients: string[];
  preparation: string[];
  alternative: string | null;
}

/**
 * Maps to: src/nutrition_agent/models/diet_plan.py - ShoppingListItem
 */
export interface ShoppingListItem {
  food: string;
  quantity: string;
}

/**
 * Maps to: src/nutrition_agent/models/diet_plan.py - DietPlan
 */
export interface DietPlan {
  diet_type: string;
  total_calories: number;
  macronutrients: Macronutrients;
  daily_meals: Meal[];
  shopping_list: ShoppingListItem[];
  day_identifier: number;
}

// =============================================================================
// AGENT STATE - Maps to src/nutrition_agent/state.py
// =============================================================================

export type ReviewDecision = "approve" | "change_meal" | "regenerate_all";

export type AgentPhase =
  | "idle"
  | "data_collection"
  | "calculation"
  | "recipe_generation"
  | "meal_review"
  | "validation"
  | "complete"
  | "error";

/**
 * Full agent state matching NutritionAgentState(CopilotKitState).
 */
export interface NutritionAgentState {
  // Phase 1: Data Collection
  user_profile: UserProfile | null;
  missing_fields: string[];

  // Phase 2: Calculation
  nutritional_targets: NutritionalTargets | null;
  meal_distribution: Record<string, number> | null;

  // Phase 3: Recipe Generation
  daily_meals: Meal[];
  meal_generation_errors: Record<string, string>;

  // Phase 4: HITL Review
  review_decision: ReviewDecision | null;
  user_feedback: string | null;
  selected_meal_to_change: string | null;

  // Phase 5: Validation
  validation_errors: string[];
  final_diet_plan: DietPlan | null;
}

// =============================================================================
// HITL TYPES
// =============================================================================

export interface HITLOption {
  action: ReviewDecision;
  label: string;
  requires?: string[];
}

export interface HITLInterruptPayload {
  type: "meal_plan_review";
  daily_meals: Meal[];
  nutritional_targets: NutritionalTargets | null;
  meal_generation_errors: Record<string, string>;
  options: HITLOption[];
}

export interface HITLUserResponse {
  action: ReviewDecision;
  meal_time?: MealTime;
  feedback?: string;
}

// =============================================================================
// DEBUG INFO
// =============================================================================

export interface DebugInfo {
  phase: AgentPhase;
  elapsed_seconds: number;
  tools_invoked: string[];
  last_error: string | null;
}
