from pydantic import BaseModel, Field

from ...shared.enums import ActivityLevel, DietType, Objective


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
    """Structure of an individual ingredient from recipe generator."""

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
        description="Definitive list of ingredients and weights from recipe_gen node.",
    )


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


class NutritionalPlanOutput(BaseModel):
    """Structured output for generate_nutritional_plan tool.

    This model ensures type safety and validation for nutritional calculations.
    All percentage fields should sum to ~100%.
    """

    bmr: float = Field(..., description="Basal Metabolic Rate (kcal/day)")
    tdee: float = Field(..., description="Total Daily Energy Expenditure (kcal/day)")
    target_calories: float = Field(
        ..., description="Adjusted calorie target for objective"
    )
    protein_grams: float = Field(..., description="Daily protein target in grams")
    protein_percentage: float = Field(..., description="Protein as % of total calories")
    carbs_grams: float = Field(..., description="Daily carbs target in grams")
    carbs_percentage: float = Field(..., description="Carbs as % of total calories")
    fat_grams: float = Field(..., description="Daily fat target in grams")
    fat_percentage: float = Field(..., description="Fat as % of total calories")
    diet_type: DietType = Field(..., description="Diet type used")
    objective: Objective = Field(..., description="Objective applied")
