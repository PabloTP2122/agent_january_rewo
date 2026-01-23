# File: src/shared/tools.py
"""Shared nutrition tools used by all agents."""

import asyncio
import math
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel, Field

from src.shared.enums import ActivityLevel, DietType, Objective

load_dotenv()


# Base Model with strict configuration (DRY)
class StrictBaseModel(BaseModel):
    """
    Base class for all tool input schemas.

    Configuration:
    - extra="forbid": Rejects undeclared fields (anti-hallucination for LLM)
    """

    model_config = {"extra": "forbid"}


# 1. Input Schemas (Strict Validation)
class SumTotalInput(StrictBaseModel):
    """Strict input for summing calories."""

    kcals_meals: list[float] = Field(
        ...,
        description="List of caloric values for meals (e.g., [300.5, 500]).",
        min_length=1,
    )


class VerifyIngredientsInput(StrictBaseModel):
    """Strict input for mathematical audit."""

    ingredients: list[float] = Field(
        ...,
        description="List of individual calories for each ingredient.",
        min_length=1,
    )
    expected_kcal_sum: float = Field(
        ..., description="The total calorie count the agent believes is correct."
    )


class NutritionalInput(StrictBaseModel):
    """Strict input schema for the nutrition tool."""

    age: int = Field(..., ge=18, le=100, description="User age in years (18-100).")
    gender: str = Field(
        ...,
        pattern="^(male|female|masculine|feminine)$",
        description="Biological gender ('male' or 'female').",
    )
    weight: int = Field(..., ge=30, le=300, description="Body weight in Kilograms.")
    height: int = Field(..., ge=100, le=250, description="Height in Centimeters.")
    activity_level: ActivityLevel = Field(
        ..., description="User's physical activity level."
    )
    objective: Objective = Field(..., description="Current physical objective.")
    diet_type: DietType = Field(
        default=DietType.NORMAL, description="Dietary preference (Normal or Keto)."
    )


class MealDistInput(StrictBaseModel):
    """Input for meal distribution."""

    total_calories: float = Field(
        ..., gt=500, lt=10000, description="Total daily calorie target."
    )
    number_of_meals: int = Field(..., ge=1, le=6, description="Number of meals (1-6).")


class ConsolidateInput(StrictBaseModel):
    """Input for shopping list consolidation."""

    ingredients_raw: list[str] = Field(
        ...,
        description="List of ingredients (e.g., ['200g Chicken', '100g Rice']).",
    )


class IngredientInput(StrictBaseModel):
    """Structure of an individual ingredient from the Planner."""

    nombre: str = Field(
        ...,
        description="Ingredient name identified in the plan.",
    )
    peso_gramos: float = Field(
        ...,
        description="Numeric weight in grams for calculation.",
    )


class RecipeAnalysisInput(StrictBaseModel):
    """Strict input schema for the recipe analysis tool."""

    ingredientes: list[IngredientInput] = Field(
        ...,
        description="Definitive list of ingredients and weights from the Planner.",
    )


# 2. Output Models
class ProcessedItem(BaseModel):
    """Processed ingredient with nutrition data."""

    input_name: str
    matched_db_name: str
    total_kcal: float
    notes: str


class NutritionResult(BaseModel):
    """Consolidated result of recipe nutritional analysis."""

    processed_items: list[ProcessedItem]
    total_recipe_kcal: float
    warnings: str | None = Field(
        None, description="Report of search failures or inconsistencies."
    )


class NutriFacts(BaseModel):
    """Schema for nutritional data extraction via RAG."""

    food_name: str = Field(
        ...,
        description="Food name in the retrieved text.",
    )
    calories_100g: float = Field(
        ...,
        description="Calories per 100g.",
    )
    notes: str = Field(
        ...,
        description="Notes about match quality.",
    )


# 3. Business Logic (Encapsulation)
def _calculate_bmr_mifflin(weight: int, height: int, age: int, gender: str) -> float:
    """Internal deterministic BMR calculation."""
    base = (10 * weight) + (6.25 * height) - (5 * age)
    return base + 5 if gender.lower() in ["male", "masculine"] else base - 161


