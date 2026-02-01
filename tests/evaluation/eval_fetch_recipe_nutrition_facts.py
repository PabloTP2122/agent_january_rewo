"""RAGAS Evaluation for calculate_recipe_nutrition RAG Tool.

This script tests the nutritional RAG lookup tool by comparing
actual results against ground truth expectations using LLM-as-a-judge.

Metrics used:
- answer_correctness: Verifies factual accuracy (calories, ingredient matching)
- answer_similarity: Semantic similarity to expected output

Requirements:
- OPENAI_API_KEY (for judge LLM and embeddings)
- PINECONE_API_KEY (for RAG vector store)
- PINECONE_INDEX_NAME (index with nutritional data)

Run: python tests/evaluation/eval_fetch_recipe_nutrition_facts.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from datasets import Dataset  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.dataset_schema import EvaluationResult  # noqa: E402
from ragas.metrics._answer_correctness import AnswerCorrectness  # noqa: E402
from ragas.metrics._answer_similarity import AnswerSimilarity  # noqa: E402

from src.nutrition_agent.models.tools import IngredientInput
from src.nutrition_agent.nodes.recipe_generation.tool import (
    calculate_recipe_nutrition,  # noqa: E402
)

# GROUND TRUTH DATASET

# Define test cases with expected outcomes.
# Ground truth uses the ACTUAL output schema from calculate_recipe_nutrition:
# - processed_items: list of {input_name, matched_db_name, total_kcal, notes}
# - total_recipe_kcal: float
# - warnings: str | None

test_cases: list[dict[str, Any]] = [
    {
        "question": "Analiza: 100g de Plátano maduro",
        "inputs": [IngredientInput(nombre="Plátano maduro", peso_gramos=100)],
        "ground_truth": json.dumps(
            {
                "processed_items": [
                    {
                        "input_name": "Plátano maduro",
                        "matched_db_name": "Plátano maduro",
                        "total_kcal": 137.0,  # ~137 kcal per 100g
                        "notes": "Good match",
                    }
                ],
                "total_recipe_kcal": 137.0,
                "warnings": None,
            },
            ensure_ascii=False,
        ),
    },
    {
        "question": "Analiza: 200g de Pechuga de Pollo",
        "inputs": [IngredientInput(nombre="Pechuga de Pollo", peso_gramos=200)],
        "ground_truth": json.dumps(
            {
                "processed_items": [
                    {
                        "input_name": "Pechuga de Pollo",
                        "matched_db_name": "Pechuga de pollo. cocida",
                        "total_kcal": 286.0,  # ~143 kcal/100g * 2
                        "notes": "Good match",
                    }
                ],
                "total_recipe_kcal": 286.0,
                "warnings": None,
            },
            ensure_ascii=False,
        ),
    },
    {
        "question": "Analiza: 50g de Unibtainium (Elemento ficticio)",
        "inputs": [IngredientInput(nombre="Unibtainium", peso_gramos=50)],
        "ground_truth": json.dumps(
            {
                "processed_items": [
                    {
                        "input_name": "Unibtainium",
                        "matched_db_name": "MISSING",
                        "total_kcal": 0,
                        "notes": "Not found in Knowledge Base.",
                    }
                ],
                "total_recipe_kcal": 0,
                "warnings": "[Unibtainium]: Not found in Knowledge Base.",
            },
            ensure_ascii=False,
        ),
    },
    {
        "question": "Analiza: 150g de Arroz blanco cocido (sancochado)",
        "inputs": [
            IngredientInput(
                nombre="Arroz blanco cocido (sancochado)",
                peso_gramos=150,
            )
        ],
        "ground_truth": json.dumps(
            {
                "processed_items": [
                    {
                        "input_name": "Arroz blanco cocido (sancochado)",
                        "matched_db_name": "Arroz blanco cocido (sancochado)",
                        "total_kcal": 159.0,  # ~106 kcal/100g * 1.5
                        "notes": "Good match",
                    }
                ],
                "total_recipe_kcal": 159.0,
                "warnings": None,
            },
            ensure_ascii=False,
        ),
    },
]


# DATASET GENERATION


async def generate_evaluation_dataset() -> Dataset:
    """Execute the RAG tool and build evaluation dataset."""
    data_samples: dict[str, list] = {
        "question": [],
        "answer": [],
        "ground_truth": [],
        "latency_ms": [],
    }

    print("Executing calculate_recipe_nutrition tool...")

    for i, case in enumerate(test_cases):
        print(f"\n  [{i + 1}/{len(test_cases)}] {case['question']}")

        t0 = time.time()
        try:
            # Invoke the RAG tool
            result = await calculate_recipe_nutrition.ainvoke(
                {"ingredientes": case["inputs"]}
            )
            answer = json.dumps(result, ensure_ascii=False)

            # Show brief result
            if isinstance(result, dict):
                total = result.get("total_recipe_kcal", 0)
                print(f"    Result: {total:.1f} kcal total")
            else:
                print(f"    Result: {result}")

        except Exception as e:
            answer = json.dumps({"error": str(e)})
            print(f"    ERROR: {e}")

        latency_ms = round((time.time() - t0) * 1000, 1)
        print(f"    Latency: {latency_ms} ms")

        data_samples["question"].append(case["question"])
        data_samples["answer"].append(answer)
        data_samples["ground_truth"].append(case["ground_truth"])
        data_samples["latency_ms"].append(latency_ms)

    return Dataset.from_dict(data_samples)


# RAGAS EVALUATION


async def run_evaluation() -> None:
    """Run RAGAS evaluation on RAG tool results."""
    print("\n" + "=" * 70)
    print("CALCULATE_RECIPE_NUTRITION RAG EVALUATION (RAGAS)")
    print("=" * 70)

    # Generate dataset with actual tool outputs
    dataset = await generate_evaluation_dataset()

    print("\n" + "-" * 70)
    print("Running RAGAS evaluation (LLM Judge: GPT-4o)...")
    print("-" * 70)

    # Select metrics for structured output evaluation.
    # ragas>=0.0.19 requires initialised metric instances,
    #  e.g. AnswerCorrectness(), not classes.
    metrics = [AnswerCorrectness(), AnswerSimilarity()]

    # Use GPT-4o as judge for accuracy
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
    assert isinstance(results, EvaluationResult)
    df = results.to_pandas()

    # Add metadata columns for traceability
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    k_value = 5  # retriever search_kwargs k
    run_ts = datetime.now().isoformat(timespec="seconds")

    df["run_timestamp"] = run_ts
    df["embedding_model"] = embedding_model
    df["judge_model"] = "gpt-4o"
    df["k_value"] = k_value

    # Timestamped CSV under tests/evaluation/data/
    csv_dir = Path(__file__).parent / "data"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_filename = f"eval_rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = csv_dir / csv_filename
    df.to_csv(csv_path)
    print(f"\nCSV saved to: {csv_path}")
    print("\nDetailed Results by Test Case:")
    print("-" * 70)
    for idx, row in df.iterrows():
        # Results use ragas column names (user_input, not question) after column_map
        print(f"\nCase {idx + 1}: {row['user_input']}")
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
    if avg_correctness >= 0.6 and avg_similarity >= 0.6:
        print("\n[PASS] RAG tool meets quality thresholds")
    else:
        print("\n[WARN] RAG tool below quality thresholds")
        print("  Target: correctness >= 0.6, similarity >= 0.6")
        print("  Note: Some variance expected due to RAG retrieval")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
