"""Prompt templates for the recipe_generation_batch and recipe_generation_single nodes.

This module provides prompts for parallel batch meal generation, optimized for:
- Generating meals independently (no sequential context accumulation)
- Hybrid approach: N-1 meals parallel, last meal sequential with exact budget
- ~60% latency reduction vs sequential generation
"""

RECIPE_GENERATION_PROMPT = """\
Generate a single meal recipe for a complete daily meal plan in Spanish.

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
- Target Calories for THIS meal: {target_calories} kcal (+/-5% tolerance)
- This meal is part of a {total_meals}-meal daily plan

{special_instructions}

Generate a Meal with the following structure:
- meal_time: "{meal_time}"
- title: Short descriptive name (5-150 characters)
- description: Brief overview of the meal (10-500 characters)
- total_calories: Must be within +/-5% of {target_calories}
- ingredients: List of STRUCTURED ingredients, each with:
  - nombre: Ingredient name in Spanish (e.g., "Pechuga de pollo")
  - cantidad_display: Human-readable quantity with CORRECT unit:
    - Solids/meats: use grams (e.g., "200g", "150g")
    - Liquids (aceite, leche, caldo): use ml (e.g., "15ml", "200ml")
    - Countable items (huevos, tortillas): use unidades (e.g., "3 unidades", "2 unidades")
  - peso_gramos: Weight in grams (numeric, for nutritional calculation — always in grams regardless of display unit)
  - kcal: Kilocalories for THIS ingredient in the specified quantity
- preparation: Numbered list of cooking steps
- alternative (optional): A simpler alternative if available

CRITICAL CONSTRAINT - Ingredient kcal consistency:
The SUM of all ingredient kcal values MUST EQUAL total_calories (±0.5 kcal).
Example: if total_calories = 350, then ingredient kcals must sum to 350.

Example ingredients format:
  ingredients: [
    {{"nombre": "Pechuga de pollo", "cantidad_display": "200g", "peso_gramos": 200.0, "kcal": 330.0}},
    {{"nombre": "Aceite de oliva", "cantidad_display": "10ml", "peso_gramos": 9.0, "kcal": 80.0}},
    {{"nombre": "Huevo entero", "cantidad_display": "2 unidades", "peso_gramos": 100.0, "kcal": 143.0}}
  ]
  total_calories: 553.0  (330 + 80 + 143 = 553 ✓)

IMPORTANT:
- Be PRECISE with per-ingredient kcal - they will be summed and verified
- If total calories don't match target (±5%), you'll be asked to regenerate
- Use realistic portion sizes (e.g., "pollo 150g" not "pollo 500g")
- Use PRECISE ingredient names (e.g., "Platano maduro" not "platano")
- Do NOT include any foods from the excluded list: {excluded_foods}
- Keep the meal appropriate for {diet_type} diet
- Use metric units (grams, ml) for all quantities
- Use CORRECT units in cantidad_display: grams for solids, ml for liquids (aceite, leche, caldo), unidades for countable items (huevos, tortillas)
- This meal will be generated in parallel with other meals, so focus on hitting
  YOUR target precisely without worrying about other meals
"""  # noqa: E501

# Instruction for the LAST meal (stricter tolerance, exact budget)
LAST_MEAL_INSTRUCTION = """\
CRITICAL: This is the LAST meal of the day.
- Other meals have already been generated with total: {consumed_kcal} kcal
- You MUST use EXACTLY {remaining_budget} kcal to close the daily budget
- Tolerance is +/-2% for the last meal (stricter than regular meals)
- Adjust ingredient quantities precisely to hit this exact number"""

# Instruction for regular meals (standard tolerance)
REGULAR_MEAL_INSTRUCTION = """\
This is meal {current_meal_number} of {total_meals}.
Hit your target calories ({target_calories} kcal) within +/-5% tolerance."""