def _get_activity_multiplier(level: ActivityLevel) -> float:
    """Get TDEE multiplier for activity level."""
    mapping = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHTLY_ACTIVE: 1.375,
        ActivityLevel.MODERATELY_ACTIVE: 1.55,
        ActivityLevel.VERY_ACTIVE: 1.725,
        ActivityLevel.EXTRA_ACTIVE: 1.9,
    }
    return mapping[level]


# 4. ResourceLoader for RAG
class ResourceLoader:
    """
    Singleton for managing connections.
    Centralizes configuration validation.
    """

    _retriever = None
    _extractor_llm = None

    @staticmethod
    def _validate_env_vars() -> None:
        """Validates critical credentials exist before connecting."""
        required_vars = ["PINECONE_API_KEY", "OPENAI_API_KEY", "PINECONE_INDEX_NAME"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ConnectionError(
                f"""Missing configuration in Worker environment:
                 {", ".join(missing)}. """
                "Ensure environment variables are loaded."
            )

    @classmethod
    def get_retriever(cls) -> Any:
        """Get or create Pinecone retriever singleton."""
        if cls._retriever is None:
            # 1. Validate before connecting
            cls._validate_env_vars()

            # 2. Get config from environment
            index_name = os.getenv("PINECONE_INDEX_NAME", "")
            embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

            try:
                embeddings = OpenAIEmbeddings(model=embedding_model)

                vector_store = PineconeVectorStore.from_existing_index(
                    index_name=index_name, embedding=embeddings
                )
                cls._retriever = vector_store.as_retriever(search_kwargs={"k": 1})

            except Exception as e:
                raise ConnectionError(  # noqa: B904
                    f"Error initializing Pinecone connection: {str(e)}"
                )

        return cls._retriever

    @classmethod
    def get_extractor_chain(cls) -> RunnableSerializable[dict, Any]:
        """Get or create extraction chain singleton."""
        if cls._extractor_llm is None:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            prompt = ChatPromptTemplate.from_template(
                """Analyze the context. Extract data for: '{ingredient_name}'.
                Context: {context}
                If no match, return 0 and explain in notes."""
            )
            cls._extractor_llm = prompt | llm.with_structured_output(NutriFacts)
        return cls._extractor_llm


# 5. Tool Definitions
@tool("generate_nutritional_plan", args_schema=NutritionalInput)  # type: ignore [misc]
def generate_nutritional_plan(
    age: int,
    gender: str,
    weight: int,
    height: int,
    activity_level: ActivityLevel,
    objective: Objective,
    diet_type: DietType = DietType.NORMAL,
) -> str:
    """
    Calculates daily caloric needs and macronutrient distribution.

    Use this tool when the user provides their physical data
    and wants a diet plan or to know how many calories to consume.
    DO NOT use if data like weight or height is missing.
    """
    try:
        # 1. "Hands": Pure mathematical calculations
        bmr = _calculate_bmr_mifflin(weight, height, age, gender)
        tdee = bmr * _get_activity_multiplier(activity_level)

        # Objective adjustment mapping (hidden from LLM)
        objective_adjustments = {
            Objective.FAT_LOSS: 0.83,
            Objective.MUSCLE_GAIN: 1.15,
            Objective.MAINTENANCE: 1.0,
        }

        target_calories = round(tdee * objective_adjustments[objective])

        # Macro logic
        if diet_type == DietType.KETO:
            p_grams = int((target_calories * 0.25) / 4)
            f_grams = int((target_calories * 0.70) / 9)
            c_grams = int((target_calories * 0.05) / 4)
        else:
            # Normal logic: Protein indexed to weight, rest adjusts
            p_mult = (
                2.2 if objective in [Objective.FAT_LOSS, Objective.MUSCLE_GAIN] else 1.6
            )
            p_grams = int(weight * p_mult)
            f_grams = int(weight * 0.9)  # 0.9g/kg fat base

            remaining_cals = target_calories - (p_grams * 4) - (f_grams * 9)
            c_grams = max(0, int(remaining_cals / 4))

        # 2. Concise, token-efficient response
        objective_label = objective.value.replace("_", " ").title()
        return (
            f"TDEE: {int(tdee)} kcal | Target: {target_calories} kcal\n"
            f"Protein: {p_grams}g | Fat: {f_grams}g | Carbs: {c_grams}g\n"
            f"Goal: {objective_label} ({diet_type.value.title()})"
        )

    except Exception as e:
        # 3. Instructive error message
        return (
            f"Calculation error: {str(e)}. "
            "Verify that numeric data (weight/height) is logical."
        )


@tool("sum_total_kcal", args_schema=SumTotalInput)  # type: ignore [misc]
def sum_total_kcal(kcals_meals: list[float]) -> str:
    """
    Sums a list of meal calories and returns the exact total.
    Use this tool ALWAYS when you need to aggregate intakes
    to get a daily total.
    """
    try:
        total = sum(kcals_meals)
        return f"{round(total, 2)} kcal"
    except Exception as e:
        return f"Error: {str(e)}. Verify the list contains only numbers."


@tool("sum_ingredients_kcal", args_schema=VerifyIngredientsInput)  # type: ignore [misc]
def sum_ingredients_kcal(ingredients: list[float], expected_kcal_sum: float) -> str:
    """
    Verifies if ingredient sum matches expected total.

    If discrepancy found, returns the REAL value for immediate correction.
    """
    try:
        # 1. The Mathematical Truth
        calculated_sum = sum(ingredients)

        # 2. Anti-obsessive tolerance (0.5 kcal)
        if math.isclose(calculated_sum, expected_kcal_sum, abs_tol=0.5):
            return "Verification successful: ingredient sum matches total."

        # 3. Prescriptive correction protocol (anti-loop)
        real_total = round(calculated_sum, 2)
        diff = round(real_total - expected_kcal_sum, 2)

        return (
            f"Correction required: real sum is {real_total} kcal "
            f"(difference: {diff} kcal). "
            f"Use {real_total} kcal in your final response."
        )

    except Exception as e:
        return f"Technical error: {str(e)}"


@tool("get_meal_distribution", args_schema=MealDistInput)  # type: ignore [misc]
def get_meal_distribution(
    total_calories: float, number_of_meals: int
) -> dict[str, float]:
    """
    Calculates exact caloric distribution per meal.

    Use this tool to know how many calories to assign to Breakfast,
    Lunch, Dinner, etc. based on the user's eating frequency.
    """
    # 1. Distribution patterns (percentages)
    distributions = {
        1: {"Comida Unica (OMAD)": 1.0},
        2: {"Brunch": 0.5, "Cena": 0.5},
        3: {"Desayuno": 0.3, "Comida": 0.4, "Cena": 0.3},
        4: {"Desayuno": 0.25, "Comida": 0.35, "Snack PM": 0.15, "Cena": 0.25},
        5: {
            "Desayuno": 0.25,
            "Snack AM": 0.10,
            "Comida": 0.35,
            "Snack PM": 0.10,
            "Cena": 0.20,
        },
        6: {
            "Desayuno": 0.20,
            "Snack AM": 0.10,
            "Comida": 0.30,
            "Snack PM": 0.10,
            "Cena": 0.20,
            "Recena": 0.10,
        },
    }

    # 2. Strategy selection
    selected_dist = distributions.get(number_of_meals, distributions[6])

    # 3. Calorie calculation
    result = {}
    accumulated = 0

    keys = list(selected_dist.keys())

    for i, meal_name in enumerate(keys):
        percentage = selected_dist[meal_name]

        # Last meal gets remainder to handle decimals
        if i == len(keys) - 1:
            kcal_val = total_calories - accumulated
        else:
            kcal_val = round(total_calories * percentage)
            accumulated += kcal_val

        result[meal_name] = round(kcal_val, 1)

    return result


@tool("consolidate_shopping_list", args_schema=ConsolidateInput)  # type: ignore [misc]
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    """
    Consolidates a list of raw ingredients into a clean shopping list.

    Use this tool when you have ingredients from multiple recipes
    and need to generate a unified shopping list.
    """
    consolidated: dict[str, float] = {}

    # Regex: (Quantity) (Optional unit) (Optional preposition) (Item name)
    pattern = r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)?\s*(?:de\s+)?(?P<item>.+)"

    for raw_item in ingredients_raw:
        clean_item = raw_item.strip()
        match = re.search(pattern, clean_item, re.IGNORECASE)

        if match:
            # Case 1: Successful parse
            qty = float(match.group("qty"))
            raw_unit = (match.group("unit") or "unidad").lower().strip()
            item_name = match.group("item").lower().strip()

            # Common unit normalization
            unit = raw_unit
            if raw_unit in ["kg", "kilos", "kilogramos"]:
                qty *= 1000
                unit = "g"
            elif raw_unit in ["gr", "gramos"]:
                unit = "g"
            elif raw_unit in ["l", "litros"]:
                qty *= 1000
                unit = "ml"

            # Unique composite key: "chicken (g)" != "chicken (unit)"
            key = f"{item_name} ({unit})"

            consolidated[key] = consolidated.get(key, 0.0) + qty

        else:
            # Case 2: Fallback (items without clear quantity)
            key = f"{clean_item.lower()} (varios)"
            consolidated[key] = consolidated.get(key, 0.0) + 1.0

    # Output generation
    final_list = []
    for key, total_qty in consolidated.items():
        try:
            name_part, unit_part = key.rsplit(" (", 1)
            unit_clean = unit_part.replace(")", "")

            # Smart formatting
            if unit_clean == "varios":
                formatted_item = f"- {name_part.title()}"
            else:
                formatted_item = f"- {total_qty:.0f}{unit_clean} de {name_part.title()}"

            final_list.append(formatted_item)
        except ValueError:
            final_list.append(f"- {key}")

    return "\n".join(sorted(final_list))


