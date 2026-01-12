"""Tools executed by worker according with plan and #E's.
TODO: revisar DRY con claude code.

"""

import math
import os
import re
from enum import StrEnum
from typing import Any, cast

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv()

# TODO: agregar también API de Pinecone. Evaluar si muevo esta parte a
# una función u otro archivo.

VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
if not VECTOR_STORE_ID:
    raise ValueError("VECTOR_STORE_ID no encontrado en el archivo .env")


#  1. Definición de Enums (Guardrails Anti-Alucinación)
class ActivityLevel(StrEnum):
    """Niveles de actividad estandarizados para evitar ambigüedad."""

    SEDENTARY = "sedentary"  # Poco o nada de ejercicio
    LIGHTLY_ACTIVE = "lightly_active"  # Ejercicio ligero 1-3 días
    MODERATELY_ACTIVE = "moderately_active"  # Ejercicio moderado 3-5 días
    VERY_ACTIVE = "very_active"  # Ejercicio fuerte 6-7 días
    EXTRA_ACTIVE = "extra_active"  # Trabajo físico + entrenamiento


class Objective(StrEnum):
    """Objetivos claros para guiar el cálculo calórico."""

    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class DietType(StrEnum):
    """Tipos de dieta soportados."""

    NORMAL = "normal"
    KETO = "keto"


# --- 1. Schemas de Entrada (Strict Validation) ---


class SumTotalInput(BaseModel):
    """Input estricto para sumar calorías. Prohíbe campos extra."""

    kcals_meals: list[float] = Field(
        ...,
        description="Lista de valores calóricos de las comidas (ej. [300.5, 500]).",
        min_length=1,
    )
    # Configuración de Pydantic v2 para rechazar "ruido" del LLM
    model_config = {"extra": "forbid"}


class VerifyIngredientsInput(BaseModel):
    """Input estricto para auditoría matemática. Prohíbe campos extra."""

    ingredients: list[float] = Field(
        ...,
        description="Lista de calorías individuales de cada ingrediente.",
        min_length=1,
    )
    expected_kcal_sum: float = Field(
        ..., description="El total calórico que el agente cree que es correcto."
    )
    model_config = {"extra": "forbid"}


#  2. Schema de Validación (Pydantic v2)
class NutritionalInput(BaseModel):
    """Schema de entrada estricto para la herramienta de nutrición."""

    age: int = Field(
        ..., ge=18, le=100, description="Edad del usuario en años (18-100)."
    )
    gender: str = Field(
        ...,
        pattern="^(male|female|masculine|feminine)$",
        description="Género biológico ('male' o 'female').",
    )
    weight: int = Field(..., ge=30, le=300, description="Peso corporal en Kilogramos.")
    height: int = Field(..., ge=100, le=250, description="Altura en Centímetros.")
    activity_level: ActivityLevel = Field(
        ..., description="Nivel de actividad física del usuario."
    )
    objective: Objective = Field(..., description="Objetivo físico actual.")
    diet_type: DietType = Field(
        default=DietType.NORMAL, description="Preferencia dietética (Normal o Keto)."
    )


#  3. Lógica de Negocio (Encapsulamiento)
def _calculate_bmr_mifflin(weight: int, height: int, age: int, gender: str) -> float:
    """Cálculo interno determinista de TMB."""
    base = (10 * weight) + (6.25 * height) - (5 * age)
    return base + 5 if gender.lower() in ["male", "masculine"] else base - 161


def _get_activity_multiplier(level: ActivityLevel) -> float:
    mapping = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHTLY_ACTIVE: 1.375,
        ActivityLevel.MODERATELY_ACTIVE: 1.55,
        ActivityLevel.VERY_ACTIVE: 1.725,
        ActivityLevel.EXTRA_ACTIVE: 1.9,
    }
    return mapping[level]


