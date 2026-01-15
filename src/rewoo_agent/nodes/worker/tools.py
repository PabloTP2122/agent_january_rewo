"""Tools executed by worker according with plan and #E's."""

import asyncio
import math
import os
import re
from enum import StrEnum
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel, Field

load_dotenv()


# Base Model con configuración estricta (DRY)
class StrictBaseModel(BaseModel):
    """
    Clase base para todos los schemas de input de herramientas.

    Configuración:
    - extra="forbid": Rechaza campos no declarados (anti-alucinación del LLM)
    """

    model_config = {"extra": "forbid"}


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


# 1. Schemas de Entrada (Strict Validation)
class SumTotalInput(StrictBaseModel):
    """Input estricto para sumar calorías."""

    kcals_meals: list[float] = Field(
        ...,
        description="Lista de valores calóricos de las comidas (ej. [300.5, 500]).",
        min_length=1,
    )


class VerifyIngredientsInput(StrictBaseModel):
    """Input estricto para auditoría matemática."""

    ingredients: list[float] = Field(
        ...,
        description="Lista de calorías individuales de cada ingrediente.",
        min_length=1,
    )
    expected_kcal_sum: float = Field(
        ..., description="El total calórico que el agente cree que es correcto."
    )


#  2. Schema de Validación (Pydantic v2)
class NutritionalInput(StrictBaseModel):
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
        objective_label = objective.value.replace("_", " ").title()
        return (
            f"TDEE: {int(tdee)} kcal | Objetivo: {target_calories} kcal\n"
            f"Proteína: {p_grams}g | Grasas: {f_grams}g | Carbohidratos: {c_grams}g\n"
            f"Meta: {objective_label} ({diet_type.value.title()})"
        )

    except Exception as e:
        # 3. Mensaje de Error Instructivo (Guidance)
        return (
            f"Error en cálculo: {str(e)}. "
            "Verifica que los datos numéricos (peso/altura) sean lógicos."
        )


@tool("sum_total_kcal", args_schema=SumTotalInput)  # type: ignore [misc]
def sum_total_kcal(kcals_meals: list[float]) -> str:
    """
    Suma una lista de calorías de comidas y retorna el total exacto.
    Usa esta herramienta SIEMPRE que necesites agregar ingestas para
    obtener un total diario.
    """
    try:
        total = sum(kcals_meals)
        return f"{round(total, 2)} kcal"
    except Exception as e:
        return f"Error: {str(e)}. Verifica que la lista contenga solo números."


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
            return "Verificación exitosa: suma de ingredientes coincide con el total."

        # 3. Protocolo de Corrección Prescriptiva (Anti-Bucle)
        real_total = round(calculated_sum, 2)
        diff = round(real_total - expected_kcal_sum, 2)

        return (
            f"Corrección requerida: suma real es {real_total} kcal "
            f"(diferencia: {diff} kcal). "
            f"Usa {real_total} kcal en tu respuesta final."
        )

    except Exception as e:
        return f"Error técnico: {str(e)}"


class MealDistInput(StrictBaseModel):
    """Input para distribución de comidas."""

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


class ConsolidateInput(StrictBaseModel):
    """Input para consolidación de lista de compras."""

    ingredients_raw: list[str] = Field(
        ...,
        description="Lista de ingredientes (ej: ['200g Pechuga', '100g Arroz']).",
    )


