"""Unit tests for src/shared/tools.py - All 6 migrated tools."""

from typing import Any

import pytest
from pydantic import ValidationError

from src.shared import (
    consolidate_shopping_list,
    generate_nutritional_plan,
    get_meal_distribution,
    sum_ingredients_kcal,
    sum_total_kcal,
)

# =============================================================================
# 1. generate_nutritional_plan tests
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


# =============================================================================
# 2. sum_total_kcal tests
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


# =============================================================================
# 3. sum_ingredients_kcal tests
# =============================================================================


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


# =============================================================================
# 4. get_meal_distribution tests
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


# =============================================================================
# 5. consolidate_shopping_list tests
# =============================================================================


def test_consolidate_shopping_list_basic() -> None:
    """Test basic consolidation of ingredients."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["200g Pollo", "100g Arroz", "50g Aguacate"]}
    )

    assert isinstance(result, str)
    assert "pollo" in result.lower()
    assert "arroz" in result.lower()
    assert "aguacate" in result.lower()


def test_consolidate_shopping_list_duplicates() -> None:
    """Test duplicate ingredients are summed."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["100g Pollo", "150g Pollo", "200g Arroz"]}
    )

    # Pollo should be consolidated to 250g
    assert "250g" in result or "250" in result


def test_consolidate_shopping_list_unit_normalization() -> None:
    """Test kg is converted to grams."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["1kg Pollo", "500g Pollo"]}
    )

    # 1kg + 500g = 1500g
    assert "1500" in result


def test_consolidate_shopping_list_liter_normalization() -> None:
    """Test liters are converted to ml."""
    result = consolidate_shopping_list.invoke({"ingredients_raw": ["1l Leche"]})

    # 1l = 1000ml
    assert "1000" in result and "ml" in result


def test_consolidate_shopping_list_no_quantity() -> None:
    """Test items without clear quantity are handled gracefully."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["Sal al gusto", "100g Arroz"]}
    )

    # Both items should appear
    assert "sal" in result.lower()
    assert "arroz" in result.lower()


# =============================================================================
# 6. calculate_recipe_nutrition tests (async - requires API keys)
#    These are smoke tests that require PINECONE_API_KEY and OPENAI_API_KEY
#    Skipped if environment variables are not set
# =============================================================================


def test_calculate_recipe_nutrition_missing_env() -> None:
    """Test that missing env vars return appropriate error."""
    import asyncio
    import os

    from src.shared import calculate_recipe_nutrition
    from src.shared.tools import ResourceLoader

    # Reset singleton to force re-initialization
    ResourceLoader._retriever = None
    ResourceLoader._extractor_llm = None

    # Temporarily remove env vars if they exist
    original_pinecone = os.environ.pop("PINECONE_API_KEY", None)
    original_openai = os.environ.pop("OPENAI_API_KEY", None)

    async def _run_test() -> dict[str, Any]:
        result = await calculate_recipe_nutrition.ainvoke(
            {"ingredientes": [{"nombre": "Pollo", "peso_gramos": 100}]}
        )
        return result  # type: ignore[no-any-return]

    try:
        result = asyncio.run(_run_test())

        # Should return error dict when env vars missing
        assert isinstance(result, dict)
        assert "system_error" in result or "error" in str(result).lower()
    finally:
        # Restore env vars
        if original_pinecone:
            os.environ["PINECONE_API_KEY"] = original_pinecone
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai
        # Reset singleton again
        ResourceLoader._retriever = None
        ResourceLoader._extractor_llm = None
