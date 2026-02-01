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


@tool("consolidate_shopping_list", args_schema=ConsolidateInput)  # type: ignore [misc]
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    """
    Consolidates a list of raw ingredients into a clean shopping list.

    Use this tool when you have ingredients from multiple recipes
    and need to generate a unified shopping list.
    """
    consolidated: dict[str, float] = {}

    # Regex: (Quantity) (Optional unit) (Optional preposition) (Item name)
    pattern = r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)?\s*(?:de\s+)?(?P<item>.+)"

    for raw_item in ingredients_raw:
        clean_item = raw_item.strip()
        match = re.search(pattern, clean_item, re.IGNORECASE)

        if match:
            # Case 1: Successful parse
            qty = float(match.group("qty"))
            raw_unit = (match.group("unit") or "unidad").lower().strip()
            item_name = match.group("item").lower().strip()

            # Common unit normalization
            unit = raw_unit
            if raw_unit in ["kg", "kilos", "kilogramos"]:
                qty *= 1000
                unit = "g"
            elif raw_unit in ["gr", "gramos"]:
                unit = "g"
            elif raw_unit in ["l", "litros"]:
                qty *= 1000
                unit = "ml"

            # Unique composite key: "chicken (g)" != "chicken (unit)"
            key = f"{item_name} ({unit})"

            consolidated[key] = consolidated.get(key, 0.0) + qty

        else:
            # Case 2: Fallback (items without clear quantity)
            key = f"{clean_item.lower()} (varios)"
            consolidated[key] = consolidated.get(key, 0.0) + 1.0

    # Output generation
    final_list = []
    for key, total_qty in consolidated.items():
        try:
            name_part, unit_part = key.rsplit(" (", 1)
            unit_clean = unit_part.replace(")", "")

            # Smart formatting
            if unit_clean == "varios":
                formatted_item = f"- {name_part.title()}"
            else:
                formatted_item = f"- {total_qty:.0f}{unit_clean} de {name_part.title()}"

            final_list.append(formatted_item)
        except ValueError:
            final_list.append(f"- {key}")

    return "\n".join(sorted(final_list))
