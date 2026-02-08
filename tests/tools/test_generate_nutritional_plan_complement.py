import pytest
from pydantic import ValidationError

from src.nutrition_agent.nodes.calculation.tools import generate_nutritional_plan

# =============================================================================
# generate_nutritional_plan tests
#    (already covered in test_generate_nutritional_plan.py - complementary)
# =============================================================================


def test_generate_nutritional_plan_maintenance() -> None:
    """Test maintenance objective applies 1.0 multiplier (no change to TDEE)."""
    result = generate_nutritional_plan.invoke(
        {
            "age": 40,
            "gender": "male",
            "weight": 75,
            "height": 175,
            "activity_level": "sedentary",
            "objective": "maintenance",
            "diet_type": "normal",
        }
    )

    assert isinstance(result, dict)
    assert "error" not in result

    # Maintenance: target_calories == TDEE (rounded)
    expected_target = round(result["tdee"] * 1.0)
    assert abs(result["target_calories"] - expected_target) < 1


def test_generate_nutritional_plan_female_bmr() -> None:
    """Test female BMR uses correct Mifflin-St Jeor formula (-161 instead of +5)."""
    result = generate_nutritional_plan.invoke(
        {
            "age": 30,
            "gender": "female",
            "weight": 60,
            "height": 160,
            "activity_level": "sedentary",
            "objective": "maintenance",
            "diet_type": "normal",
        }
    )

    assert isinstance(result, dict)
    assert "error" not in result

    # Female BMR = 10*60 + 6.25*160 - 5*30 - 161 = 600 + 1000 - 150 - 161 = 1289
    expected_bmr = 1289.0
    assert abs(result["bmr"] - expected_bmr) < 1


def test_generate_nutritional_plan_invalid_weight() -> None:
    """Test that weight outside valid range (30-300) raises ValidationError."""
    with pytest.raises(ValidationError):
        generate_nutritional_plan.invoke(
            {
                "age": 30,
                "gender": "male",
                "weight": 10,  # Invalid: below 30
                "height": 175,
                "activity_level": "sedentary",
                "objective": "maintenance",
            }
        )
