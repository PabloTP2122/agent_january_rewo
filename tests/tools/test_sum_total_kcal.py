"""Unit tests for src/nutrition_agent/nodes/validation/tools.py sum_total_kcal tool"""

import pytest
from pydantic import ValidationError

from src.nutrition_agent.nodes.validation.tools import sum_total_kcal

# =============================================================================
# sum_total_kcal tests
# =============================================================================


def test_sum_total_kcal_basic() -> None:
    """Test basic calorie summation."""
    result = sum_total_kcal.invoke({"kcals_meals": [300.5, 500.0, 400.25]})

    assert "1200.75 kcal" in result


def test_sum_total_kcal_single_meal() -> None:
    """Test single meal summation."""
    result = sum_total_kcal.invoke({"kcals_meals": [750.0]})

    assert "750.0 kcal" in result


def test_sum_total_kcal_empty_list_raises() -> None:
    """Test empty list raises ValidationError (min_length=1)."""
    with pytest.raises(ValidationError):
        sum_total_kcal.invoke({"kcals_meals": []})
