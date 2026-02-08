"""Unit tests for src/nutrition_agent/nodes/validation/tools.py
consolidate_shopping_list tool."""

from src.nutrition_agent.nodes.validation.tools import consolidate_shopping_list

# =============================================================================
# consolidate_shopping_list tests — existing
# =============================================================================


def test_consolidate_shopping_list_basic() -> None:
    """Test basic consolidation of ingredients (qty-first format)."""
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
    assert "250" in result


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
# New tests — real-world formats
# =============================================================================


def test_consolidate_real_llm_output() -> None:
    """Regression test with actual LLM-generated ingredients."""
    result = consolidate_shopping_list.invoke(
        {
            "ingredients_raw": [
                "Leche desnatada 300ml",
                "Avena 80g",
                "Banana madura 100g",
                "Mantequilla de almendra 20g",
                "Proteína en polvo (whey) 30g",
                "Miel 15g",
                "Pechuga de pollo 200g",
                "Quinoa 120g",
                "Brócoli 100g",
                "Espinaca fresca 50g",
                "Aceite de oliva 15ml",
                "Ajo 10g",
                "Cebolla 50g",
                "Pimienta y sal al gusto",
                "Jugo de limón 15ml",
                "Pechuga de pollo 150g (brasa o al grill, sin piel)",
                "Arroz integral cocido 150g",
                "Brócoli al vapor 100g",
                "Zanahorias al vapor 75g",
                "Aceite de oliva 10ml",
                "Sal y pimienta al gusto",
                "Limón 1/2 unidad",
            ]
        }
    )

    lower = result.lower()

    # Pechuga de pollo: 200g + 150g = 350g
    assert "pechuga de pollo" in lower
    assert "350" in result

    # Brócoli: 100g + 100g = 200g (names differ slightly but both contain "brócoli")
    # Note: "Brócoli" and "Brócoli al vapor" may remain separate due to different names
    assert "bróco" in lower or "broco" in lower

    # Aceite de oliva: 15ml + 10ml = 25ml
    assert "aceite de oliva" in lower
    assert "25" in result

    # Items without quantity should still appear
    assert "pimienta" in lower or "sal" in lower

    # Must NOT have the old broken output
    assert "1100" not in result  # No phantom "G" item
    assert "340m" not in result  # No broken "L" item


def test_item_first_format() -> None:
    """Test item-first format: 'Avena 80g'."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["Avena 80g", "Quinoa 120g"]}
    )

    lower = result.lower()
    assert "avena" in lower
    assert "80" in result
    assert "quinoa" in lower
    assert "120" in result


def test_parenthesized_weight() -> None:
    """Test parenthesized weight: 'Espinaca (100g)'."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["Espinaca (100g)", "Tomate (200g)"]}
    )

    lower = result.lower()
    assert "espinaca" in lower
    assert "100" in result
    assert "tomate" in lower
    assert "200" in result


def test_item_with_parenthesized_notes_and_weight() -> None:
    """Test: 'Proteína en polvo (whey) 30g' — parens are notes, not weight."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["Proteína en polvo (whey) 30g"]}
    )

    lower = result.lower()
    assert "prote" in lower
    assert "30" in result
    # The item name should not be empty or just "g"
    assert lower.count("- ") >= 1  # At least one item line


def test_fraction_quantity() -> None:
    """Test fraction handling: 'Limón 1/2 unidad'."""
    result = consolidate_shopping_list.invoke({"ingredients_raw": ["Limón 1/2 unidad"]})

    lower = result.lower()
    assert "lim" in lower  # limón / limon
    # Fraction should not cause a crash; item should appear


def test_mixed_format_duplicates() -> None:
    """Test consolidation across qty-first and item-first formats."""
    result = consolidate_shopping_list.invoke(
        {
            "ingredients_raw": [
                "200g Pollo",  # qty-first
                "Pollo 150g",  # item-first
            ]
        }
    )

    lower = result.lower()
    assert "pollo" in lower
    # 200 + 150 = 350
    assert "350" in result


def test_count_with_parenthesized_weight() -> None:
    """Test: '3 huevos enteros (150g)' — leading count + parens weight."""
    result = consolidate_shopping_list.invoke(
        {"ingredients_raw": ["3 huevos enteros (150g)"]}
    )

    lower = result.lower()
    assert "huevos" in lower
    assert "150" in result


def test_output_uses_colon_format() -> None:
    """Verify output format is '- Item: 200g' for _parse_shopping_list compat."""
    result = consolidate_shopping_list.invoke({"ingredients_raw": ["200g Pollo"]})

    # Should contain ": " separator for items with quantities
    assert ": " in result
    # Format: "- Pollo: 200g"
    assert "pollo" in result.lower()
    assert "200g" in result