async def _process_ingredient_task(ing: IngredientInput) -> ProcessedItem:
    """Atomic work unit for an ingredient."""
    try:
        retriever = ResourceLoader.get_retriever()
        extractor = ResourceLoader.get_extractor_chain()

        # 1. Retrieval
        docs = await retriever.ainvoke(ing.nombre)

        if not docs:
            return ProcessedItem(
                input_name=ing.nombre,
                matched_db_name="MISSING",
                total_kcal=0,
                notes="Not found in Knowledge Base.",
            )

        # 2. Extraction
        raw_data = await extractor.ainvoke(
            {"ingredient_name": ing.nombre, "context": docs[0].page_content}
        )

        # 3. Calculation
        factor = ing.peso_gramos / 100.0
        return ProcessedItem(
            input_name=ing.nombre,
            matched_db_name=raw_data.food_name,
            total_kcal=round(raw_data.calories_100g * factor, 1),
            notes=raw_data.notes,
        )

    except Exception as e:
        return ProcessedItem(
            input_name=ing.nombre,
            matched_db_name="ERROR",
            total_kcal=0,
            notes=f"Internal exception: {str(e)}",
        )


@tool("calculate_recipe_nutrition", args_schema=RecipeAnalysisInput)  # type: ignore [misc]
async def calculate_recipe_nutrition(
    ingredientes: list[IngredientInput], _config: RunnableConfig | None = None
) -> Any:
    """
    Queries the knowledge base (RAG) to obtain precise
    and consolidated nutritional values.

    Use this tool when you have the definitive list of ingredients
    and their weights from the plan.
    Performs vector search, scales values to the indicated weight,
    and reports substitutions or warnings if there's no exact match.
    """
    # Fail-fast if infrastructure doesn't respond
    try:
        ResourceLoader.get_retriever()
    except ConnectionError as e:
        return {"system_error": str(e), "status": "failed"}

    # Parallel execution (Worker behavior)
    tasks = [_process_ingredient_task(ing) for ing in ingredientes]
    results = await asyncio.gather(*tasks)

    # Result consolidation
    clean_items = []
    total_kcal = 0.0
    warnings = []

    for item in results:
        clean_items.append(item)
        total_kcal += item.total_kcal

        if item.matched_db_name in ["MISSING", "ERROR"]:
            warnings.append(f"[{item.input_name}]: {item.notes}")

    output = NutritionResult(
        processed_items=clean_items,
        total_recipe_kcal=round(total_kcal, 1),
        warnings=" | ".join(warnings) if warnings else None,
    )

    return output.model_dump()


# Export all tools as a list
tools = [
    generate_nutritional_plan,
    sum_total_kcal,
    sum_ingredients_kcal,
    get_meal_distribution,
    consolidate_shopping_list,
    calculate_recipe_nutrition,
]
