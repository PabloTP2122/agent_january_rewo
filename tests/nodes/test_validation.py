"""Unit tests for the validation node.

Tests the deterministic validation logic (no LLM) including:
- Global calorie tolerance (±5%)
- Per-meal ingredient kcal sum vs budget from meal_distribution (±5%)
- Routing hints (selected_meal_to_change, user_feedback)
- Validation retry counter
- Meal count matching
- Edge cases (no meals, missing targets)
"""

from nutrition_agent.state import NutritionAgentState
from src.nutrition_agent.models import (
    Ingredient,
    Meal,
    MealNotice,
    NutritionalTargets,
    UserProfile,
)
from src.nutrition_agent.nodes.validation.validation import validation
from src.shared.enums import ActivityLevel, DietType, MealTime, Objective

# Fixtures


def _make_user_profile(*, number_of_meals: int = 3) -> UserProfile:
    return UserProfile(
        age=30,
        gender="male",
        weight=80,
        height=180,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        objective=Objective.MAINTENANCE,
        diet_type=DietType.NORMAL,
        number_of_meals=number_of_meals,
    )


def _make_nutritional_targets() -> NutritionalTargets:
    return NutritionalTargets(
        bmr=1500.0,
        tdee=2325.0,
        target_calories=2000.0,
        protein_grams=150.0,
        protein_percentage=30.0,
        carbs_grams=200.0,
        carbs_percentage=40.0,
        fat_grams=66.7,
        fat_percentage=30.0,
    )


def _make_meal(
    meal_time: MealTime,
    title: str,
    total_calories: float,
    *,
    ingredient_kcals: list[float] | None = None,
) -> Meal:
    """Create a Meal with ingredients whose kcals match total_calories by default."""
    if ingredient_kcals is None:
        ingredient_kcals = [total_calories]

    ingredients = [
        Ingredient(
            nombre=f"Ingrediente {i + 1}",
            cantidad_display="100g",
            peso_gramos=100.0,
            kcal=kcal,
        )
        for i, kcal in enumerate(ingredient_kcals)
    ]
    return Meal(
        meal_time=meal_time,
        title=title,
        description="Descripcion de prueba para el test de validacion",
        total_calories=total_calories,
        ingredients=ingredients,
        preparation=["Paso 1", "Paso 2"],
    )


def _base_state(
    *,
    daily_meals: list[Meal],
    meal_distribution: dict[str, float] | None = None,
    number_of_meals: int = 3,
) -> NutritionAgentState:
    """Build a minimal state dict suitable for the validation node."""
    return {
        "daily_meals": daily_meals,
        "nutritional_targets": _make_nutritional_targets(),
        "user_profile": _make_user_profile(number_of_meals=number_of_meals),
        "meal_distribution": meal_distribution,
    }


# Tests


class TestValidationPassesWithinTolerance:
    """All meals within 5% of budget → no errors, final_diet_plan built."""

    def test_exact_match(self) -> None:
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Test", 600.0),
            _make_meal(MealTime.COMIDA, "Comida Test", 800.0),
            _make_meal(MealTime.CENA, "Cena Test", 600.0),
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None
        assert result["final_diet_plan"].total_calories == 2000.0
        assert result["validation_retry_count"] == 0
        assert result["selected_meal_to_change"] is None
        assert result["user_feedback"] is None
        assert result["meal_notices"] == {}

    def test_within_tolerance(self) -> None:
        """Each meal ~4% off budget (within 5% threshold)."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Test", 624.0),  # 600 * 1.04
            _make_meal(MealTime.COMIDA, "Comida Test", 768.0),  # 800 * 0.96
            _make_meal(MealTime.CENA, "Cena Test", 576.0),  # 600 * 0.96
        ]
        # Global total: 624 + 768 + 576 = 1968, target 2000, error = 1.6% ✅
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None
        assert result["validation_retry_count"] == 0


class TestValidationCatchesPerMealBudgetViolation:
    """One meal significantly off its budget → error includes meal name and %."""

    def test_cena_14pct_off(self) -> None:
        """Real example: Cena at 516 kcal vs budget 600 = 14% error."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno OK", 600.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena Mala", 516.0),
        ]
        # Global: 600+800+516 = 1916 vs 2000 = 4.2% → passes global check
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        assert result["final_diet_plan"] is None
        errors = result["validation_errors"]
        assert len(errors) == 1
        assert "Cena Mala" in errors[0]
        assert "Cena" in errors[0]
        assert "14.0%" in errors[0]
        # Routing: single meal failed → targeted regeneration
        assert result["selected_meal_to_change"] == "Cena"
        assert "budget" in result["user_feedback"]
        assert "516.0" in result["user_feedback"]
        assert result["validation_retry_count"] == 1

    def test_no_meal_distribution_skips_check(self) -> None:
        """When meal_distribution is None, per-meal budget check is skipped."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Test", 600.0),
            _make_meal(MealTime.COMIDA, "Comida Test", 800.0),
            _make_meal(MealTime.CENA, "Cena Test", 600.0),
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution=None,
        )

        result = validation(state)

        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None


class TestValidationCatchesIngredientSumMismatch:
    """Ingredient kcals don't sum to budget → error reported."""

    def test_ingredient_sum_off(self) -> None:
        bad_meal = _make_meal(
            MealTime.CENA,
            "Cena Inconsistente",
            600.0,
            ingredient_kcals=[300.0, 100.0],  # sum = 400, budget = 600 → 33.3%
        )
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno OK", 600.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            bad_meal,
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        assert result["final_diet_plan"] is None
        errors = result["validation_errors"]
        ingredient_errors = [e for e in errors if "ingredient kcal sum" in e]
        assert len(ingredient_errors) == 1
        assert "Cena Inconsistente" in ingredient_errors[0]
        assert "400.0" in ingredient_errors[0]
        assert "budget" in ingredient_errors[0]
        assert "33.3%" in ingredient_errors[0]
        # Single meal failed → targeted regeneration
        assert result["selected_meal_to_change"] == "Cena"
        assert result["validation_retry_count"] == 1


