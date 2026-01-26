"""Smoke test for the calculation node.

This standalone script tests the calculation node with a mock state
to verify it produces correct NutritionalTargets and meal distribution.

Run: python tests/quick_tool_tests/test_calculation_node.py
"""

import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from src.nutrition_agent.models import NutritionalTargets, UserProfile  # noqa: E402
from src.nutrition_agent.nodes.calculation import calculation  # noqa: E402
from src.shared.enums import ActivityLevel, DietType, Objective  # noqa: E402


def create_mock_state(user_profile: UserProfile) -> dict[str, Any]:
    """Create a mock state dict that mimics NutritionAgentState behavior."""
    return {
        "user_profile": user_profile,
        "messages": [],
        "missing_fields": [],
        "nutritional_targets": None,
        "meal_distribution": None,
        "daily_meals": [],
        "meal_generation_errors": {},
        "review_decision": None,
        "user_feedback": None,
        "selected_meal_to_change": None,
        "validation_errors": [],
        "final_diet_plan": None,
    }


def test_calculation_muscle_gain() -> None:
    """Test calculation node for muscle gain objective."""
    print("\n" + "=" * 60)
    print("TEST 1: Muscle Gain - Male, 80kg, 180cm, Very Active")
    print("=" * 60)

    profile = UserProfile(
        age=25,
        gender="male",
        weight=80,
        height=180,
        activity_level=ActivityLevel.VERY_ACTIVE,
        objective=Objective.MUSCLE_GAIN,
        diet_type=DietType.NORMAL,
        excluded_foods=[],
        number_of_meals=3,
    )

    state = create_mock_state(profile)
    result = calculation(state)  # type: ignore[arg-type]

    # Validate output structure
    assert "nutritional_targets" in result  # noqa: S101
    assert "meal_distribution" in result  # noqa: S101

    targets: NutritionalTargets = result["nutritional_targets"]
    distribution: dict[str, float] = result["meal_distribution"]

    print("\nNutritional Targets:")
    print(f"  BMR: {targets.bmr:.1f} kcal")
    print(f"  TDEE: {targets.tdee:.1f} kcal")
    print(f"  Target Calories: {targets.target_calories:.1f} kcal (surplus)")
    prot = f"{targets.protein_grams:.1f}g ({targets.protein_percentage:.1f}%)"
    print(f"  Protein: {prot}")
    print(f"  Carbs: {targets.carbs_grams:.1f}g ({targets.carbs_percentage:.1f}%)")
    print(f"  Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage:.1f}%)")

    print("\nMeal Distribution:")
    for meal_name, calories in distribution.items():
        print(f"  {meal_name}: {calories:.1f} kcal")

    # Assertions
    assert targets.target_calories > targets.tdee  # noqa: S101
    assert targets.protein_grams == 176.0  # noqa: S101
    assert len(distribution) == 3  # noqa: S101

    total_dist = sum(distribution.values())
    assert abs(total_dist - targets.target_calories) < 1  # noqa: S101

    print("\n[OK] Test passed!")


def test_calculation_fat_loss() -> None:
    """Test calculation node for fat loss objective."""
    print("\n" + "=" * 60)
    print("TEST 2: Fat Loss - Female, 70kg, 165cm, Moderately Active")
    print("=" * 60)

    profile = UserProfile(
        age=30,
        gender="female",
        weight=70,
        height=165,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        objective=Objective.FAT_LOSS,
        diet_type=DietType.NORMAL,
        excluded_foods=["mariscos"],
        number_of_meals=4,
    )

    state = create_mock_state(profile)
    result = calculation(state)  # type: ignore[arg-type]

    targets: NutritionalTargets = result["nutritional_targets"]
    distribution: dict[str, float] = result["meal_distribution"]

    print("\nNutritional Targets:")
    print(f"  BMR: {targets.bmr:.1f} kcal")
    print(f"  TDEE: {targets.tdee:.1f} kcal")
    print(f"  Target Calories: {targets.target_calories:.1f} kcal (deficit)")
    print(
        f"  Protein: {targets.protein_grams:.1f}g ({targets.protein_percentage:.1f}%)"
    )
    print(f"  Carbs: {targets.carbs_grams:.1f}g ({targets.carbs_percentage:.1f}%)")
    print(f"  Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage:.1f}%)")

    print("\nMeal Distribution (4 meals):")
    for meal_name, calories in distribution.items():
        print(f"  {meal_name}: {calories:.1f} kcal")

    # Assertions
    assert targets.target_calories < targets.tdee  # noqa: S101
    assert len(distribution) == 4  # noqa: S101
    assert "Snack PM" in distribution  # noqa: S101

    print("\n[OK] Test passed!")


def test_calculation_keto() -> None:
    """Test calculation node for keto diet."""
    print("\n" + "=" * 60)
    print("TEST 3: Keto Diet - Male, 85kg, 175cm, Lightly Active")
    print("=" * 60)

    profile = UserProfile(
        age=35,
        gender="male",
        weight=85,
        height=175,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        objective=Objective.MAINTENANCE,
        diet_type=DietType.KETO,
        excluded_foods=[],
        number_of_meals=2,
    )

    state = create_mock_state(profile)
    result = calculation(state)  # type: ignore[arg-type]

    targets: NutritionalTargets = result["nutritional_targets"]
    distribution: dict[str, float] = result["meal_distribution"]

    print("\nNutritional Targets (Keto 25/5/70):")
    print(f"  BMR: {targets.bmr:.1f} kcal")
    print(f"  TDEE: {targets.tdee:.1f} kcal")
    print(f"  Target Calories: {targets.target_calories:.1f} kcal")
    print(
        f"  Protein: {targets.protein_grams:.1f}g ({targets.protein_percentage:.1f}%)"
    )
    print(f"  Carbs: {targets.carbs_grams:.1f}g ({targets.carbs_percentage:.1f}%)")
    print(f"  Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage:.1f}%)")

    print("\nMeal Distribution (2 meals):")
    for meal_name, calories in distribution.items():
        print(f"  {meal_name}: {calories:.1f} kcal")

    # Keto macro assertions
    assert targets.protein_percentage == 25.0  # noqa: S101
    assert targets.carbs_percentage == 5.0  # noqa: S101
    assert targets.fat_percentage == 70.0  # noqa: S101
    assert len(distribution) == 2  # noqa: S101

    print("\n[OK] Test passed!")


def test_calculation_missing_profile() -> None:
    """Test calculation node raises error when user_profile is missing."""
    print("\n" + "=" * 60)
    print("TEST 4: Error Handling - Missing User Profile")
    print("=" * 60)

    state: dict[str, None] = {"user_profile": None}

    try:
        calculation(state)  # type: ignore[arg-type]
        print("\n[FAIL] Expected ValueError but none was raised!")
        assert False  # noqa: S101, B011
    except ValueError as e:
        print(f"\nExpected error raised: {e}")
        assert "user_profile is required" in str(e)  # noqa: S101
        print("\n[OK] Test passed!")


def run_all_tests() -> None:
    """Run all smoke tests."""
    print("\n" + "#" * 70)
    print("# CALCULATION NODE SMOKE TESTS")
    print("#" * 70)

    tests = [
        test_calculation_muscle_gain,
        test_calculation_fat_loss,
        test_calculation_keto,
        test_calculation_missing_profile,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
