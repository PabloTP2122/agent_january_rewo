"""TDD for tests.tool.generate_nutritional_plan."""

import pytest
from pydantic import ValidationError

from src.shared import generate_nutritional_plan


# 1. Test de Lógica Matemática (Happy Path)
def test_muscle_gain_calculation() -> None:
    """Test muscle gain calculation returns correct structured data."""
    result = generate_nutritional_plan.invoke(
        {
            "age": 25,
            "gender": "male",
            "weight": 80,
            "height": 180,
            "activity_level": "very_active",
            "objective": "muscle_gain",
            "diet_type": "normal",
        }
    )

    # Now returns dict instead of string
    assert isinstance(result, dict)  # noqa: S101
    assert "error" not in result  # noqa: S101

    # Verify expected keys exist
    assert "bmr" in result  # noqa: S101
    assert "tdee" in result  # noqa: S101
    assert "target_calories" in result  # noqa: S101
    assert "protein_grams" in result  # noqa: S101
    assert "protein_percentage" in result  # noqa: S101
    assert "carbs_grams" in result  # noqa: S101
    assert "carbs_percentage" in result  # noqa: S101
    assert "fat_grams" in result  # noqa: S101
    assert "fat_percentage" in result  # noqa: S101

    # Verify protein calculation: 80kg * 2.2 = 176g
    assert result["protein_grams"] == 176.0  # noqa: S101

    # Verify objective is preserved
    assert result["objective"] == "muscle_gain"  # noqa: S101


def test_fat_loss_calculation() -> None:
    """Test fat loss calculation applies 0.83 multiplier correctly."""
    result = generate_nutritional_plan.invoke(
        {
            "age": 30,
            "gender": "female",
            "weight": 70,
            "height": 165,
            "activity_level": "moderately_active",
            "objective": "fat_loss",
            "diet_type": "normal",
        }
    )

    assert isinstance(result, dict)  # noqa: S101
    assert "error" not in result  # noqa: S101

    # Verify deficit is applied (target < TDEE)
    assert result["target_calories"] < result["tdee"]  # noqa: S101

    # TDEE * 0.83 = target_calories
    expected_target = round(result["tdee"] * 0.83)
    assert abs(result["target_calories"] - expected_target) < 1  # noqa: S101


def test_keto_diet_macros() -> None:
    """Test keto diet returns 25/5/70 macro percentages."""
    result = generate_nutritional_plan.invoke(
        {
            "age": 35,
            "gender": "male",
            "weight": 85,
            "height": 175,
            "activity_level": "lightly_active",
            "objective": "maintenance",
            "diet_type": "keto",
        }
    )

    assert isinstance(result, dict)  # noqa: S101
    assert "error" not in result  # noqa: S101

    # Keto fixed percentages
    assert result["protein_percentage"] == 25.0  # noqa: S101
    assert result["carbs_percentage"] == 5.0  # noqa: S101
    assert result["fat_percentage"] == 70.0  # noqa: S101
    assert result["diet_type"] == "keto"  # noqa: S101


# 2. Test de Validación de Tipos (Guardrails)
def test_invalid_enum_raises_error() -> None:
    """Si el LLM alucina un objetivo, la tool debe fallar ANTES de ejecutar lógica."""
    with pytest.raises(ValidationError):
        generate_nutritional_plan.invoke(
            {
                "age": 30,
                "gender": "male",
                "weight": 75,
                "height": 180,
                "activity_level": "sedentary",
                "objective": "QUIERO_PONERME_CUADRADO",  # <--- Valor inválido
            }
        )


# 3. Test de Límites (Edge Cases)
def test_edge_case_negative_carbs() -> None:
    """
    Caso extremo: Alta proteína y grasa pueden consumir todas las calorías.
    Verifica que carbs no sea negativo (max(0, ...)).
    """
    result = generate_nutritional_plan.invoke(
        {
            "age": 25,
            "gender": "male",
            "weight": 120,  # Very heavy - high protein needs
            "height": 165,  # Short - lower TDEE
            "activity_level": "sedentary",  # Low activity
            "objective": "fat_loss",  # Deficit applied
            "diet_type": "normal",
        }
    )

    assert isinstance(result, dict)  # noqa: S101
    assert "error" not in result  # noqa: S101

    # Carbs should never be negative
    assert result["carbs_grams"] >= 0  # noqa: S101
