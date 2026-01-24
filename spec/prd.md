# PRD: Nutrition Agent (Plan-and-Execute Architecture)

> **Document Type**: Product Requirements Document for Agent Execution
> **Target**: AI Agent implementing the nutrition_agent module
> **Progress Tracking**: `spec/progress.txt`
> **Version**: FIXED - All critical issues resolved

---

## Table of Contents

1. [Overview](#1-overview)
2. [Agent Instructions](#2-agent-instructions)
3. [Technical Specifications](#3-technical-specifications)
4. [Implementation Phases](#4-implementation-phases)
5. [Verification Checklist](#5-verification-checklist)

---

## 1. Overview

### 1.1 Project Goal

Build a **Plan-and-Execute nutrition planning agent** that:
- Collects user profile data conversationally
- Calculates TDEE and macronutrients deterministically (no LLM)
- Generates ALL daily meals in parallel using LLM (reduced latency)
- Supports Human-in-the-Loop (HITL) review of the complete daily plan (single review point)
- Validates calorie math before final output

### 1.2 Architecture Decision

**Chosen Architecture**: Plan-and-Execute (scored 32/35)
**Rejected**: ReWOO (18/35) - kept in `src/rewoo_agent/` for A/B testing

### 1.3 Directory Structure (ALREADY EXISTS)

```
src/
├── shared/                      # Create files here
│   └── __init__.py
├── nutrition_agent/             # Create files here
│   ├── __init__.py
│   ├── state.py                 # EMPTY - implement
│   ├── graph.py                 # EMPTY - implement
│   ├── models/
│   │   └── __init__.py
│   ├── nodes/
│   │   └── __init__.py
│   └── prompts/
│       ├── __init__.py
│       ├── data_collection.py   # Has docstring only
│       └── recipe_generation.py # EMPTY
└── rewoo_agent/                 # KEEP for A/B testing - DO NOT MODIFY
```

**IMPORTANT**: Directory structure already exists. Only create/modify files inside existing directories.

---

## 2. Agent Instructions

### 2.1 Workflow

For each phase:
1. Read the phase requirements from this document
2. Implement all tasks in the phase
3. Run `pre-commit run --all-files` to validate
4. If pre-commit fails, fix issues and retry
5. Update `spec/progress.txt` with completed tasks
6. Create a git commit with descriptive message
7. If blocked or unsure, **ask the user**

### 2.2 Progress Tracking Format

Update `spec/progress.txt` after each phase:

```
# Nutrition Agent Implementation Progress

## Phase 1: Shared Foundation
- [x] Created src/shared/enums.py
- [x] Created src/shared/llm.py
- [x] Created src/shared/tools.py
- [x] Updated src/shared/__init__.py
Commit: <commit-hash>
Date: <YYYY-MM-DD>

## Phase 2: Models
- [ ] Task pending...
```

### 2.3 Commit Convention

```
feat(nutrition-agent): <phase-description>

- Bullet point of changes
- Another change

Phase X/7 complete
```

### 2.4 Pre-commit Requirement

Before every commit, run:
```bash
pre-commit run --all-files
```

If it fails:
1. Read the error output
2. Fix the issues (formatting, linting, type errors)
3. Run pre-commit again
4. Only commit when pre-commit passes

### 2.5 Error Handling

If you encounter:
- **Import errors**: Check if dependencies exist, ask user if unclear
- **Type errors**: Ensure Pydantic models match expected types
- **Test failures**: Fix the failing test, ask user if logic is unclear
- **Unclear requirements**: Ask user before proceeding

---

## 3. Technical Specifications

### 3.1 Enums (src/shared/enums.py)

```python
# File: src/shared/enums.py
from enum import StrEnum

class ActivityLevel(StrEnum):
    """Niveles de actividad estandarizados para evitar ambigüedad."""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"

class Objective(StrEnum):
    """Objetivos claros para guiar el cálculo calórico."""
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"

class DietType(StrEnum):
    """Tipos de dieta soportados."""
    NORMAL = "normal"
    KETO = "keto"

class MealTime(StrEnum):
    """Tiempos de comida válidos."""
    DESAYUNO = "Desayuno"
    ALMUERZO = "Almuerzo"
    COMIDA = "Comida"
    CENA = "Cena"
    SNACK = "Snack"
```

### 3.2 Models

#### 3.2.1 UserProfile (src/nutrition_agent/models/user_profile.py)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `age` | `int` | 18-100 | User age in years |
| `gender` | `Literal["male", "female"]` | required | Biological gender for BMR calc |
| `weight` | `int` | 30-300 | Weight in kg |
| `height` | `int` | 100-250 | Height in cm |
| `activity_level` | `ActivityLevel` | required | From enums |
| `objective` | `Objective` | required | From enums |
| `diet_type` | `DietType` | default="normal" | From enums |
| `excluded_foods` | `list[str]` | default=[] | Foods to avoid |
| `number_of_meals` | `int` | 1-6, default=3 | Meals per day |

**NOTA**: Los tipos `weight` e `height` son `int` para mantener compatibilidad con la tool `generate_nutritional_plan` existente.

#### 3.2.2 NutritionalTargets (src/nutrition_agent/models/nutritional_targets.py)

| Field | Type | Description |
|-------|------|-------------|
| `bmr` | `float` | Basal Metabolic Rate (Mifflin-St Jeor) |
| `tdee` | `float` | Total Daily Energy Expenditure |
| `target_calories` | `float` | Adjusted by objective |
| `protein_grams` | `float` | Daily protein target |
| `protein_percentage` | `float` | 0-100 |
| `carbs_grams` | `float` | Daily carbs target |
| `carbs_percentage` | `float` | 0-100 |
| `fat_grams` | `float` | Daily fat target |
| `fat_percentage` | `float` | 0-100 |

#### 3.2.3 Meal (src/nutrition_agent/models/diet_plan.py)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `meal_time` | `MealTime` | required | From enums |
| `title` | `str` | 5-150 chars | Meal name |
| `description` | `str` | 10-500 chars | Brief description |
| `total_calories` | `float` | 0-2000 | Meal calories |
| `ingredients` | `list[str]` | required | With quantities in grams |
| `preparation` | `list[str]` | required | Numbered steps |
| `alternative` | `str` | optional | Alternative suggestion |

#### 3.2.4 Macronutrients (src/nutrition_agent/models/diet_plan.py)

| Field | Type | Description |
|-------|------|-------------|
| `protein_percentage` | `float` | 0-100 |
| `protein_grams` | `float` | Total grams |
| `carbs_percentage` | `float` | 0-100 |
| `carbs_grams` | `float` | Total grams |
| `fat_percentage` | `float` | 0-100 |
| `fat_grams` | `float` | Total grams |

#### 3.2.5 ShoppingListItem (src/nutrition_agent/models/diet_plan.py)

| Field | Type | Description |
|-------|------|-------------|
| `food` | `str` | Ingredient name (2-100 chars) |
| `quantity` | `str` | Amount with unit (e.g., "200g", "1 unidad") |

**NOTA**: Estructura compatible con la tool `consolidate_shopping_list` existente.

#### 3.2.6 DietPlan (src/nutrition_agent/models/diet_plan.py)

| Field | Type | Description |
|-------|------|-------------|
| `diet_type` | `str` | e.g., "High Protein", "Keto" |
| `total_calories` | `float` | 500-10000 |
| `macronutrients` | `Macronutrients` | Daily macro breakdown |
| `daily_meals` | `list[Meal]` | 1-6 meals |
| `shopping_list` | `list[ShoppingListItem]` | Consolidated list |
| `day_identifier` | `int` | Day number in plan |

### 3.3 State Definition (src/nutrition_agent/state.py)

```python
# File: src/nutrition_agent/state.py
from typing import Literal

from copilotkit.langgraph import CopilotKitState
from pydantic import Field

from src.nutrition_agent.models import (
    UserProfile,
    NutritionalTargets,
    Meal,
    DietPlan
)


class NutritionAgentState(CopilotKitState):
    # Phase 1: Data Collection
    user_profile: UserProfile | None = None
    missing_fields: list[str] = Field(default_factory=list)

    # Phase 2: Calculation
    nutritional_targets: NutritionalTargets | None = None
    meal_distribution: dict[str, float] | None = None

    # Phase 3: Recipe Generation (PARALLEL BATCH)
    daily_meals: list[Meal] = Field(default_factory=list)  # All meals generated in parallel
    meal_generation_errors: dict[str, str] = Field(default_factory=dict)  # Errors per meal_time

    # Phase 4: HITL Review (BATCH REVIEW - single review of complete plan)
    review_decision: Literal["approve", "change_meal", "regenerate_all"] | None = None
    user_feedback: str | None = None
    selected_meal_to_change: str | None = None  # MealTime to change (only if review_decision == "change_meal")

    # Phase 5: Validation
    validation_errors: list[str] = Field(default_factory=list)
    final_diet_plan: DietPlan | None = None
```

**Import**: `from copilotkit.langgraph import CopilotKitState`

**NOTA**: Se usa `Field(default_factory=list)` en lugar de `= []` para evitar el problema de mutable defaults en Pydantic.

**CAMBIO v2 (Paralelización)**: Se eliminaron `current_meal_index`, `meals_completed`, `skip_remaining_reviews`, `meals_approved` ya que ahora se genera todo el batch en paralelo y hay una sola revisión HITL del plan completo.

### 3.4 Graph Flow (Parallel Batch Architecture)

```
START
  │
  ▼
┌─────────────────────┐
│   data_collection   │ ◄─────────┐
│       (LLM)         │           │ missing_fields
└─────────┬───────────┘           │
          │ profile_complete      │
          ▼                       │
┌─────────────────────┐           │
│     calculation     │───────────┘
│   (deterministic)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────┐
│  recipe_generation_batch    │ ◄──────────────────────┐
│  (LLM PARALLEL)             │                        │
│  asyncio.gather() N meals   │                        │
└─────────┬───────────────────┘                        │
          │                                            │
          ▼                                            │
┌─────────────────────────────┐   change_meal          │
│    meal_review_batch        │────────────────────────┤
│  (HITL - reviews ALL meals) │                        │
└─────────┬───────────────────┘   regenerate_all       │
          │                    ────────────────────────┘
          │ approve
          ▼
┌─────────────────────────────┐
│       validation            │─────┐
│     (deterministic)         │     │ validation_errors
└─────────┬───────────────────┘     │
          │ valid                   │
          ▼                         │
         END ◄──────────────────────┘
                (retry via recipe_generation_batch)
```

**Key Change**: All meals are generated in a single parallel batch, then reviewed together in one HITL checkpoint. This reduces latency by ~60% and eliminates O(n²) token growth.

### 3.5 Node Specifications

#### Node 1: data_collection

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/data_collection.py` |
| **Function** | `async def data_collection(state: NutritionAgentState) -> dict` |
| **Type** | LLM (uses structured output) |
| **Tools** | None (pure LLM extraction) |
| **Input** | `state.messages`, `state.user_profile` |
| **Output** | `{"user_profile": UserProfile, "missing_fields": []}` |
| **Prompt File** | `src/nutrition_agent/prompts/data_collection.py` |
| **Behavior** | Extract UserProfile from conversation. If profile exists and complete, return empty dict. |

#### Node 2: calculation

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/calculation.py` |
| **Function** | `def calculation(state: NutritionAgentState) -> dict` |
| **Type** | Deterministic (NO LLM) |
| **Tools** | `generate_nutritional_plan`, `get_meal_distribution` |
| **Input** | `state.user_profile` |
| **Output** | `{"nutritional_targets": NutritionalTargets, "meal_distribution": dict}` |
| **Formulas** | Mifflin-St Jeor for BMR, activity multipliers for TDEE |

**BMR Formula (Mifflin-St Jeor)**:
- Male: `BMR = 10*weight + 6.25*height - 5*age + 5`
- Female: `BMR = 10*weight + 6.25*height - 5*age - 161`

**Activity Multipliers**:
- sedentary: 1.2
- lightly_active: 1.375
- moderately_active: 1.55
- very_active: 1.725
- extra_active: 1.9

**Objective Adjustments**:
- fat_loss: TDEE * 0.8 (20% deficit)
- muscle_gain: TDEE * 1.1 (10% surplus)
- maintenance: TDEE * 1.0

#### Node 3: recipe_generation_batch

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/recipe_generation_batch.py` |
| **Function** | `async def recipe_generation_batch(state: NutritionAgentState) -> dict` |
| **Type** | LLM (parallel structured outputs via `asyncio.gather()`) |
| **Input** | `state.meal_distribution`, `state.user_profile`, `state.nutritional_targets` |
| **Output** | `{"daily_meals": [Meal, ...], "meal_generation_errors": {}}` |
| **Tools** | `calculate_recipe_nutrition` (for pre-validation per meal) |
| **Prompt File** | `src/nutrition_agent/prompts/recipe_generation.py` |
| **Behavior** | Generate ALL meals in parallel using hybrid approach (see Section 3.5.2) |

**Hybrid Parallel Strategy:**
1. Generate meals 1 to N-1 in parallel via `asyncio.gather()`
2. Calculate consumed calories from parallel results
3. Generate last meal (N) sequentially with exact remaining budget
4. Each meal goes through pre-validation loop (max 3 attempts)

**Benefits:**
- ~60% latency reduction vs sequential generation
- O(n) token usage vs O(n²) in sequential approach
- Precise budget for last meal (not possible with full parallelization)

#### Node 3b: recipe_generation_single (for HITL change_meal)

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/recipe_generation_single.py` |
| **Function** | `async def recipe_generation_single(state: NutritionAgentState) -> dict` |
| **Type** | LLM (single meal regeneration) |
| **Input** | `state.daily_meals`, `state.selected_meal_to_change`, `state.user_feedback`, `state.meal_distribution` |
| **Output** | `{"daily_meals": [Meal, ...], "review_decision": None}` |
| **Behavior** | Regenerate ONE specific meal after user requests a change. Replaces meal in `daily_meals` list. |

**When Used:**
- User reviews complete plan and selects "change_meal" for a specific meal
- Takes `user_feedback` to guide regeneration (e.g., "make it vegetarian")
- Returns to `meal_review_batch` for re-review

#### Node 4: meal_review_batch

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/meal_review_batch.py` |
| **Function** | `def meal_review_batch(state: NutritionAgentState) -> dict` |
| **Type** | HITL (uses `interrupt()`) |
| **Tools** | None (HITL only) |
| **Input** | `state.daily_meals`, `state.nutritional_targets`, `state.meal_generation_errors` |
| **Output** | `{"review_decision": str, "selected_meal_to_change": str \| None, "user_feedback": str \| None}` |
| **Behavior** | Single HITL review of the complete daily meal plan. User can approve all, change one meal, or regenerate everything. |

**Interrupt payload**:
```python
interrupt({
    "type": "meal_plan_review",
    "daily_meals": [meal.model_dump() for meal in state.daily_meals],
    "nutritional_targets": state.nutritional_targets.model_dump(),
    "meal_generation_errors": state.meal_generation_errors,  # Show warnings if any
    "options": [
        {"action": "approve", "label": "Approve Entire Plan"},
        {"action": "change_meal", "label": "Change Specific Meal", "requires": ["meal_time", "feedback"]},
        {"action": "regenerate_all", "label": "Regenerate All Meals"}
    ]
})
```

**User Decision Options:**
- `approve`: Accept entire plan, proceed to validation
- `change_meal`: Regenerate one specific meal (requires `meal_time` and optional `feedback`)
- `regenerate_all`: Discard plan and regenerate all meals from scratch

#### Node 5: validation

| Property | Value |
|----------|-------|
| **File** | `src/nutrition_agent/nodes/validation.py` |
| **Function** | `def validation(state: NutritionAgentState) -> dict` |
| **Type** | Deterministic (NO LLM) |
| **Tools** | `sum_total_kcal`, `consolidate_shopping_list` |
| **Input** | `state.daily_meals`, `state.nutritional_targets`, `state.user_profile` |
| **Output** | `{"validation_errors": [], "final_diet_plan": DietPlan}` |
| **Behavior** | Sum meal calories from `daily_meals`, compare to target (±5% tolerance). Build DietPlan if valid. |

**Note**: Changed from `meals_completed` to `daily_meals` to match new batch state.

### 3.5.1 Prompt Templates

**DATA_COLLECTION_PROMPT** (`src/nutrition_agent/prompts/data_collection.py`):

```python
DATA_COLLECTION_PROMPT = """You are a nutrition assistant collecting user profile data.

Extract a complete UserProfile with these fields:
- age (int, 18-100): User's age in years
- gender ("male" or "female"): Biological gender for BMR calculation
- weight (int, 30-300): Weight in kilograms
- height (int, 100-250): Height in centimeters
- activity_level: One of: sedentary, lightly_active, moderately_active, very_active, extra_active
- objective: One of: fat_loss, muscle_gain, maintenance
- diet_type (optional): "normal" or "keto" (default: normal)
- excluded_foods (optional): Foods to avoid
- number_of_meals (optional, 1-6): Meals per day (default: 3)

Instructions:
1. If the user hasn't provided all required fields, ask for the missing ones conversationally
2. Validate numeric ranges before accepting values
3. Return UserProfile ONLY when ALL required fields are collected
4. Be friendly and conversational, don't ask for all fields at once

Current conversation context will be provided in the messages.

Required fields: age, gender, weight, height, activity_level, objective
Optional fields: diet_type (default: normal), excluded_foods (default: []), number_of_meals (default: 3)
"""
```

**RECIPE_GENERATION_PROMPT** (`src/nutrition_agent/prompts/recipe_generation.py`):

```python
RECIPE_GENERATION_PROMPT = """Generate a single meal recipe for a complete daily meal plan.

User Profile:
- Objective: {objective}
- Diet Type: {diet_type}
- Excluded Foods: {excluded_foods}

Daily Nutritional Context:
- Total Daily Target: {daily_target_calories} kcal
- Daily Protein Target: {daily_protein_grams}g
- Daily Carbs Target: {daily_carbs_grams}g
- Daily Fat Target: {daily_fat_grams}g

Meal Requirements:
- Meal Time: {meal_time}
- Target Calories for THIS meal: {target_calories} kcal (±5% tolerance)
- This meal is part of a {total_meals}-meal daily plan

{special_instructions}

Generate a Meal with the following structure:
- meal_time: "{meal_time}"
- title: Short descriptive name (5-150 characters)
- description: Brief overview of the meal (10-500 characters)
- total_calories: Must be within ±5% of {target_calories}
- ingredients: List of ingredients with quantities in grams (e.g., "pollo 150g", "arroz 80g")
- preparation: Numbered list of cooking steps
- alternative (optional): A simpler alternative if available

IMPORTANT:
- Be PRECISE with calorie estimation
- Ingredients will be validated via RAG lookup
- Do NOT include any foods from the excluded list: {excluded_foods}
- Keep the meal appropriate for {diet_type} diet
- Ensure total_calories is realistic for the ingredients listed
- Use metric units (grams, ml) for all quantities
- This meal will be generated in parallel with other meals, so focus on hitting YOUR target precisely
"""

# For last meal in hybrid approach (stricter tolerance)
LAST_MEAL_INSTRUCTION = """
CRITICAL: This is the LAST meal of the day.
- Other meals have already been generated with total: {consumed_kcal} kcal
- You MUST use EXACTLY {remaining_budget} kcal to close the daily budget
- Tolerance is ±2% for the last meal (stricter than regular meals)
"""

# For regular meals
REGULAR_MEAL_INSTRUCTION = """
This is meal {current_meal_number} of {total_meals}. Hit your target within ±5% tolerance.
"""
```

**Note**: The prompt now supports parallel batch generation. `special_instructions` is filled with either `LAST_MEAL_INSTRUCTION` or `REGULAR_MEAL_INSTRUCTION` depending on meal position.

### 3.5.2 Pre-Validation Logic (recipe_generation_batch)

The `recipe_generation_batch` node uses a **hybrid parallel strategy** with pre-validation loops to ensure all meals are mathematically valid BEFORE human review.

**Hybrid Algorithm:**
```python
async def recipe_generation_batch(state: NutritionAgentState) -> dict:
    meal_times = list(state.meal_distribution.keys())
    total_meals = len(meal_times)

    # 1. Generate first N-1 meals in PARALLEL
    parallel_tasks = []
    for idx in range(total_meals - 1):
        task = _generate_single_meal_with_validation(
            meal_time=meal_times[idx],
            target_calories=state.meal_distribution[meal_times[idx]],
            user_profile=state.user_profile,
            nutritional_targets=state.nutritional_targets,
            is_last_meal=False
        )
        parallel_tasks.append(task)

    parallel_results = await asyncio.gather(*parallel_tasks)

    # 2. Calculate consumed calories from parallel results
    consumed_kcal = sum(
        meal.total_calories for meal, error in parallel_results if meal is not None
    )

    # 3. Generate LAST meal sequentially with EXACT remaining budget
    remaining_budget = state.nutritional_targets.target_calories - consumed_kcal
    last_meal_result = await _generate_single_meal_with_validation(
        meal_time=meal_times[-1],
        target_calories=remaining_budget,  # Exact budget
        user_profile=state.user_profile,
        nutritional_targets=state.nutritional_targets,
        is_last_meal=True
    )

    # 4. Combine results and handle errors
    all_results = [*parallel_results, last_meal_result]
    daily_meals = [meal for meal, _ in all_results if meal is not None]
    errors = {meal_time: err for (_, err), meal_time in zip(all_results, meal_times) if err}

    return {"daily_meals": daily_meals, "meal_generation_errors": errors}
```

**Single Meal Pre-Validation Loop:**
```python
async def _generate_single_meal_with_validation(
    meal_time: str,
    target_calories: float,
    user_profile: UserProfile,
    nutritional_targets: NutritionalTargets,
    is_last_meal: bool
) -> tuple[Meal | None, str | None]:
    MAX_ATTEMPTS = 3
    TOLERANCE = 0.05 if not is_last_meal else 0.02  # Stricter for last meal

    best_meal, best_error = None, float('inf')

    for attempt in range(MAX_ATTEMPTS):
        # 1. Generate meal via LLM
        meal = await llm.with_structured_output(Meal).ainvoke(prompt)

        # 2. Validate via RAG
        try:
            nutrition = await calculate_recipe_nutrition(meal.ingredients)
            actual_kcal = nutrition["total_recipe_kcal"]
        except Exception:
            actual_kcal = meal.total_calories  # Fallback to LLM estimate

        # 3. Check tolerance
        error_pct = abs(actual_kcal - target_calories) / target_calories
        if error_pct <= TOLERANCE:
            meal.total_calories = actual_kcal
            return (meal, None)  # Success

        # Track best attempt
        if error_pct < best_error:
            best_error = error_pct
            best_meal = meal
            best_meal.total_calories = actual_kcal

    # Return best attempt with error message
    return (best_meal, f"Failed after {MAX_ATTEMPTS} attempts. Best error: {best_error*100:.1f}%")
```

**Rationale:**
- **Hybrid approach**: Parallel for speed, sequential last meal for precision
- **~60% latency reduction**: vs fully sequential generation
- **O(n) token usage**: Each meal gets fixed context, no accumulation
- **Pre-validated meals**: Human reviewer only sees mathematically valid plans
- **Graceful degradation**: If one meal fails, others are still usable

**Trade-off:**
- Last meal is sequential (adds ~20% to total time vs full parallelization)
- Benefit: Exact budget closure, mathematically correct daily totals

### 3.6 Conditional Edges (Batch Architecture)

| From | Condition | To |
|------|-----------|-----|
| `data_collection` | `user_profile is None or missing_fields` | `data_collection` |
| `data_collection` | `user_profile complete` | `calculation` |
| `calculation` | always | `recipe_generation_batch` |
| `recipe_generation_batch` | always | `meal_review_batch` |
| `recipe_generation_single` | always | `meal_review_batch` |
| `meal_review_batch` | `review_decision == "approve"` | `validation` |
| `meal_review_batch` | `review_decision == "change_meal"` | `recipe_generation_single` |
| `meal_review_batch` | `review_decision == "regenerate_all"` | `recipe_generation_batch` |
| `validation` | `validation_errors` | `recipe_generation_batch` |
| `validation` | `valid` | `END` |

**Key Change**: No more loops for individual meals. Single batch generation → single batch review → validation.

### 3.6.1 Conditional Edge Implementations

```python
# File: src/nutrition_agent/graph.py - Routing functions
from langgraph.graph import END
from src.nutrition_agent.state import NutritionAgentState


def route_after_data_collection(state: NutritionAgentState) -> str:
    """Decide si continuar recolectando datos o pasar a calculation."""
    if state.user_profile is None or state.missing_fields:
        return "data_collection"  # Loop back
    return "calculation"


def route_after_meal_review_batch(state: NutritionAgentState) -> str:
    """Route after batch review of all meals."""
    decision = state.review_decision

    if decision == "approve":
        return "validation"
    elif decision == "change_meal":
        return "recipe_generation_single"  # Regenerate one specific meal
    elif decision == "regenerate_all":
        return "recipe_generation_batch"  # Regenerate entire batch
    else:
        # Fallback (shouldn't happen)
        return "validation"


def route_after_validation(state: NutritionAgentState) -> str:
    """Decide si el plan es válido o necesita corrección."""
    if state.validation_errors:
        return "recipe_generation_batch"  # Regenerate entire batch
    return END  # Plan válido
```

**NOTA**: Estas funciones se usan con `add_conditional_edges()` en `graph.py`.

### 3.7 Tools (src/shared/tools.py)

Migrate these tools from `src/rewoo_agent/nodes/worker/tools.py`:

| Tool Name | Purpose | Schema Class |
|-----------|---------|--------------|
| `generate_nutritional_plan` | Calculate TDEE/macros | `NutritionalInput` |
| `get_meal_distribution` | Distribute calories across meals | `MealDistInput` |
| `calculate_recipe_nutrition` | RAG lookup for ingredient nutrition | `RecipeAnalysisInput` |
| `sum_ingredients_kcal` | Verify meal calorie sum | `VerifyIngredientsInput` |
| `sum_total_kcal` | Verify daily calorie sum | `SumTotalInput` |
| `consolidate_shopping_list` | Merge ingredients into shopping list | `ConsolidateInput` |

**Keep**: `StrictBaseModel` base class with `model_config = {"extra": "forbid"}`

### 3.8 LLM Configuration (src/shared/llm.py)

```python
# Required function signature
def get_llm(model: str = "gpt-4o") -> BaseChatModel:
    """
    Returns LLM instance with Helicone proxy.

    Args:
        model: Model name (gpt-4o, gpt-4o-mini, gemini-2.5-flash)

    Returns:
        Configured ChatOpenAI or ChatGoogleGenerativeAI instance
    """
```

**Environment Variables**:
- `OPENAI_API_KEY`
- `HELICONE_API_KEY`
- `GOOGLE_API_KEY` (optional, for Gemini fallback)

### 3.8.1 Helicone Proxy Configuration

**IMPORTANTE**: Configurar Helicone desde Fase 1 para observabilidad completa.

```python
# File: src/shared/llm.py
import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

def get_llm(model: str = "gpt-4o") -> BaseChatModel:
    """
    Returns LLM instance with Helicone proxy for OpenAI models.

    Args:
        model: Model name (gpt-4o, gpt-4o-mini, gemini-2.5-flash)

    Returns:
        Configured ChatOpenAI or ChatGoogleGenerativeAI instance

    Note:
        - OpenAI models: routed through Helicone proxy
        - Gemini models: direct connection (Helicone not supported)
    """
    helicone_api_key = os.getenv("HELICONE_API_KEY")

    if model.startswith("gemini"):
        # Gemini: conexión directa (sin soporte Helicone)
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    # OpenAI: proxy via Helicone para observabilidad
    return ChatOpenAI(
        model=model,
        base_url="https://oai.helicone.ai/v1",
        default_headers={"Helicone-Auth": f"Bearer {helicone_api_key}"}
    )
```

**Referencia de implementación funcional**: `src/agent/llm.py`

**IMPORTANTE**: El código existente en `src/agent/llm.py` usa `OpenAI` (legacy completion model). Debe ser reemplazado con `ChatOpenAI` (chat model) para soportar structured outputs requeridos por los nodos del nutrition_agent.

### 3.9 API Integration (src/api/main.py)

Register the nutrition_agent with CopilotKit:

```python
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from src.nutrition_agent.graph import graph as nutrition_graph

# In the CopilotKitRemoteEndpoint setup:
LangGraphAGUIAgent(
    name="nutrition_agent",
    description="Nutrition planning agent with HITL support",
    graph=nutrition_graph,
)
```

**NOTA**: La clase correcta es `LangGraphAGUIAgent`, NO `LangGraphAgent`.

---

## 4. Implementation Phases

### Phase 1: Shared Foundation

**Goal**: Create shared utilities used by all agents.

**Files to create**:
1. `src/shared/enums.py` - Type definitions (ActivityLevel, Objective, DietType, MealTime)
2. `src/shared/llm.py` - LLM factory with Helicone proxy
3. `src/shared/tools.py` - Migrate 6 tools from rewoo_agent
4. `src/shared/__init__.py` - Export all public symbols

**Tasks**:
- [ ] Create `src/shared/enums.py` with all StrEnum types from Section 3.1
- [ ] Create `src/shared/llm.py` with `get_llm()` function (see Section 3.8.1 for Helicone config)
- [ ] Copy tools from `src/rewoo_agent/nodes/worker/tools.py` to `src/shared/tools.py`
- [ ] Migrate auxiliary RAG classes: `StrictBaseModel`, `ResourceLoader`, `NutriFacts`, `ProcessedItem`, `NutritionResult`
- [ ] Update imports in tools.py to use `src/shared/enums.py`
- [ ] Update `src/shared/__init__.py` to export: `get_llm`, `ActivityLevel`, `Objective`, `DietType`, `MealTime`, and all tool functions
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(shared): add shared foundation (enums, llm, tools)`

**Verification**:
```bash
python -c "from src.shared import get_llm, ActivityLevel, generate_nutritional_plan"
python -c "from src.shared.tools import ResourceLoader, NutriFacts, NutritionResult, ProcessedItem, StrictBaseModel"
```

---

### Phase 2: Models

**Goal**: Define all Pydantic models for the nutrition agent.

**Files to create**:
1. `src/nutrition_agent/models/user_profile.py`
2. `src/nutrition_agent/models/nutritional_targets.py`
3. `src/nutrition_agent/models/diet_plan.py` (Meal, Macronutrients, ShoppingListItem, DietPlan)
4. `src/nutrition_agent/models/__init__.py` - Export all models

**Tasks**:
- [ ] Create `user_profile.py` with `UserProfile` model per Section 3.2.1
- [ ] Create `nutritional_targets.py` with `NutritionalTargets` model per Section 3.2.2
- [ ] Create `diet_plan.py` with `Meal`, `Macronutrients`, `ShoppingListItem`, `DietPlan` per Sections 3.2.3-3.2.6
- [ ] Update `models/__init__.py` to export all models
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(nutrition-agent): add Pydantic models`

**Verification**:
```bash
python -c "from src.nutrition_agent.models import UserProfile, NutritionalTargets, DietPlan, Meal"
```

---

### Phase 3: State and Prompts

**Goal**: Define agent state and LLM prompts.

**Files to create/modify**:
1. `src/nutrition_agent/state.py` - NutritionAgentState
2. `src/nutrition_agent/prompts/data_collection.py` - DATA_COLLECTION_PROMPT
3. `src/nutrition_agent/prompts/recipe_generation.py` - RECIPE_GENERATION_PROMPT
4. `src/nutrition_agent/prompts/__init__.py` - Export prompts

**Tasks**:
- [ ] Implement `state.py` with `NutritionAgentState` per Section 3.3 (include all imports!)
- [ ] Create `DATA_COLLECTION_PROMPT` in `prompts/data_collection.py` per Section 3.5.1
- [ ] Create `RECIPE_GENERATION_PROMPT` in `prompts/recipe_generation.py` per Section 3.5.1
- [ ] Update `prompts/__init__.py` to export both prompts
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(nutrition-agent): add state and prompts`

**Verification**:
```bash
python -c "from src.nutrition_agent.state import NutritionAgentState; from src.nutrition_agent.prompts import DATA_COLLECTION_PROMPT, RECIPE_GENERATION_PROMPT"
```

---

### Phase 4: Nodes Implementation

**Goal**: Implement all 6 graph nodes (batch architecture).

**Files to create**:
1. `src/nutrition_agent/nodes/data_collection.py`
2. `src/nutrition_agent/nodes/calculation.py`
3. `src/nutrition_agent/nodes/recipe_generation_batch.py` - **NEW** (parallel batch generation)
4. `src/nutrition_agent/nodes/recipe_generation_single.py` - **NEW** (single meal regeneration for HITL)
5. `src/nutrition_agent/nodes/meal_review_batch.py` - **NEW** (batch review of complete plan)
6. `src/nutrition_agent/nodes/validation.py`
7. `src/nutrition_agent/nodes/__init__.py` - Export all node functions

**Tasks**:
- [ ] Implement `data_collection.py` per Section 3.5 Node 1
  - Use `llm.with_structured_output(UserProfile)`
  - Return empty dict if profile already complete
- [ ] Implement `calculation.py` per Section 3.5 Node 2
  - Use Mifflin-St Jeor formula (NO LLM)
  - Calculate meal distribution using `get_meal_distribution` tool or inline logic
  - Return `{"nutritional_targets": NutritionalTargets, "meal_distribution": dict}`
- [ ] Implement `recipe_generation_batch.py` per Section 3.5 Node 3
  - Use `asyncio.gather()` for parallel generation of N-1 meals
  - Generate last meal sequentially with exact remaining budget
  - Implement helper `_generate_single_meal_with_validation()` (Section 3.5.2)
  - Use `calculate_recipe_nutrition` for RAG validation per meal
  - Handle partial failures with `meal_generation_errors` dict
  - Return `{"daily_meals": [Meal, ...], "meal_generation_errors": {}}`
- [ ] Implement `recipe_generation_single.py` per Section 3.5 Node 3b
  - Regenerate ONE specific meal after user requests "change_meal"
  - Use `state.selected_meal_to_change` and `state.user_feedback`
  - Replace meal in `daily_meals` list
  - Return `{"daily_meals": [...], "review_decision": None}` to reset decision
- [ ] Implement `meal_review_batch.py` per Section 3.5 Node 4
  - Use `from langgraph.types import interrupt`
  - Send complete plan in interrupt payload
  - Return `{"review_decision": str, "selected_meal_to_change": str | None, "user_feedback": str | None}`
- [ ] Implement `validation.py` per Section 3.5 Node 5
  - Use `state.daily_meals` (not meals_completed)
  - Sum calories with ±5% tolerance
  - Build `DietPlan` if valid
  - Return `validation_errors` if invalid
- [ ] Update `nodes/__init__.py` to export all node functions
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(nutrition-agent): implement all graph nodes (batch architecture)`

**Verification**:
```bash
python -c "from src.nutrition_agent.nodes import data_collection, calculation, recipe_generation_batch, recipe_generation_single, meal_review_batch, validation"
```

---

### Phase 5: Graph Assembly

**Goal**: Assemble the LangGraph StateGraph with nodes and edges (batch architecture).

**Files to create/modify**:
1. `src/nutrition_agent/graph.py` - StateGraph definition
2. `src/nutrition_agent/llm.py` - Local LLM config (optional, can reuse shared)
3. `src/nutrition_agent/__init__.py` - Export graph

**Tasks**:
- [ ] Implement `graph.py`:
  - Import all nodes from `src.nutrition_agent.nodes`
  - Import routing functions per Section 3.6.1
  - Create `StateGraph(NutritionAgentState)`
  - Add all 6 nodes with `graph.add_node()`
  - Set entry point: `graph.set_entry_point("data_collection")`
  - Add conditional edge from data_collection using `route_after_data_collection`
  - Add edge from calculation to recipe_generation_batch
  - Add edge from recipe_generation_batch to meal_review_batch
  - Add edge from recipe_generation_single to meal_review_batch
  - Add conditional edge from meal_review_batch using `route_after_meal_review_batch`
  - Add conditional edge from validation using `route_after_validation`
  - Compile graph: `graph = builder.compile()`
- [ ] Export `graph` from `__init__.py`
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(nutrition-agent): assemble LangGraph state graph (batch architecture)`

**Graph Assembly Template**:
```python
# File: src/nutrition_agent/graph.py
from langgraph.graph import StateGraph, END

from src.nutrition_agent.state import NutritionAgentState
from src.nutrition_agent.nodes import (
    data_collection,
    calculation,
    recipe_generation_batch,
    recipe_generation_single,
    meal_review_batch,
    validation,
)


def route_after_data_collection(state: NutritionAgentState) -> str:
    """Decide si continuar recolectando datos o pasar a calculation."""
    if state.user_profile is None or state.missing_fields:
        return "data_collection"
    return "calculation"


def route_after_meal_review_batch(state: NutritionAgentState) -> str:
    """Route after batch review of all meals."""
    decision = state.review_decision
    if decision == "approve":
        return "validation"
    elif decision == "change_meal":
        return "recipe_generation_single"
    elif decision == "regenerate_all":
        return "recipe_generation_batch"
    return "validation"  # Fallback


def route_after_validation(state: NutritionAgentState) -> str:
    """Decide si el plan es válido o necesita corrección."""
    if state.validation_errors:
        return "recipe_generation_batch"
    return END


# Build the graph
builder = StateGraph(NutritionAgentState)

# Add nodes (6 total for batch architecture)
builder.add_node("data_collection", data_collection)
builder.add_node("calculation", calculation)
builder.add_node("recipe_generation_batch", recipe_generation_batch)
builder.add_node("recipe_generation_single", recipe_generation_single)
builder.add_node("meal_review_batch", meal_review_batch)
builder.add_node("validation", validation)

# Set entry point
builder.set_entry_point("data_collection")

# Add edges
builder.add_conditional_edges(
    "data_collection",
    route_after_data_collection,
    {"data_collection": "data_collection", "calculation": "calculation"}
)

builder.add_edge("calculation", "recipe_generation_batch")

builder.add_edge("recipe_generation_batch", "meal_review_batch")

builder.add_edge("recipe_generation_single", "meal_review_batch")  # Returns to review after single meal change

builder.add_conditional_edges(
    "meal_review_batch",
    route_after_meal_review_batch,
    {
        "validation": "validation",
        "recipe_generation_single": "recipe_generation_single",
        "recipe_generation_batch": "recipe_generation_batch"
    }
)

builder.add_conditional_edges(
    "validation",
    route_after_validation,
    {"recipe_generation_batch": "recipe_generation_batch", END: END}
)

# Compile
graph = builder.compile()
```

**Verification**:
```bash
python -c "from src.nutrition_agent import graph; print(graph.nodes)"
# Expected: dict_keys(['data_collection', 'calculation', 'recipe_generation_batch', 'recipe_generation_single', 'meal_review_batch', 'validation'])
```

---

### Phase 6: API Integration

**Goal**: Register nutrition_agent with FastAPI/CopilotKit.

**Files to modify**:
1. `src/api/main.py` - Register new agent
2. `langgraph.json` - Add nutrition_agent entry (if exists)

**Tasks**:
- [ ] Import `graph` from `src.nutrition_agent` in `main.py`
- [ ] Add `LangGraphAGUIAgent` for nutrition_agent per Section 3.9 (NOT `LangGraphAgent`)
- [ ] Update `langgraph.json` if it exists (add nutrition_agent)
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `feat(api): register nutrition_agent with CopilotKit`

**Verification**:
```bash
# Start server and check health
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl http://localhost:8000/health
# Kill server
pkill -f uvicorn
```

---

### Phase 7: Testing & Quality Assurance

**Goal**: Asegurar calidad del código con tests automatizados verificables.

**Test Structure**:
```
tests/
├── quick_tool_tests/      # Smoke tests (scripts standalone async)
│   ├── __init__.py
│   ├── calculate_recipe_nutrition_test.py  # Existente
│   └── test_calculation_node.py            # Nuevo
├── evaluation/            # RAGAS evaluations
│   ├── __init__.py
│   ├── eval_fetch_recipe_nutrition_facts.py  # Existente
│   └── eval_recipe_generation.py             # Nuevo
└── tools/                 # Unit tests (pytest)
    ├── __init__.py
    ├── test_generate_nutritional_plan.py    # Existente
    └── test_shared_tools.py                 # Nuevo
```

**Files to create**:
1. `tests/tools/test_shared_tools.py` - Unit tests para las 6 herramientas migradas
2. `tests/quick_tool_tests/test_calculation_node.py` - Smoke test del nodo calculation
3. `tests/evaluation/eval_recipe_generation.py` - RAGAS evaluation con ground truth

**Tasks**:
- [ ] Create `tests/tools/test_shared_tools.py` with tests for all 6 migrated tools
- [ ] Create `tests/quick_tool_tests/test_calculation_node.py` for calculation node smoke test
- [ ] Create `tests/evaluation/eval_recipe_generation.py` with ground truth dataset
- [ ] Run `pytest tests/tools/ -v` and verify 100% pass
- [ ] Run smoke tests and verify no exceptions
- [ ] Run `pre-commit run --all-files`
- [ ] Commit: `test(nutrition-agent): add automated test suite`

**Verification Commands**:
```bash
# Unit tests (pytest) - MUST PASS
pytest tests/tools/ -v --tb=short

# Smoke tests (standalone scripts)
python tests/quick_tool_tests/calculate_recipe_nutrition_test.py
python tests/quick_tool_tests/test_calculation_node.py

# RAGAS evaluation (requires OPENAI_API_KEY and PINECONE_API_KEY)
python tests/evaluation/eval_recipe_generation.py

# Coverage report (optional)
pytest tests/ --cov=src/nutrition_agent --cov-report=term-missing
```

**Success Criteria**:
- [ ] `pytest tests/tools/ -v` passes with 0 failures
- [ ] Smoke tests execute without exceptions
- [ ] RAGAS evaluation generates metrics (answer_correctness, answer_similarity)

---

## 5. Verification Checklist

After all phases complete, verify:

- [ ] `pre-commit run --all-files` passes
- [ ] All imports work without errors
- [ ] Server starts without errors
- [ ] `/health` endpoint returns 200
- [ ] `spec/progress.txt` shows all phases complete
- [ ] 7 commits exist (one per phase)
- [ ] `pytest tests/tools/ -v` passes with 0 failures
- [ ] Smoke tests in `tests/quick_tool_tests/` execute successfully
- [ ] RAGAS evaluation metrics generated (optional, requires API keys)

**Final Test** (manual):
1. Start backend: `uvicorn src.api.main:app --reload`
2. Start frontend: `cd ui && npm run dev`
3. Open http://localhost:3000
4. Start conversation: "I want a meal plan"
5. Verify conversational data collection works
6. Verify meal generation works
7. Verify HITL review pauses for approval

---

## Appendix A: File Reference

| File | Phase | Type |
|------|-------|------|
| `src/shared/enums.py` | 1 | Create |
| `src/shared/llm.py` | 1 | Create |
| `src/shared/tools.py` | 1 | Create |
| `src/shared/__init__.py` | 1 | Modify |
| `src/nutrition_agent/models/user_profile.py` | 2 | Create |
| `src/nutrition_agent/models/nutritional_targets.py` | 2 | Create |
| `src/nutrition_agent/models/diet_plan.py` | 2 | Create |
| `src/nutrition_agent/models/__init__.py` | 2 | Modify |
| `src/nutrition_agent/state.py` | 3 | Create/**MODIFY** |
| `src/nutrition_agent/prompts/data_collection.py` | 3 | Modify |
| `src/nutrition_agent/prompts/recipe_generation.py` | 3 | Create/**MODIFY** |
| `src/nutrition_agent/prompts/__init__.py` | 3 | Modify |
| `src/nutrition_agent/nodes/data_collection.py` | 4 | Create |
| `src/nutrition_agent/nodes/calculation.py` | 4 | Create |
| `src/nutrition_agent/nodes/recipe_generation_batch.py` | 4 | **Create (NEW)** |
| `src/nutrition_agent/nodes/recipe_generation_single.py` | 4 | **Create (NEW)** |
| `src/nutrition_agent/nodes/meal_review_batch.py` | 4 | **Create (NEW)** |
| `src/nutrition_agent/nodes/validation.py` | 4 | Create |
| `src/nutrition_agent/nodes/__init__.py` | 4 | Modify |
| `src/nutrition_agent/graph.py` | 5 | Create |
| `src/nutrition_agent/__init__.py` | 5 | Modify |
| `src/api/main.py` | 6 | Modify |
| `tests/tools/test_shared_tools.py` | 7 | Create |
| `tests/quick_tool_tests/test_calculation_node.py` | 7 | Create |
| `tests/evaluation/eval_recipe_generation.py` | 7 | Create |

**Note**: Files marked **MODIFY** in Phase 3 require updates to match batch architecture if already implemented.

---

## Appendix B: Reference Documentation

For detailed code examples and additional context, see:
- `spec/02-implementation-examples.md` - Code samples
- `spec/02-migration-implementation-plan.md` - Detailed migration spec
- `spec/03-agregar-HITL.md` - HITL feature specification
- `spec/flujo-grafo-detail.md` - Graph flow diagrams

---

## Appendix C: Changelog (Fixes Applied)

This document (`prd-fixed.md`) includes the following corrections from the original `prd.md`:

| # | Section | Fix Applied |
|---|---------|-------------|
| 1 | 3.2.1 | Changed `weight` and `height` from `float` to `int` for compatibility with existing tools |
| 2 | 3.2.5 | Changed `ShoppingListItem` structure from 3 fields to 2 fields (`food`, `quantity`) |
| 3 | 3.3 | Added complete imports at top of State definition |
| 4 | 3.3 | Changed mutable defaults `= []` to `Field(default_factory=list)` |
| 5 | 3.5.1 | **NEW SECTION**: Added concrete prompt templates for data_collection and recipe_generation |
| 6 | 3.6.1 | **NEW SECTION**: Added routing function implementations |
| 7 | 3.9 | Fixed typo: `LangGraphAgent` → `LangGraphAGUIAgent` |
| 8 | Phase 5 | Added graph assembly template code |
| 9 | Phase 6 | Updated task to use correct class name |
| 10 | 3.8.1 | Added note about legacy `OpenAI` vs `ChatOpenAI` |

---

## Appendix D: Architecture Change - Parallel Batch Generation (v2)

**Date**: 2026-01-24

### Problem Statement

The original sequential architecture had two critical issues:

1. **High Latency**: With N meals, the cycle `recipe_generation → meal_review` repeated N times, causing N HITL interruptions and N sequential LLM calls.

2. **O(n²) Token Growth**: Each invocation of `recipe_generation` received the growing `meals_completed` list, causing exponential token consumption.

### Solution: Hybrid Parallel Batch Architecture

| Change | Before | After |
|--------|--------|-------|
| Meal Generation | Sequential (N calls) | Parallel (N-1 calls) + 1 sequential |
| HITL Review | N reviews (per meal) | 1 review (complete plan) |
| Token Growth | O(n²) | O(n) |
| Latency | ~N × (LLM + HITL) | ~1 × (LLM parallel) + 1 × HITL |
| State Fields | `current_meal_index`, `meals_completed`, `skip_remaining_reviews` | `daily_meals`, `meal_generation_errors`, `selected_meal_to_change` |

### Sections Modified

| Section | Change Summary |
|---------|----------------|
| 1.1 | Updated project goals to reflect batch architecture |
| 3.3 | Replaced sequential state fields with batch fields |
| 3.4 | New graph flow diagram with batch nodes |
| 3.5 Node 3 | `recipe_generation` → `recipe_generation_batch` |
| 3.5 Node 3b | **NEW**: `recipe_generation_single` for HITL changes |
| 3.5 Node 4 | `meal_review` → `meal_review_batch` |
| 3.5 Node 5 | Updated to use `daily_meals` |
| 3.5.1 | Updated prompts for batch context |
| 3.5.2 | New hybrid algorithm with `asyncio.gather()` |
| 3.6 | Updated conditional edges table |
| 3.6.1 | New routing functions for batch nodes |
| Phase 4 | Updated file list and tasks |
| Phase 5 | Updated graph assembly template |
| Appendix A | Updated file reference table |

### Trade-offs

| Aspect | Benefit | Cost |
|--------|---------|------|
| Latency | ~60% reduction | Slightly more complex implementation |
| Tokens | ~40% reduction | N/A |
| Last Meal Precision | Exact budget (sequential) | Adds ~20% to parallel time |
| Error Handling | Graceful partial failures | More states to manage |
| UX | Single review point | Less granular feedback |

### Impact on Completed Phases

**Phase 3 (State and Prompts)** requires modifications:
- `state.py`: Replace fields per new Section 3.3
- `prompts/recipe_generation.py`: Update prompt per new Section 3.5.1
