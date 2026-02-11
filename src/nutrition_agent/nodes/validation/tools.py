"""consolidate_shopping_list, sum_total_kcal"""

import re

from langchain_core.tools import tool

from ...models.tools import ConsolidateInput, SumTotalInput


@tool("sum_total_kcal", args_schema=SumTotalInput)  # type: ignore [misc]
def sum_total_kcal(kcals_meals: list[float]) -> str:
    """
    Sums a list of meal calories and returns the exact total.
    Use this tool ALWAYS when you need to aggregate intakes
    to get a daily total.
    """
    try:
        total = sum(kcals_meals)
        return f"{round(total, 2)} kcal"
    except Exception as e:
        return f"Error: {str(e)}. Verify the list contains only numbers."


# Ingredient parsing helpers

# Known units whitelist — prevents "ml" from being split into "m" + item "l"
_KNOWN_UNITS = r"(?:gramos|kilogramos|kilos|litros|unidades|unidad|gr|kg|ml|g|l)"

# Pattern: a number followed immediately (optionally with spaces) by a known unit
# Works anywhere in the string — handles both "200g Pollo" and "Avena 80g"
_QTY_UNIT_RE = re.compile(
    rf"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>{_KNOWN_UNITS})\b",
    re.IGNORECASE,
)

# Pattern: fraction like "1/2" followed by a known unit
_FRAC_UNIT_RE = re.compile(
    rf"(?P<num>\d+)\s*/\s*(?P<den>\d+)\s*(?P<unit>{_KNOWN_UNITS})\b",
    re.IGNORECASE,
)


def _normalize_unit(raw_unit: str, qty: float) -> tuple[float, str]:
    """Normalize unit to base (g / ml / unidad) and scale qty."""
    u = raw_unit.lower()
    if u in ("kg", "kilos", "kilogramos"):
        return qty * 1000, "g"
    if u in ("gr", "gramos"):
        return qty, "g"
    if u == "g":
        return qty, "g"
    if u in ("l", "litros"):
        return qty * 1000, "ml"
    if u == "ml":
        return qty, "ml"
    if u in ("unidad", "unidades"):
        return qty, "unidad/es"
    return qty, u


def _clean_item_name(name: str) -> str:
    """Clean up the item name after quantity extraction."""
    # Remove empty parentheses left over after extracting qty from inside parens
    name = re.sub(r"\(\s*\)", "", name)
    # Remove trailing parenthesized cooking notes like "(al grill, sin piel)"
    name = re.sub(r"\([^)]*\)\s*$", "", name)
    # Remove leading/trailing "de "
    name = re.sub(r"^\s*de\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+de\s*$", "", name, flags=re.IGNORECASE)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _parse_ingredient(raw: str) -> tuple[float, str, str]:
    """Parse an ingredient string into (qty, unit, item_name).

    Tries multiple patterns in priority order:
    1. qty + known unit anywhere in string (e.g., "Avena 80g" or "200g Pollo")
    2. Fraction + known unit (e.g., "Limón 1/2 unidad")
    3. Fallback: no quantity detected
    """
    text = raw.strip()

    # Try fraction pattern first (less common, but must be checked before int pattern
    # eats the numerator)
    frac_match = _FRAC_UNIT_RE.search(text)
    if frac_match:
        num = float(frac_match.group("num"))
        den = float(frac_match.group("den"))
        qty = num / den if den != 0 else num
        raw_unit = frac_match.group("unit")
        qty, unit = _normalize_unit(raw_unit, qty)
        item = text[: frac_match.start()] + text[frac_match.end() :]
        item = _clean_item_name(item)
        return qty, unit, item.lower()

    # Try numeric qty + known unit
    qty_match = _QTY_UNIT_RE.search(text)
    if qty_match:
        qty = float(qty_match.group("qty"))
        raw_unit = qty_match.group("unit")
        qty, unit = _normalize_unit(raw_unit, qty)
        item = text[: qty_match.start()] + text[qty_match.end() :]
        item = _clean_item_name(item)
        return qty, unit, item.lower()

    # Fallback: no parseable quantity
    return 0.0, "varios", _clean_item_name(text).lower()


def _fmt_qty(qty: float, unit: str) -> str:
    """Format quantity + unit for shopping list output."""
    num = f"{qty:g}"  # strips trailing zeros: 3.0→"3", 0.5→"0.5"
    sep = " " if len(unit) > 2 else ""  # "g"/"ml"→"", "unidad"→" "
    return f"{num}{sep}{unit}"


# Tool: consolidate_shopping_list


@tool("consolidate_shopping_list", args_schema=ConsolidateInput)  # type: ignore [misc]
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    """
    Consolidates a list of raw ingredients into a clean shopping list.

    Use this tool when you have ingredients from multiple recipes
    and need to generate a unified shopping list.
    """
    consolidated: dict[str, float] = {}

    for raw_item in ingredients_raw:
        qty, unit, item_name = _parse_ingredient(raw_item)

        if not item_name:
            item_name = raw_item.strip().lower()

        # Unique composite key: "pollo (g)" != "pollo (unidad)"
        key = f"{item_name} ({unit})"

        if unit == "varios":
            consolidated[key] = consolidated.get(key, 0.0) + 1.0
        else:
            consolidated[key] = consolidated.get(key, 0.0) + qty

    # Output generation — format: "- Item Name: 200g"
    # This format is compatible with _parse_shopping_list in validation.py
    final_list = []
    for key, total_qty in consolidated.items():
        try:
            name_part, unit_part = key.rsplit(" (", 1)
            unit_clean = unit_part.replace(")", "")

            if unit_clean == "varios":
                formatted_item = f"- {name_part.title()}"
            else:
                qty_str = _fmt_qty(total_qty, unit_clean)
                formatted_item = f"- {name_part.title()}: {qty_str}"

            final_list.append(formatted_item)
        except ValueError:
            final_list.append(f"- {key}")

    return "\n".join(sorted(final_list))
