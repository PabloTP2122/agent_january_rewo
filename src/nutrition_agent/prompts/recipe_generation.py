"""Prompt template for the recipe_generation node.

This prompt guides the LLM to generate individual meal recipes that fit
the user's nutritional plan, with precise calorie targeting.
"""

RECIPE_GENERATION_PROMPT = """\
Generate a single meal recipe that fits the user's nutritional plan.

User Profile:
- Objective: {objective}
- Diet Type: {diet_type}
- Excluded Foods: {excluded_foods}

Daily Context:
- Total Daily Target: {daily_target_calories} kcal
- Already Consumed: {consumed_kcal} kcal (meals 1 to {current_meal_index})
- Remaining Budget: {remaining_budget} kcal

Meal Requirements:
- Meal Time: {meal_time}
- Target Calories for THIS meal: {target_calories} kcal (+/-5% tolerance)
- This is meal {current_meal_number} of {total_meals}

{is_last_meal_instruction}

Generate a Meal with the following structure:
- meal_time: "{meal_time}"
- title: Short descriptive name (5-150 characters)
- description: Brief overview of the meal (10-500 characters)
- total_calories: Must be within +/-5% of {target_calories}
- ingredients: List of ingredients with quantities in grams (e.g., "pollo 150g")
- preparation: Numbered list of cooking steps
- alternative (optional): A simpler alternative if available

IMPORTANT:
- Be PRECISE with calorie estimation
- Ingredients will be validated via RAG lookup
- If this is the last meal, hit the target EXACTLY to close the daily budget
- Do NOT include any foods from the excluded list: {excluded_foods}
- Keep the meal appropriate for {diet_type} diet
- Ensure total_calories is realistic for the ingredients listed
- Use metric units (grams, ml) for all quantities
"""

# Instruction appended when generating the last meal of the day
LAST_MEAL_INSTRUCTION = """\
CRITICAL: This is the LAST meal of the day. You must use EXACTLY the remaining
budget ({remaining_budget} kcal) to close out the daily calorie target. Adjust
ingredient quantities precisely to hit this number."""

# Instruction for non-last meals
REGULAR_MEAL_INSTRUCTION = """\
Use the target calories ({target_calories} kcal) as your guide. Small variations
within +/-5% are acceptable."""
