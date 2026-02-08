import pytest
from pydantic import ValidationError

from src.nutrition_agent.nodes.calculation.tools import get_meal_distribution

# =============================================================================
# get_meal_distribution tests
# =============================================================================


def test_get_meal_distribution_3_meals() -> None:
    """Test 3-meal distribution (30/40/30)."""
    result = get_meal_distribution.invoke(
        {"total_calories": 2000.0, "number_of_meals": 3}
    )

    assert isinstance(result, dict)
    assert len(result) == 3
    assert "Desayuno" in result
    assert "Comida" in result
    assert "Cena" in result

    # Check percentages: 30% = 600, 40% = 800, 30% = 600
    assert result["Desayuno"] == 600.0
    assert result["Comida"] == 800.0
    # Last meal gets remainder
    total = sum(result.values())
    assert abs(total - 2000.0) < 1


def test_get_meal_distribution_1_meal_omad() -> None:
    """Test OMAD (One Meal A Day) distribution."""
    result = get_meal_distribution.invoke(
        {"total_calories": 1800.0, "number_of_meals": 1}
    )

    assert len(result) == 1
    assert "Comida Unica (OMAD)" in result
    assert result["Comida Unica (OMAD)"] == 1800.0


def test_get_meal_distribution_5_meals() -> None:
    """Test 5-meal distribution includes snacks."""
    result = get_meal_distribution.invoke(
        {"total_calories": 2500.0, "number_of_meals": 5}
    )

    assert len(result) == 5
    assert "Snack AM" in result
    assert "Snack PM" in result

    # Total should match input
    total = sum(result.values())
    assert abs(total - 2500.0) < 1


def test_get_meal_distribution_invalid_calories() -> None:
    """Test calories outside valid range raises ValidationError."""
    with pytest.raises(ValidationError):
        get_meal_distribution.invoke(
            {"total_calories": 400.0, "number_of_meals": 3}  # Below 500 minimum
        )


def test_get_meal_distribution_invalid_meals() -> None:
    """Test meals outside 1-6 range raises ValidationError."""
    with pytest.raises(ValidationError):
        get_meal_distribution.invoke(
            {"total_calories": 2000.0, "number_of_meals": 7}  # Above 6 maximum
        )
