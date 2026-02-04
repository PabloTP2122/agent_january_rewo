"""RAGAS Evaluation for Recipe Generation Node.

This script evaluates the quality of generated meals by comparing
them against ground truth expectations using LLM-as-a-judge.

Metrics used:
- answer_correctness: Verifies factual accuracy (calories, ingredients)
- answer_similarity: Semantic similarity to expected output

Requirements:
- OPENAI_API_KEY (for judge LLM)
- PINECONE_API_KEY (for RAG validation, optional)

Run: python tests/evaluation/eval_recipe_generation.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import TypedDict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from datasets import Dataset  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.metrics._answer_correctness import AnswerCorrectness  # noqa: E402
from ragas.metrics._answer_similarity import AnswerSimilarity  # noqa: E402

from src.nutrition_agent.models import (  # noqa: E402
    Meal,
    NutritionalTargets,
    UserProfile,
)
from src.nutrition_agent.prompts import (  # noqa: E402
    RECIPE_GENERATION_PROMPT,
    REGULAR_MEAL_INSTRUCTION,
)
from src.shared import get_llm  # noqa: E402
from src.shared.enums import ActivityLevel, DietType, Objective  # noqa: E402

# GROUND TRUTH DATASET


class TestCase(TypedDict):
    """Type definition for evaluation test cases."""

    question: str
    user_profile: UserProfile
    nutritional_targets: NutritionalTargets
    meal_time: str
    target_calories: float
    ground_truth: str


# Define test cases with expected outcomes
# Ground truth focuses on:
# - Correct meal_time
# - Calories within ±10% of target (realistic for LLM)
# - Required fields present
# - Diet restrictions respected

test_cases: list[TestCase] = [
    {
        "question": "Generate a 600 kcal breakfast for muscle gain, normal diet",
        "user_profile": UserProfile(
            age=25,
            gender="male",
            weight=80,
            height=180,
            activity_level=ActivityLevel.VERY_ACTIVE,
            objective=Objective.MUSCLE_GAIN,
            diet_type=DietType.NORMAL,
            excluded_foods=[],
            number_of_meals=3,
        ),
        "nutritional_targets": NutritionalTargets(
            bmr=1800.0,
            tdee=3100.0,
            target_calories=3410.0,
            protein_grams=176.0,
            protein_percentage=20.6,
            carbs_grams=350.0,
            carbs_percentage=41.1,
            fat_grams=145.0,
            fat_percentage=38.3,
        ),
        "meal_time": "Desayuno",
        "target_calories": 600.0,
        "ground_truth": json.dumps(
            {
                "expected_meal_time": "Desayuno",
                "expected_calories_range": [540, 660],  # ±10%
                "required_fields": [
                    "title",
                    "description",
                    "ingredients",
                    "preparation",
                ],
                "must_have_protein": True,  # Muscle gain needs protein
                "excluded_foods_respected": True,
            }
        ),
    },
    {
        "question": "Generate a 400 kcal dinner for fat loss, no seafood",
        "user_profile": UserProfile(
            age=35,
            gender="female",
            weight=70,
            height=165,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            objective=Objective.FAT_LOSS,
            diet_type=DietType.NORMAL,
            excluded_foods=["mariscos", "camarones", "pescado"],
            number_of_meals=3,
        ),
        "nutritional_targets": NutritionalTargets(
            bmr=1400.0,
            tdee=2170.0,
            target_calories=1801.0,
            protein_grams=154.0,
            protein_percentage=34.2,
            carbs_grams=150.0,
            carbs_percentage=33.3,
            fat_grams=65.0,
            fat_percentage=32.5,
        ),
        "meal_time": "Cena",
        "target_calories": 400.0,
        "ground_truth": json.dumps(
            {
                "expected_meal_time": "Cena",
                "expected_calories_range": [360, 440],  # ±10%
                "required_fields": [
                    "title",
                    "description",
                    "ingredients",
                    "preparation",
                ],
                "must_exclude": ["mariscos", "camarones", "pescado"],
                "should_be_light": True,  # Fat loss + dinner
            }
        ),
    },
    {
        "question": "Generate a 500 kcal lunch for keto diet maintenance",
        "user_profile": UserProfile(
            age=40,
            gender="male",
            weight=85,
            height=175,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            objective=Objective.MAINTENANCE,
            diet_type=DietType.KETO,
            excluded_foods=[],
            number_of_meals=3,
        ),
        "nutritional_targets": NutritionalTargets(
            bmr=1750.0,
            tdee=2406.0,
            target_calories=2406.0,
            protein_grams=150.0,
            protein_percentage=25.0,
            carbs_grams=30.0,
            carbs_percentage=5.0,
            fat_grams=187.0,
            fat_percentage=70.0,
        ),
        "meal_time": "Comida",
        "target_calories": 500.0,
        "ground_truth": json.dumps(
            {
                "expected_meal_time": "Comida",
                "expected_calories_range": [450, 550],  # ±10%
                "required_fields": [
                    "title",
                    "description",
                    "ingredients",
                    "preparation",
                ],
                "keto_requirements": {
                    "low_carb": True,  # Should minimize carbs
                    "high_fat": True,  # Should emphasize fats
                },
            }
        ),
    },
]


# MEAL GENERATION FUNCTION


async def generate_meal(
    user_profile: UserProfile,
    nutritional_targets: NutritionalTargets,
    meal_time: str,
    target_calories: float,
) -> Meal:
    """Generate a single meal using the recipe generation prompt."""
    excluded_foods_str = ", ".join(user_profile.excluded_foods) or "ninguno"

    special_instructions = REGULAR_MEAL_INSTRUCTION.format(
        current_meal_number=1,
        total_meals=3,
        target_calories=round(target_calories, 1),
    )

    prompt = RECIPE_GENERATION_PROMPT.format(
        objective=user_profile.objective.value,
        diet_type=user_profile.diet_type.value,
        excluded_foods=excluded_foods_str,
        daily_target_calories=round(nutritional_targets.target_calories, 1),
        daily_protein_grams=round(nutritional_targets.protein_grams, 1),
        daily_carbs_grams=round(nutritional_targets.carbs_grams, 1),
        daily_fat_grams=round(nutritional_targets.fat_grams, 1),
        meal_time=meal_time,
        target_calories=round(target_calories, 1),
        total_meals=3,
        special_instructions=special_instructions,
    )

    llm = get_llm("gpt-4o")
    structured_llm = llm.with_structured_output(Meal)

    result: Meal = await structured_llm.ainvoke(prompt)
    # Cast to Meal since with_structured_output returns BaseModel
    return result


# DATASET GENERATION


async def generate_evaluation_dataset() -> Dataset:
    """Execute meal generation and build evaluation dataset."""
    data_samples: dict[str, list[str]] = {
        "question": [],
        "answer": [],
        "ground_truth": [],
    }

    print("Generating meals for evaluation...")

    for i, case in enumerate(test_cases):
        print(f"\n  [{i + 1}/{len(test_cases)}] {case['question']}")

        try:
            # Extract typed values from test case
            user_profile = case["user_profile"]
            nutritional_targets = case["nutritional_targets"]
            meal_time = case["meal_time"]
            target_calories = case["target_calories"]

            meal = await generate_meal(
                user_profile=user_profile,
                nutritional_targets=nutritional_targets,
                meal_time=meal_time,
                target_calories=target_calories,
            )

            # Convert meal to JSON for evaluation
            answer = json.dumps(
                {
                    "meal_time": meal.meal_time.value,
                    "title": meal.title,
                    "description": meal.description,
                    "total_calories": meal.total_calories,
                    "ingredients": meal.ingredients,
                    "preparation": meal.preparation,
                    "alternative": meal.alternative,
                },
                ensure_ascii=False,
            )

            print(f"    Generated: {meal.title} ({meal.total_calories:.0f} kcal)")

        except Exception as e:
            answer = json.dumps({"error": str(e)})
            print(f"    ERROR: {e}")

        data_samples["question"].append(case["question"])
        data_samples["answer"].append(answer)
        data_samples["ground_truth"].append(case["ground_truth"])

    return Dataset.from_dict(data_samples)


# RAGAS EVALUATION


async def run_evaluation() -> None:
    """Run RAGAS evaluation on generated meals."""
    print("\n" + "=" * 70)
    print("RECIPE GENERATION EVALUATION (RAGAS)")
    print("=" * 70)

    # Generate dataset with actual meal outputs
    dataset = await generate_evaluation_dataset()

    print("\n" + "-" * 70)
    print("Running RAGAS evaluation (LLM Judge: GPT-4o)...")
    print("-" * 70)

    # Select metrics for structured output evaluation
    metrics = [AnswerCorrectness(), AnswerSimilarity()]

    # Use GPT-4o as judge for higher accuracy
    eval_llm = ChatOpenAI(model="gpt-4o")

    # Map our dataset columns to ragas schema: user_input, response, reference
    column_map = {
        "user_input": "question",
        "response": "answer",
        "reference": "ground_truth",
    }

    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=eval_llm,
        column_map=column_map,
    )

    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(results)

    # Export to Pandas for detailed analysis
    df = results.to_pandas()

    print("\nDetailed Results by Test Case:")
    print("-" * 70)
    for idx, row in df.iterrows():
        # Results use ragas column names (user_input, not question) after column_map
        q = str(row["user_input"])
        print(f"\nCase {idx + 1}: {q[:50]}{'...' if len(q) > 50 else ''}")
        print(f"  Answer Correctness: {row['answer_correctness']:.3f}")
        print(f"  Answer Similarity:  {row['answer_similarity']:.3f}")

    # Calculate averages
    avg_correctness = df["answer_correctness"].mean()
    avg_similarity = df["answer_similarity"].mean()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Average Answer Correctness: {avg_correctness:.3f}")
    print(f"Average Answer Similarity:  {avg_similarity:.3f}")

    # Quality thresholds
    if avg_correctness >= 0.7 and avg_similarity >= 0.7:
        print("\n[PASS] Recipe generation meets quality thresholds")
    else:
        print("\n[WARN] Recipe generation below quality thresholds")
        print("  Target: correctness >= 0.7, similarity >= 0.7")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