class TestValidationNoMeals:
    """Empty daily_meals → error 'No meals to validate'."""

    def test_empty_meals(self) -> None:
        state = _base_state(daily_meals=[], number_of_meals=3)

        result = validation(state)

        assert result["final_diet_plan"] is None
        assert "No meals to validate" in result["validation_errors"]


class TestValidationMissingTargets:
    """No nutritional_targets → error 'Missing nutritional targets'."""

    def test_missing_targets(self) -> None:
        meals = [_make_meal(MealTime.DESAYUNO, "Desayuno Test", 600.0)]
        state: NutritionAgentState = {
            "daily_meals": meals,
            "nutritional_targets": None,
            "user_profile": _make_user_profile(),
            "meal_distribution": None,
        }

        result = validation(state)

        assert result["final_diet_plan"] is None
        assert "Missing nutritional targets" in result["validation_errors"]


class TestValidationMealCountMismatch:
    """2 meals but number_of_meals=3 → error reported."""

    def test_count_mismatch(self) -> None:
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Test", 600.0),
            _make_meal(MealTime.COMIDA, "Comida Test", 800.0),
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
            number_of_meals=3,
        )

        result = validation(state)

        assert result["final_diet_plan"] is None
        errors = result["validation_errors"]
        count_errors = [e for e in errors if "Expected 3 meals but got 2" in e]
        assert len(count_errors) == 1


class TestValidationMultipleMealsFailRoutesToBatch:
    """When 2+ meals fail budget check → no targeted regen (batch route)."""

    def test_two_meals_off(self) -> None:
        """Desayuno and Cena both off → selected_meal_to_change is None."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Mala", 400.0),  # vs 600
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena Mala", 400.0),  # vs 600
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={
                "Desayuno": 600.0,
                "Comida": 800.0,
                "Cena": 600.0,
            },
        )

        result = validation(state)

        assert result["final_diet_plan"] is None
        assert len(result["validation_errors"]) >= 2
        # Multiple failures → no targeted regen
        assert result["selected_meal_to_change"] is None
        assert result["user_feedback"] is None
        assert result["validation_retry_count"] == 1


class TestValidationRetryCount:
    """Retry counter increments on failure and resets on success."""

    def test_retry_count_increments(self) -> None:
        """Counter goes from 1 → 2 on second failure."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno OK", 600.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena Mala", 400.0),  # 33% off
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={
                "Desayuno": 600.0,
                "Comida": 800.0,
                "Cena": 600.0,
            },
        )
        # Simulate second attempt (retry_count already 1)
        state["validation_retry_count"] = 1

        result = validation(state)

        assert result["final_diet_plan"] is None
        assert result["validation_retry_count"] == 2

    def test_retry_count_resets_on_success(self) -> None:
        """Counter resets to 0 when validation passes."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno OK", 600.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena OK", 600.0),
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={
                "Desayuno": 600.0,
                "Comida": 800.0,
                "Cena": 600.0,
            },
        )
        # Simulate previous failure
        state["validation_retry_count"] = 2

        result = validation(state)

        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None
        assert result["validation_retry_count"] == 0


class TestMealNoticesWarning:
    """Meal 2-5% off budget → warning notice."""

    def test_warning_at_3pct(self) -> None:
        """Desayuno at 618 kcal vs budget 600 = 3% → severity='warning'."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Borderline", 618.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena OK", 600.0),
        ]
        # Global: 618+800+600 = 2018 vs 2000 = 0.9% → passes global check
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        # 3% is within tolerance → validation passes
        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None
        # But a warning notice is emitted
        notices = result["meal_notices"]
        assert "Desayuno" in notices
        notice = notices["Desayuno"]
        assert isinstance(notice, MealNotice)
        assert notice.severity == "warning"
        assert notice.deviation_pct == 3.0
        # Other meals: no notices
        assert "Comida" not in notices
        assert "Cena" not in notices


class TestMealNoticesError:
    """Meal >5% off budget → error notice."""

    def test_error_at_14pct(self) -> None:
        """Cena at 516 kcal vs budget 600 = 14% → severity='error'."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno OK", 600.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena Mala", 516.0),
        ]
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        # Validation fails
        assert result["final_diet_plan"] is None
        # Error notice emitted
        notices = result["meal_notices"]
        assert "Cena" in notices
        notice = notices["Cena"]
        assert isinstance(notice, MealNotice)
        assert notice.severity == "error"
        assert notice.deviation_pct == 14.0


class TestMealNoticesBelowThreshold:
    """Meal <2% off budget → no notice."""

    def test_no_notice_at_1pct(self) -> None:
        """Desayuno at 606 kcal vs budget 600 = 1% → no notice."""
        meals = [
            _make_meal(MealTime.DESAYUNO, "Desayuno Casi Perfecto", 606.0),
            _make_meal(MealTime.COMIDA, "Comida OK", 800.0),
            _make_meal(MealTime.CENA, "Cena OK", 600.0),
        ]
        # Global: 606+800+600 = 2006 vs 2000 = 0.3% → passes
        state = _base_state(
            daily_meals=meals,
            meal_distribution={"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0},
        )

        result = validation(state)

        assert result["validation_errors"] == []
        assert result["final_diet_plan"] is not None
        assert result["meal_notices"] == {}