@tool("consolidate_shopping_list", args_schema=ConsolidateInput)  # type: ignore [misc]
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    """
    Consolida una lista de ingredientes crudos en una lista de compra limpia.

    Usa esta herramienta cuando tengas ingredientes de múltiples recetas
    y necesites generar una lista de compras unificada.
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
            #  Caso 1: Parseo Exitoso
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
            #  Caso 2: Fallback (Items sin cantidad clara)
            # Ej: "Sal y pimienta", "Un poco de aceite"
            # No lo consideramos error, sino un ítem "genérico"
            key = f"{clean_item.lower()} (varios)"
            # Sumamos 1 solo para que aparezca en la lista,
            # el valor numérico es simbólico aquí
            consolidated[key] = consolidated.get(key, 0.0) + 1.0

    #  Generación de Salida
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

    return "\n".join(sorted(final_list))


class IngredientInput(StrictBaseModel):
    """Estructura de un ingrediente individual proveniente del Planner."""

    nombre: str = Field(
        ...,
        description="Nombre del ingrediente identificado en el plan.",
    )
    peso_gramos: float = Field(
        ...,
        description="Peso numérico en gramos para el cálculo.",
    )


class RecipeAnalysisInput(StrictBaseModel):
    """Schema de entrada estricto para la herramienta de análisis de recetas."""

    ingredientes: list[IngredientInput] = Field(
        ...,
        description="Lista definitiva de ingredientes y pesos generada por el Planner.",
    )


class ProcessedItem(BaseModel):
    input_name: str
    matched_db_name: str
    total_kcal: float
    notes: str


class NutritionResult(BaseModel):
    """Resultado consolidado del análisis nutricional de una receta."""

    processed_items: list[ProcessedItem]
    total_recipe_kcal: float
    warnings: str | None = Field(
        None, description="Reporte de fallos de búsqueda o inconsistencias."
    )


class NutriFacts(BaseModel):
    """Schema para extracción de datos nutricionales via RAG."""

    food_name: str = Field(
        ...,
        description="Nombre del alimento en el texto recuperado.",
    )
    calories_100g: float = Field(
        ...,
        description="Calorías por 100g.",
    )
    notes: str = Field(
        ...,
        description="Notas sobre la calidad de la coincidencia.",
    )


class ResourceLoader:
    """
    Singleton para gestionar conexiones.
    Centraliza la validación de configuración.
    """

    _retriever = None
    _extractor_llm = None

    @staticmethod
    def _validate_env_vars() -> None:
        """Valida que las credenciales críticas existan antes de intentar conectar."""
        required_vars = ["PINECONE_API_KEY", "OPENAI_API_KEY", "PINECONE_INDEX_NAME"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ConnectionError(
                f"""Configuración faltante en el entorno del Worker:
                 {", ".join(missing)}. """
                "Asegúrate de que las variables de entorno estén cargadas."
            )

    @classmethod
    def get_retriever(cls) -> Any:
        if cls._retriever is None:
            # 1. Validamos antes de conectar
            cls._validate_env_vars()

            # 2. Obtenemos configuración del entorno
            index_name = os.getenv("PINECONE_INDEX_NAME", "")
            embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            # Default seguro

            try:
                embeddings = OpenAIEmbeddings(model=embedding_model)

                # PineconeVectorStore busca automáticamente
                # 'PINECONE_API_KEY' en os.environ
                # No hace falta pasarlo explícitamente si la variable se llama así.
                vector_store = PineconeVectorStore.from_existing_index(
                    index_name=index_name, embedding=embeddings
                )
                cls._retriever = vector_store.as_retriever(search_kwargs={"k": 1})

            except Exception as e:
                # Capturamos errores de librería (ej. índice no existe, key inválida)
                raise ConnectionError(  # noqa: B904
                    f"Error inicializando conexión a Pinecone: {str(e)}"
                )

        return cls._retriever

    @classmethod
    def get_extractor_chain(cls) -> RunnableSerializable[dict, Any]:
        if cls._extractor_llm is None:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            prompt = ChatPromptTemplate.from_template(
                """Analiza el contexto. Extrae datos para: '{ingredient_name}'.
                Contexto: {context}
                Si no coincide, retorna 0 y explica en notas."""
            )
            cls._extractor_llm = prompt | llm.with_structured_output(NutriFacts)
        return cls._extractor_llm


async def _process_ingredient_task(ing: IngredientInput) -> ProcessedItem:
    """Unidad de trabajo atómica para un ingrediente."""
    try:
        retriever = ResourceLoader.get_retriever()
        extractor = ResourceLoader.get_extractor_chain()

        # 1. Retrieval
        docs = await retriever.ainvoke(ing.nombre)

        if not docs:
            return ProcessedItem(
                input_name=ing.nombre,
                matched_db_name="MISSING",
                total_kcal=0,
                notes="No encontrado en Knowledge Base.",
            )

        # 2. Extraction
        raw_data = await extractor.ainvoke(
            {"ingredient_name": ing.nombre, "context": docs[0].page_content}
        )

        # 3. Calculation
        factor = ing.peso_gramos / 100.0
        return ProcessedItem(
            input_name=ing.nombre,
            matched_db_name=raw_data.food_name,
            total_kcal=round(raw_data.calories_100g * factor, 1),
            notes=raw_data.notes,
        )

    except Exception as e:
        return ProcessedItem(
            input_name=ing.nombre,
            matched_db_name="ERROR",
            total_kcal=0,
            notes=f"Excepción interna: {str(e)}",
        )


@tool("calculate_recipe_nutrition", args_schema=RecipeAnalysisInput)  # type: ignore [misc]
async def calculate_recipe_nutrition(
    ingredientes: list[IngredientInput], _config: RunnableConfig | None = None
) -> Any:
    """
    Consulta la base de conocimientos (RAG) para obtener valores
    nutricionales precisos y consolidados.

    Usa esta herramienta cuando tengas la lista definitiva de ingredientes
    y sus pesos proveniente del plan.
    Realiza la búsqueda vectorial, escala los valores al peso indicado
    y reporta sustituciones o advertencias si no hay coincidencia exacta.
    """

    # Fail-fast si la infraestructura no responde
    try:
        ResourceLoader.get_retriever()
    except ConnectionError as e:
        return {"system_error": str(e), "status": "failed"}

    # Ejecución paralela (Worker behavior)
    tasks = [_process_ingredient_task(ing) for ing in ingredientes]
    results = await asyncio.gather(*tasks)

    # Consolidación de resultados
    clean_items = []
    total_kcal = 0.0
    warnings = []

    for item in results:
        clean_items.append(item)
        total_kcal += item.total_kcal

        if item.matched_db_name in ["MISSING", "ERROR"]:
            warnings.append(f"[{item.input_name}]: {item.notes}")

    output = NutritionResult(
        processed_items=clean_items,
        total_recipe_kcal=round(total_kcal, 1),
        warnings=" | ".join(warnings) if warnings else None,
    )

    return output.model_dump()


tools = [
    generate_nutritional_plan,
    sum_total_kcal,
    sum_ingredients_kcal,
    get_meal_distribution,
    consolidate_shopping_list,
    calculate_recipe_nutrition,
]