#  4. Definición de la Tool (LangGraph Interface)
@tool("generate_nutritional_plan", args_schema=NutritionalInput)  # type: ignore [misc]
def generate_nutritional_plan(
    age: int,
    gender: str,
    weight: int,
    height: int,
    activity_level: ActivityLevel,
    objective: Objective,
    diet_type: DietType = DietType.NORMAL,
) -> str:
    """
    Calcula las necesidades calóricas diarias y la distribución de macronutrientes.

    Usa esta herramienta cuando el usuario proporcione sus datos físicos
    y quiera un plan de dieta o saber cuántas calorías consumir.
    NO la uses si faltan datos como peso o altura.
    """
    try:
        # 1. "Manos": Ejecución de cálculos matemáticos puros
        bmr = _calculate_bmr_mifflin(weight, height, age, gender)
        tdee = bmr * _get_activity_multiplier(activity_level)

        # Mapeo de ajustes según objetivo (oculto al LLM)
        objective_adjustments = {
            Objective.FAT_LOSS: 0.83,
            Objective.MUSCLE_GAIN: 1.15,
            Objective.MAINTENANCE: 1.0,
        }

        target_calories = round(tdee * objective_adjustments[objective])

        # Lógica de Macros
        if diet_type == DietType.KETO:
            p_grams = int((target_calories * 0.25) / 4)
            f_grams = int((target_calories * 0.70) / 9)
            c_grams = int((target_calories * 0.05) / 4)
        else:
            # Lógica Normal: Proteína indexada al peso, el resto se ajusta
            p_mult = (
                2.2 if objective in [Objective.FAT_LOSS, Objective.MUSCLE_GAIN] else 1.6
            )
            p_grams = int(weight * p_mult)
            f_grams = int(weight * 0.9)  # 0.9g/kg grasa base

            remaining_cals = target_calories - (p_grams * 4) - (f_grams * 9)
            c_grams = max(0, int(remaining_cals / 4))

        # 2. Diseño de Respuesta: Concisa y Token-Efficient
        return (
            f"PLAN_GENERADO | TDEE: {int(tdee)}kcal | TARGET: {target_calories}kcal\n"
            f"""MACROS >
            Proteína: {p_grams}g
            | Grasas: {f_grams}g
            | Carbohidratos: {c_grams}g\n"""
            f"""META > {objective.value.replace("_", " ").title()}
            ({diet_type.value.title()})"""
        )

    except Exception as e:
        # 3. Mensaje de Error Instructivo (Guidance)
        return f"""ERROR CÁLCULO: Hubo un fallo interno
         ({str(e)}). Por favor verifica que los datos numéricos
        (peso/altura) sean lógicos."""


@tool("sum_total_kcal", args_schema=SumTotalInput)  # type: ignore [misc]
def sum_total_kcal(kcals_meals: list[float]) -> str:
    """
    Suma una lista de calorías de comidas y retorna el total exacto.
    Usa esta herramienta SIEMPRE que necesites agregar ingestas para\\
    obtener un total diario.
    """
    try:
        total = sum(kcals_meals)
        return f"TOTAL_CALCULADO: {round(total, 2)} kcal"
    except Exception as e:
        return f"ERROR DE CÁLCULO: {str(e)}"


@tool("sum_ingredients_kcal", args_schema=VerifyIngredientsInput)  # type: ignore [misc]
def sum_ingredients_kcal(ingredients: list[float], expected_kcal_sum: float) -> str:
    """
    Verifica si la suma de ingredientes de cada comida coincide con el total esperado.
    Si hay discrepancia, devuelve el valor matemático REAL para corrección inmediata.
    """
    try:
        # 1. La Verdad Matemática (Cerebro de Silicio)
        calculated_sum = sum(ingredients)

        # 2. Tolerancia Anti-Obsesiva (0.5 kcal)
        # Evita que el agente se bloquee por decimales irrelevantes (ej. 199.9 vs 200)
        if math.isclose(calculated_sum, expected_kcal_sum, abs_tol=0.5):
            return """VERIFICACIÓN EXITOSA: La suma de ingredientes coincide con el \\
                total esperado."""

        # 3. Protocolo de Corrección Prescriptiva (Anti-Bucle)
        real_total = round(calculated_sum, 2)
        diff = round(real_total - expected_kcal_sum, 2)

        # TODO: Si cumple con un 90% de la cantidad, aceptarlo
        return (
            f"CORRECCIÓN REQUERIDA: La suma matemática real es {real_total} kcal "
            f"(Diferencia detectada: {diff} kcal). "
            f"""STOP: No intentes recalcular.\\
            Actualiza tu respuesta final usando {real_total} kcal."""
        )

    except Exception as e:
        return f"ERROR TÉCNICO: {str(e)}"


