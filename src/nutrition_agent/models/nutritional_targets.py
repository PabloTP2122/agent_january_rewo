# File: src/nutrition_agent/models/nutritional_targets.py
"""Nutritional targets model for calculated TDEE and macronutrient distribution."""

from typing import Self

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


class NutritionalTargets(BaseModel):
    """Calculated nutritional targets based on user profile.

    This model stores the output of the calculation node, which uses the
    Mifflin-St Jeor formula to compute BMR, then applies activity multipliers
    and objective adjustments to determine daily calorie and macro targets.

    All values are immutable after creation (deterministic phase).

    Units:
    - *_calories: kilocalories (kcal)
    - *_grams: grams
    - *_percentage: percentage of total calories (0-100)

    Example:
        >>> targets = NutritionalTargets(
        ...     bmr=1500.0,
        ...     tdee=2325.0,
        ...     target_calories=2000.0,
        ...     protein_grams=150.0,
        ...     protein_percentage=30.0,
        ...     carbs_grams=200.0,
        ...     carbs_percentage=40.0,
        ...     fat_grams=66.7,
        ...     fat_percentage=30.0,
        ... )
    """

    bmr: float = Field(
        ...,
        gt=400,
        lt=3500,
        description=(
            "Basal Metabolic Rate (kcal/day) calculated using "
            "Mifflin-St Jeor formula. Expected range: 400-3500 kcal."
        ),
        examples=[1500.0, 1650.0, 1800.0],
    )
    tdee: float = Field(
        ...,
        gt=700,
        lt=5500,
        description=(
            "Total Daily Energy Expenditure (kcal/day) = BMR × activity multiplier. "
            "Expected range: 700-5500 kcal."
        ),
        examples=[2100.0, 2325.0, 2550.0],
    )
    target_calories: float = Field(
        ...,
        gt=400,
        lt=6000,
        description=(
            "Adjusted calorie target for objective (kcal/day). "
            "Calculated as TDEE × objective_factor: "
            "fat_loss (×0.8), maintenance (×1.0), muscle_gain (×1.1). "
            "Expected range: 400-6000 kcal."
        ),
        examples=[1800.0, 2000.0, 2250.0],
    )
    protein_grams: float = Field(
        ...,
        ge=0,
        le=500,
        description=(
            "Daily protein target in grams. "
            "Calculated as: target_calories × protein_percentage / 4. "
            "Note: 1g protein = 4 kcal."
        ),
        examples=[100.0, 150.0, 175.0],
    )
    protein_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Protein as percentage of total daily calories (0-100%).",
        examples=[25.0, 30.0, 35.0],
    )
    carbs_grams: float = Field(
        ...,
        ge=0,
        le=800,
        description=(
            "Daily carbohydrates target in grams. "
            "Calculated as: target_calories × carbs_percentage / 4. "
            "Note: 1g carbs = 4 kcal."
        ),
        examples=[150.0, 200.0, 250.0],
    )
    carbs_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Carbohydrates as percentage of total daily calories (0-100%).",
        examples=[40.0, 45.0, 50.0],
    )
    fat_grams: float = Field(
        ...,
        ge=0,
        le=300,
        description=(
            "Daily fat target in grams. "
            "Calculated as: target_calories × fat_percentage / 9. "
            "Note: 1g fat = 9 kcal."
        ),
        examples=[50.0, 66.7, 75.0],
    )
    fat_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Fat as percentage of total daily calories (0-100%).",
        examples=[20.0, 25.0, 30.0],
    )

    @field_validator("tdee", mode="after")  # type: ignore[misc]
    @classmethod
    def validate_tdee_vs_bmr(cls, v: float, info: ValidationInfo) -> float:
        """Ensure TDEE is greater than BMR (activity multiplier effect)."""
        bmr = info.data.get("bmr")
        if bmr and v < bmr:
            raise ValueError(
                f"TDEE ({v} kcal) must be >= BMR ({bmr} kcal). "
                f"Activity multiplier should be >= 1.0."
            )
        return v

    @field_validator("target_calories", mode="after")  # type: ignore[misc]
    @classmethod
    def validate_target_calories_coherence(
        cls, v: float, info: ValidationInfo
    ) -> float:
        """Ensure target_calories is within reasonable range of TDEE."""
        tdee = info.data.get("tdee")
        if tdee:
            # Allow range: 70% to 120% of TDEE (covering all objectives)
            min_reasonable = tdee * 0.7
            max_reasonable = tdee * 1.2
            if not (min_reasonable <= v <= max_reasonable):
                raise ValueError(
                    f"target_calories ({v} kcal) should be 70-120% of "
                    f"TDEE ({tdee} kcal). Objective adjustment likely incorrect."
                )
        return v

    @model_validator(mode="after")  # type: ignore[misc]
    def validate_all_fields(self) -> Self:
        """Comprehensive cross-field validation run after all fields are set.

        Checks:
        1. Macro percentages sum to ~100%
        2. Each macro gram value aligns with its percentage and target_calories
        3. TDEE is coherent relative to BMR
        """
        # Check 1: Macro percentages sum
        total_pct = (
            self.protein_percentage + self.carbs_percentage + self.fat_percentage
        )
        if not (99 <= total_pct <= 101):
            raise ValueError(
                f"Macro percentages must sum to ~100%. "
                f"Got: protein {self.protein_percentage}% + "
                f"carbs {self.carbs_percentage}% + "
                f"fat {self.fat_percentage}% = {total_pct}%"
            )

        # Check 2: Macro grams align with percentages and calories
        def check_macro_grams(
            name: str, grams: float, pct: float, kcal_per_gram: int
        ) -> None:
            expected_grams = (self.target_calories * pct / 100) / kcal_per_gram
            tolerance = max(expected_grams * 0.02, 0.5)
            if abs(grams - expected_grams) > tolerance:
                raise ValueError(
                    f"{name}: {grams}g doesn't align with "
                    f"target_calories ({self.target_calories} kcal) "
                    f"and {pct}% percentage. Expected ~{expected_grams:.1f}g."
                )

        check_macro_grams(
            "protein_grams", self.protein_grams, self.protein_percentage, 4
        )
        check_macro_grams("carbs_grams", self.carbs_grams, self.carbs_percentage, 4)
        check_macro_grams("fat_grams", self.fat_grams, self.fat_percentage, 9)

        return self

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "bmr": 1650.0,
                "tdee": 2557.5,
                "target_calories": 2046.0,
                "protein_grams": 153.45,
                "protein_percentage": 30.0,
                "carbs_grams": 204.6,
                "carbs_percentage": 40.0,
                "fat_grams": 68.2,
                "fat_percentage": 30.0,
            }
        }
