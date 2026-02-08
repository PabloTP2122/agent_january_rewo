"""Unit tests for src/shared/tools.py sum_ingredients_kcal tool
For every meal verification.
"""

from src.shared import sum_ingredients_kcal

# sum_ingredients_kcal tests


def test_sum_ingredients_kcal_match() -> None:
    """Test verification passes when sum matches expected."""
    result = sum_ingredients_kcal.invoke(
        {
            "ingredients": [100.0, 150.0, 250.0],
            "expected_kcal_sum": 500.0,
        }
    )

    assert "successful" in result.lower()


def test_sum_ingredients_kcal_tolerance() -> None:
    """Test 0.5 kcal tolerance is applied correctly."""
    result = sum_ingredients_kcal.invoke(
        {
            "ingredients": [100.0, 150.0, 250.0],
            "expected_kcal_sum": 500.4,  # Within 0.5 kcal tolerance
        }
    )

    assert "successful" in result.lower()


def test_sum_ingredients_kcal_mismatch() -> None:
    """Test correction is provided when sum doesn't match."""
    result = sum_ingredients_kcal.invoke(
        {
            "ingredients": [100.0, 150.0, 250.0],
            "expected_kcal_sum": 600.0,  # Wrong expectation
        }
    )

    assert "correction" in result.lower()
    assert "500" in result  # Real sum is 500