class MealDistInput(BaseModel):
    total_calories: float = Field(
        ..., gt=500, lt=10000, description="Objetivo calórico total del día."
    )
    number_of_meals: int = Field(
        ..., ge=1, le=6, description="Cantidad de comidas (1-6)."
    )


@tool("get_meal_distribution", args_schema=MealDistInput)  # type: ignore [misc]
def get_meal_distribution(
    total_calories: float, number_of_meals: int
) -> dict[str, float]:
    """
    Calcula la distribución calórica exacta por comida.

    Usa esta herramienta para saber cuántas calorías asignar al Desayuno,\\
         Comida, Cena, etc.
    basado en la frecuencia de alimentación del usuario.
    """
    # 1. Definición de Patrones de Distribución (Porcentajes)
    # Estos patrones aseguran equilibrio glucémico a lo largo del día.
    distributions = {
        1: {"Comida Única (OMAD)": 1.0},
        2: {"Brunch": 0.5, "Cena": 0.5},
        3: {"Desayuno": 0.3, "Comida": 0.4, "Cena": 0.3},
        4: {"Desayuno": 0.25, "Comida": 0.35, "Snack PM": 0.15, "Cena": 0.25},
        5: {
            "Desayuno": 0.25,
            "Snack AM": 0.10,
            "Comida": 0.35,
            "Snack PM": 0.10,
            "Cena": 0.20,
        },
        6: {
            "Desayuno": 0.20,
            "Snack AM": 0.10,
            "Comida": 0.30,
            "Snack PM": 0.10,
            "Cena": 0.20,
            "Recena": 0.10,
        },
    }

    # 2. Selección de estrategia
    # Si piden más de 6 (raro), forzamos la lógica de 6 para evitar errores.
    selected_dist = distributions.get(number_of_meals, distributions[6])

    # 3. Cálculo de Calorías
    result = {}
    accumulated = 0

    # Iteramos sobre los keys para mantener el orden de inserción (Python 3.7+)
    keys = list(selected_dist.keys())

    for i, meal_name in enumerate(keys):
        percentage = selected_dist[meal_name]

        # Si es la última comida, asignamos el resto para cuadrar decimales
        if i == len(keys) - 1:
            kcal_val = total_calories - accumulated
        else:
            kcal_val = round(total_calories * percentage)
            accumulated += kcal_val

        result[meal_name] = round(kcal_val, 1)

    return result


class ConsolidateInput(BaseModel):
    ingredients_raw: list[str] = Field(
        ...,
        description="""Lista bruta de ingredientes \\
        (ej: ['200g Pechuga de pollo', '100g Pechuga de pollo', '1 manzana']).""",
    )


