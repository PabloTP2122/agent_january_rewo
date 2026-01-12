import operator
from typing import Annotated, Any, TypedDict

from .structured_output_meal import DietPlan


class ReWOOState(TypedDict):
    # Entrada original
    task: str
    user_profile: dict[str, Any]  # Datos para generate_nutritional_plan

    # Planificación
    plan_string: str  # El texto crudo del Planner
    steps: list[tuple]  # Pasos parseados: (desc, var, tool, input)

    # Ejecución (Worker)
    # Annotated con operator.update para que los nodos puedan
    # añadir resultados al diccionario sin sobrescribir lo anterior.
    results: Annotated[dict[str, Any], operator.update]

    # Salida Final (Solver)
    final_diet_plan: DietPlan  # El objeto Pydantic v2 final
