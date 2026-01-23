# File: src/nutrition_agent/models/user_profile.py
"""User profile model for nutrition agent data collection."""

from typing import Literal

from pydantic import BaseModel, Field

from src.shared.enums import ActivityLevel, DietType, Objective


class UserProfile(BaseModel):
    """User profile data collected conversationally for nutrition planning.

    This model is used with llm.with_structured_output() in the data_collection
    node. All required fields must be extracted from conversation before
    proceeding to calculation.
    """

    age: int = Field(
        ...,
        ge=18,
        le=100,
        description="User's age in years (18-100)",
        examples=[25, 35, 45],
    )
    gender: Literal["male", "female"] = Field(
        ...,
        description="Biological gender for BMR calculation (male or female)",
        examples=["male", "female"],
    )
    weight: int = Field(
        ...,
        ge=30,
        le=300,
        description="Weight in kilograms (30-300 kg)",
        examples=[70, 80, 65],
    )
    height: int = Field(
        ...,
        ge=100,
        le=250,
        description="Height in centimeters (100-250 cm)",
        examples=[170, 180, 165],
    )
    activity_level: ActivityLevel = Field(
        ...,
        description=(
            "Physical activity level: sedentary, lightly_active, "
            "moderately_active, very_active, or extra_active"
        ),
        examples=[ActivityLevel.MODERATELY_ACTIVE, ActivityLevel.SEDENTARY],
    )
    objective: Objective = Field(
        ...,
        description="Nutrition objective: fat_loss, muscle_gain, or maintenance",
        examples=[Objective.FAT_LOSS, Objective.MUSCLE_GAIN],
    )
    diet_type: DietType = Field(
        default=DietType.NORMAL,
        description="Diet type preference: normal or keto (default: normal)",
        examples=[DietType.NORMAL, DietType.KETO],
    )
    excluded_foods: list[str] = Field(
        default_factory=list,
        description="List of foods to exclude from meal plans (allergies, preferences)",
        examples=[["gluten", "lactose"], ["mariscos", "nueces"]],
    )
    number_of_meals: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Number of meals per day (1-6, default: 3)",
        examples=[3, 4, 5],
    )