@tool("consolidate_shopping_list", args_schema=ConsolidateInput)  # type: ignore [misc]
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    """
    Procesa, suma y consolida una lista de ingredientes \\
    crudos en una lista de compra limpia.

    Detecta duplicados, normaliza unidades (kg -> g) y suma las cantidades.
    """
    consolidated: dict[str, float] = {}

    # Regex robusto: Captura (Cantidad) (Unidad opcional) (Preposición opcional)
    # (Nombre del ítem)
    # Grupos:
    # 1. qty: Números (enteros o decimales)
    # 2. unit: g, kg, ml, l, oz, lb, botes, latas...
    # 3. item: El resto del texto
    pattern = r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)?\s*(?:de\s+)?(?P<item>.+)"
    # pattern = r"""(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>g|gr|kg|ml|l|oz|lb|unidades|pieza)
    # ?\s*(?:de\s+)?(?P<item>.+)"""

    for raw_item in ingredients_raw:
        clean_item = raw_item.strip()
        match = re.search(pattern, clean_item, re.IGNORECASE)

        if match:
            # --- Caso 1: Parseo Exitoso ---
            qty = float(match.group("qty"))
            raw_unit = (match.group("unit") or "unidad").lower().strip()
            item_name = match.group("item").lower().strip()

            # Normalización de unidades comunes
            unit = raw_unit
            if raw_unit in ["kg", "kilos", "kilogramos"]:
                qty *= 1000
                unit = "g"
            elif raw_unit in ["gr", "gramos"]:
                unit = "g"
            elif raw_unit in ["l", "litros"]:
                qty *= 1000
                unit = "ml"

            # Clave única compuesta: "pollo (g)" != "pollo (unidad)"
            key = f"{item_name} ({unit})"

            consolidated[key] = consolidated.get(key, 0.0) + qty

        else:
            # --- Caso 2: Fallback (Items sin cantidad clara) ---
            # Ej: "Sal y pimienta", "Un poco de aceite"
            # No lo consideramos error, sino un ítem "genérico"
            key = f"{clean_item.lower()} (varios)"
            # Sumamos 1 solo para que aparezca en la lista,
            # el valor numérico es simbólico aquí
            consolidated[key] = consolidated.get(key, 0.0) + 1.0

    # --- Generación de Salida ---
    final_list = []
    for key, total_qty in consolidated.items():
        # Desempaquetar clave: "pechuga de pollo (g)"
        try:
            name_part, unit_part = key.rsplit(" (", 1)
            unit_clean = unit_part.replace(")", "")

            # Formateo inteligente
            if unit_clean == "varios":
                # Si es genérico, no mostramos "1.0 varios de sal", solo "Sal"
                formatted_item = f"- {name_part.title()}"
            else:
                # Si tiene unidad real
                formatted_item = f"- {total_qty:.0f}{unit_clean} de {name_part.title()}"

            final_list.append(formatted_item)
        except ValueError:
            # Fallback de seguridad extrema por si el split falla
            final_list.append(f"- {key}")

    return "LISTA DE COMPRA CONSOLIDADA:\n" + "\n".join(sorted(final_list))


class IngredientInput(BaseModel):
    name: str = Field(
        ..., description="Nombre del ingrediente (ej. 'Salami', 'Harina')."
    )
    weight_grams: float = Field(
        ..., gt=0, description="Peso en gramos del ingrediente."
    )


class RecipeInput(BaseModel):
    ingredients: list[IngredientInput] = Field(
        ..., description="Lista de ingredientes a analizar.", min_length=1
    )
    # Prohibir campos extra para evitar alucinaciones de argumentos
    model_config = {"extra": "forbid"}


# Schemas de Salida (Structured Output) - Diseño de Respuesta
class NutrientData(BaseModel):
    food_name: str = Field(
        ..., description="Nombre del alimento encontrado en la base de datos."
    )
    matched_weight: float = Field(
        ..., description="Peso utilizado para el cálculo (g)."
    )
    kcal: float = Field(..., description="Calorías calculadas para el peso dado.")
    protein: float = Field(..., description="Proteínas (g).")
    carbs: float = Field(..., description="Carbohidratos (g).")
    fats: float = Field(..., description="Grasas (g).")
    fiber: float = Field(default=0.0, description="Fibra (g).")
    # Campo solicitado para manejar "match cercano"
    notes: str = Field(
        default="Coincidencia exacta",
        description="""Nota sobre si se usó el alimento exacto o un sustituto cercano\\
        (ej. 'Se usó Salami Genérico en lugar de Salami Milano').""",
    )


class RecipeAnalysisOutput(BaseModel):
    items: list[NutrientData] = Field(..., description="Desglose por ingrediente.")
    total_kcal: float = Field(..., description="Suma total de calorías de la receta.")
    general_warning: str | None = Field(
        None, description="Advertencias nutricionales (ej. 'Alto en sodio')."
    )


@tool("fetch_recipe_nutrition_facts", args_schema=RecipeInput)  # type: ignore [misc]
def fetch_recipe_nutrition_facts(
    ingredients: list[IngredientInput],
) -> dict[str, Any]:
    """
    Consulta la base de conocimientos (RAG)
    para obtener valores nutricionales precisos y consolidados.

    Usa esta herramienta cuando tengas la lista definitiva de ingredientes y sus pesos.
    Realiza la búsqueda, escala los valores al peso indicado
    y reporta sustituciones si no hay coincidencia exacta.
    """
    # 3.1 Verificación de Configuración (Ocultar complejidad Legacy)
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        # Error Instructivo
        return {
            "error": """CONFIG_ERROR: No se encontró VECTOR_STORE_ID.\\
             Por favor verifica las variables de entorno."""
        }

    try:
        # 3.2 Configuración del RAG Interno (Micro-Agente encapsulado)
        # Esto cumple con "Responsabilidad Única":
        # la tool se encarga de resolver la data.
        llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)

        # Definición de la herramienta de búsqueda de OpenAI
        file_search_tool_def = {
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
        }

        # Bindear herramienta y Structured Output
        llm_rag_structured = llm.bind_tools(
            [file_search_tool_def]
        ).with_structured_output(RecipeAnalysisOutput)

        # 3.3 Construcción del Prompt Interno
        # Instruimos al modelo para manejar la lógica
        # de "Equivalente más cercano" aquí dentro.
        prompt_text = """
        Eres un asistente nutricional experto con acceso a una base de datos de\\
        alimentos (File Search).
        Tu tarea es buscar los valores nutricionales\\
        para la siguiente lista de ingredientes: {ingredients_list}

        REGLAS CRÍTICAS:
        1. Busca cada ingrediente en la base de datos.
        2. Si encuentras el ingrediente exacto, usa sus datos.
        3. Si NO encuentras el ingrediente exacto, busca el EQUIVALENTE MÁS CERCANO\\
        (ej. si piden 'Salami Milano' y solo hay 'Salami', usa 'Salami').
        4. Si usas un equivalente, DEBES indicarlo claramente en\\
        el campo 'notes' (ej. "No se halló X, se usó Y").
        5. Escala los valores nutricionales\\
        (por 100g) al peso solicitado para cada item.
        6. Calcula los totales de la receta.
        """

        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | llm_rag_structured

        # 3.4 Ejecución (Manos)
        # Convertimos la entrada a un formato string amigable para el prompt interno
        ingredients_str = ", ".join(
            [f"{i.name} ({i.weight_grams}g)" for i in ingredients]
        )

        # Invocación determinista
        result = chain.invoke({"ingredients_list": ingredients_str})

        # 3.5 Retorno (Output Design) - Token Efficiency
        # Retornamos el objeto validado como
        # dict para que el Agente principal lo consuma
        return cast(dict[str, Any], result.model_dump())

    except Exception as e:
        # Mensaje de Error Instructivo
        return {
            "error": f"""RAG_FAILURE: Hubo un error al consultar la base de datos
            nutricional. Detalle: {str(e)}. """
            "Intenta simplificar los nombres de los ingredientes."
        }


tools = [
    generate_nutritional_plan,
    sum_total_kcal,
    sum_ingredients_kcal,
    get_meal_distribution,
    consolidate_shopping_list,
    fetch_recipe_nutrition_facts,
]
