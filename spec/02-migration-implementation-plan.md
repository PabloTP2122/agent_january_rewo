# Plan de Migración: Structured Plan-and-Execute

**Fecha**: 2026-01-15
**Autor**: Claude Opus 4.5
**Estado**: SPEC TÉCNICO - Listo para Implementación
**Documento Previo**: `spec/01-architecture-analysis-rewoo-vs-alternatives.md`

---

## 1. Resumen Ejecutivo

Este documento detalla la implementación de la arquitectura **Structured Plan-and-Execute** para reemplazar ReWOO en el agente de planificación nutricional.

### Cambios Principales

| Componente | Antes (ReWOO) | Después (Structured P&E) |
|------------|---------------|--------------------------|
| **Flujo** | Planner → Worker → Solver | DataCollection → Calculation → RecipeGen → Validation |
| **Parsing** | Regex (#E variables) | Structured Output nativo |
| **Recopilación datos** | Externa/manual | Integrada en el grafo |
| **Human-in-the-loop** | No soportado | Nativo con CopilotKit |
| **Fine-tuning target** | Planner (no viable) | Recipe Generation (viable) |

### Beneficios Esperados

- **40% reducción** en consumo de tokens
- **Recopilación conversacional** de datos del usuario
- **Fine-tuning viable** en generación de recetas
- **Debugging simplificado** (sin regex frágil)

---

## 2. Nueva Estructura de Directorios

```
src/
├── nutrition_agent/                    # NUEVO: Agente principal
│   ├── __init__.py
│   ├── graph.py                        # StateGraph con conditional edges
│   ├── state.py                        # NutritionAgentState
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── data_collection.py          # Nodo 1: Recopilación
│   │   ├── calculation.py              # Nodo 2: Cálculos TDEE/Macros
│   │   ├── recipe_generation.py        # Nodo 3: Generación de comidas
│   │   └── validation.py               # Nodo 4: Verificación final
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_profile.py             # UserProfile (structured output)
│   │   ├── nutritional_targets.py      # NutritionalTargets
│   │   └── diet_plan.py                # Re-exporta DietPlan existente
│   └── prompts/
│       ├── __init__.py
│       ├── data_collection.py          # Prompt para recopilación
│       └── recipe_generation.py        # Prompt para generar recetas
│
├── rewoo_agent/                        # MANTENER: Para comparación A/B
│   └── ... (sin cambios)
│
├── shared/                             # NUEVO: Código compartido
│   ├── __init__.py
│   ├── tools.py                        # Mover tools de rewoo_agent
│   ├── enums.py                        # ActivityLevel, Objective, DietType
│   └── llm.py                          # Factory de LLMs con Helicone
│
└── api/
    └── main.py                         # Agregar nutrition_agent
```

---

## 3. Diagrama de Flujo del Grafo

```
                    ┌─────────────────────────────────────┐
                    │              START                   │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION NODE                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Entrada: messages del usuario                                         │  │
│  │  Salida: UserProfile (structured output) o mensaje pidiendo datos     │  │
│  │                                                                        │  │
│  │  Tools disponibles:                                                    │  │
│  │  - Frontend tool: ask_user_info (CopilotKit)                          │  │
│  │                                                                        │  │
│  │  Comportamiento:                                                       │  │
│  │  1. Analiza mensajes para extraer datos del usuario                   │  │
│  │  2. Si faltan datos → emite mensaje pidiendo información              │  │
│  │  3. Si completo → genera UserProfile y avanza                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    ¿UserProfile válido?   │
                    └─────────────┬─────────────┘
                          │               │
                    (No)  │               │ (Sí)
                          │               │
              ┌───────────┘               └───────────┐
              │                                       │
              ▼                                       ▼
    ┌─────────────────┐               ┌───────────────────────────────────────┐
    │  Volver a       │               │         CALCULATION NODE              │
    │  DATA_COLLECTION│               │  ┌─────────────────────────────────┐  │
    │  (pedir datos)  │               │  │  Entrada: UserProfile           │  │
    └─────────────────┘               │  │  Salida: NutritionalTargets +   │  │
                                      │  │          MealDistribution       │  │
                                      │  │                                 │  │
                                      │  │  Tools ejecutadas:              │  │
                                      │  │  - generate_nutritional_plan    │  │
                                      │  │  - get_meal_distribution        │  │
                                      │  │                                 │  │
                                      │  │  100% determinístico (no LLM)   │  │
                                      │  └─────────────────────────────────┘  │
                                      └───────────────────┬───────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RECIPE GENERATION NODE                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Entrada: NutritionalTargets + MealDistribution                       │  │
│  │  Salida: Meal (una comida por iteración)                              │  │
│  │                                                                        │  │
│  │  Tools disponibles:                                                    │  │
│  │  - calculate_recipe_nutrition (RAG)                                   │  │
│  │                                                                        │  │
│  │  Comportamiento:                                                       │  │
│  │  1. Genera una comida con structured output                           │  │
│  │  2. Valida ingredientes con RAG                                       │  │
│  │  3. Agrega a meals_completed                                          │  │
│  │  4. Loop hasta completar todas las comidas                            │  │
│  │                                                                        │  │
│  │  ★ TARGET PARA FINE-TUNING ★                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │ ¿Todas las comidas listas?│
                    └─────────────┬─────────────┘
                          │               │
                    (No)  │               │ (Sí)
                          │               │
              ┌───────────┘               └───────────┐
              │                                       │
              ▼                                       ▼
    ┌─────────────────┐               ┌───────────────────────────────────────┐
    │  Volver a       │               │         VALIDATION NODE               │
    │  RECIPE_GEN     │               │  ┌─────────────────────────────────┐  │
    │  (siguiente     │               │  │  Entrada: meals_completed       │  │
    │   comida)       │               │  │  Salida: DietPlan o errores     │  │
    └─────────────────┘               │  │                                 │  │
                                      │  │  Tools ejecutadas:              │  │
                                      │  │  - sum_ingredients_kcal         │  │
                                      │  │  - sum_total_kcal               │  │
                                      │  │  - consolidate_shopping_list    │  │
                                      │  │                                 │  │
                                      │  │  Comportamiento:                │  │
                                      │  │  1. Valida matemáticamente      │  │
                                      │  │  2. Si error → vuelve a RECIPE  │  │
                                      │  │  3. Si OK → genera DietPlan     │  │
                                      │  └─────────────────────────────────┘  │
                                      └───────────────────┬───────────────────┘
                                                          │
                                            ┌─────────────┴─────────────┐
                                            │    ¿Validación exitosa?   │
                                            └─────────────┬─────────────┘
                                                  │               │
                                            (No)  │               │ (Sí)
                                                  │               │
                                      ┌───────────┘               └───────────┐
                                      │                                       │
                                      ▼                                       ▼
                            ┌─────────────────┐               ┌───────────────────┐
                            │  Volver a       │               │       END         │
                            │  RECIPE_GEN     │               │  (DietPlan final) │
                            │  (regenerar     │               └───────────────────┘
                            │   comida con    │
                            │   error)        │
                            └─────────────────┘
```

---

## 4. Definición del Estado

### 4.1 Modelos de Datos

```python
# src/nutrition_agent/models/user_profile.py

from typing import Literal
from pydantic import BaseModel, Field

from shared.enums import ActivityLevel, Objective, DietType


class UserProfile(BaseModel):
    """
    Perfil del usuario recopilado conversacionalmente.
    Usado como structured output del Data Collection Node.
    """

    # Datos biométricos
    age: int = Field(
        ...,
        ge=18,
        le=100,
        description="Edad del usuario en años."
    )
    gender: Literal["male", "female"] = Field(
        ...,
        description="Género biológico para cálculo de TMB."
    )
    weight: int = Field(
        ...,
        ge=30,
        le=300,
        description="Peso corporal en kilogramos."
    )
    height: int = Field(
        ...,
        ge=100,
        le=250,
        description="Altura en centímetros."
    )

    # Preferencias
    activity_level: ActivityLevel = Field(
        ...,
        description="Nivel de actividad física semanal."
    )
    objective: Objective = Field(
        ...,
        description="Objetivo principal: perder grasa, ganar músculo, o mantenimiento."
    )
    diet_type: DietType = Field(
        default=DietType.NORMAL,
        description="Tipo de dieta preferida."
    )

    # Restricciones
    excluded_foods: list[str] = Field(
        default_factory=list,
        description="Alimentos que el usuario no puede o no quiere consumir."
    )
    number_of_meals: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Número de comidas al día."
    )
```

```python
# src/nutrition_agent/models/nutritional_targets.py

from pydantic import BaseModel, Field


class NutritionalTargets(BaseModel):
    """
    Resultado del cálculo de TDEE y macros.
    Generado por el Calculation Node.
    """

    # Calorías
    bmr: float = Field(..., description="Tasa Metabólica Basal (Mifflin-St Jeor).")
    tdee: float = Field(..., description="Gasto Energético Total Diario.")
    target_calories: float = Field(..., description="Calorías objetivo ajustadas al objetivo.")

    # Macronutrientes
    protein_grams: float = Field(..., ge=0)
    carbs_grams: float = Field(..., ge=0)
    fat_grams: float = Field(..., ge=0)

    # Porcentajes
    protein_percentage: float = Field(..., ge=0, le=100)
    carbs_percentage: float = Field(..., ge=0, le=100)
    fat_percentage: float = Field(..., ge=0, le=100)

    # Metadata
    objective_label: str = Field(..., description="Etiqueta legible del objetivo.")
    diet_type_label: str = Field(..., description="Etiqueta legible del tipo de dieta.")


class MealDistribution(BaseModel):
    """
    Distribución calórica por comida.
    Generado por get_meal_distribution tool.
    """

    distribution: dict[str, float] = Field(
        ...,
        description="Mapa de nombre de comida a calorías asignadas."
    )
    # Ejemplo: {"Desayuno": 600.0, "Comida": 800.0, "Cena": 600.0}
```

### 4.2 Estado Principal del Agente

```python
# src/nutrition_agent/state.py

from typing import Annotated, Any
import operator

from copilotkit import CopilotKitState
from pydantic import BaseModel

from .models.user_profile import UserProfile
from .models.nutritional_targets import NutritionalTargets, MealDistribution
from src.rewoo_agent.structured_output_meal import DietPlan, Meal


class NutritionAgentState(CopilotKitState):
    """
    Estado del agente de planificación nutricional.

    Hereda de CopilotKitState para integración completa:
    - messages: List[BaseMessage] - Historial de conversación
    - copilotkit: Dict con actions (frontend tools) y context

    Organizado en fases del flujo:
    """

    # ═══════════════════════════════════════════════════════════════
    # FASE 1: DATA COLLECTION
    # ═══════════════════════════════════════════════════════════════

    user_profile: UserProfile | None = None
    """Perfil completo del usuario. None si aún no está completo."""

    missing_fields: list[str] = []
    """Campos faltantes para solicitar al usuario."""

    collection_attempts: int = 0
    """Contador de intentos de recopilación (para evitar loops infinitos)."""

    # ═══════════════════════════════════════════════════════════════
    # FASE 2: CALCULATION
    # ═══════════════════════════════════════════════════════════════

    nutritional_targets: NutritionalTargets | None = None
    """Resultado del cálculo de TDEE y macros."""

    meal_distribution: MealDistribution | None = None
    """Distribución calórica por comida."""

    # ═══════════════════════════════════════════════════════════════
    # FASE 3: RECIPE GENERATION
    # ═══════════════════════════════════════════════════════════════

    current_meal_index: int = 0
    """Índice de la comida que se está generando actualmente."""

    current_meal_name: str = ""
    """Nombre de la comida actual (ej: "Desayuno")."""

    current_meal_target_kcal: float = 0.0
    """Calorías objetivo para la comida actual."""

    meals_completed: Annotated[list[Meal], operator.add] = []
    """Lista de comidas ya generadas y validadas."""

    # ═══════════════════════════════════════════════════════════════
    # FASE 4: VALIDATION
    # ═══════════════════════════════════════════════════════════════

    validation_errors: list[str] = []
    """Errores detectados en la validación matemática."""

    meals_needing_regeneration: list[str] = []
    """Nombres de comidas que necesitan ser regeneradas."""

    # ═══════════════════════════════════════════════════════════════
    # OUTPUT FINAL
    # ═══════════════════════════════════════════════════════════════

    final_diet_plan: DietPlan | None = None
    """El plan de dieta final, listo para mostrar en UI."""
```

---

## 5. Implementación de Nodos

### 5.1 Data Collection Node

```python
# src/nutrition_agent/nodes/data_collection.py

from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import ValidationError

from copilotkit import copilotkit_emit_message, copilotkit_emit_state

from ..state import NutritionAgentState
from ..models.user_profile import UserProfile
from ..prompts.data_collection import DATA_COLLECTION_SYSTEM_PROMPT
from shared.llm import get_llm


async def data_collection_node(
    state: NutritionAgentState,
    config: RunnableConfig
) -> Command[Literal["calculation", "data_collection"]]:
    """
    Nodo 1: Recopila datos del usuario conversacionalmente.

    Comportamiento:
    1. Si user_profile ya existe y es válido → avanza a calculation
    2. Si no, analiza mensajes para extraer información
    3. Usa structured output para validar completitud
    4. Si faltan datos, emite mensaje preguntando

    Returns:
        Command con goto="calculation" si completo,
        o goto="data_collection" si necesita más datos.
    """

    # Emitir estado actual al frontend (CopilotKit)
    await copilotkit_emit_state(config, {
        "phase": "data_collection",
        "missing_fields": state.get("missing_fields", []),
        "collection_attempts": state.get("collection_attempts", 0)
    })

    # ─────────────────────────────────────────────────────────────────
    # CASO 1: Ya tenemos perfil completo
    # ─────────────────────────────────────────────────────────────────
    if state.get("user_profile") is not None:
        return Command(goto="calculation")

    # ─────────────────────────────────────────────────────────────────
    # CASO 2: Demasiados intentos (evitar loop infinito)
    # ─────────────────────────────────────────────────────────────────
    max_attempts = 10
    current_attempts = state.get("collection_attempts", 0)

    if current_attempts >= max_attempts:
        error_msg = (
            "No he podido recopilar todos los datos necesarios después de "
            f"{max_attempts} intentos. Por favor, proporciona tu información "
            "de forma más clara: edad, género, peso (kg), altura (cm), "
            "nivel de actividad, y objetivo (perder grasa/ganar músculo/mantener)."
        )
        await copilotkit_emit_message(config, error_msg)
        return Command(
            goto="data_collection",
            update={"collection_attempts": current_attempts + 1}
        )

    # ─────────────────────────────────────────────────────────────────
    # CASO 3: Intentar extraer perfil de los mensajes
    # ─────────────────────────────────────────────────────────────────

    llm = get_llm(model="gpt-4o", temperature=0)
    llm_with_structure = llm.with_structured_output(UserProfile)

    messages = state.get("messages", [])
    system_msg = SystemMessage(content=DATA_COLLECTION_SYSTEM_PROMPT)

    try:
        # Intentar parsear UserProfile desde la conversación
        user_profile: UserProfile = await llm_with_structure.ainvoke(
            [system_msg, *messages],
            config
        )

        # ¡Éxito! Tenemos perfil completo
        await copilotkit_emit_state(config, {
            "user_profile": user_profile.model_dump(),
            "phase": "profile_complete"
        })

        # Confirmar al usuario
        confirmation = (
            f"Perfecto, tengo toda tu información:\n"
            f"- Edad: {user_profile.age} años\n"
            f"- Género: {user_profile.gender}\n"
            f"- Peso: {user_profile.weight} kg\n"
            f"- Altura: {user_profile.height} cm\n"
            f"- Actividad: {user_profile.activity_level.value}\n"
            f"- Objetivo: {user_profile.objective.value}\n"
            f"- Comidas al día: {user_profile.number_of_meals}\n\n"
            "Calculando tu plan nutricional..."
        )
        await copilotkit_emit_message(config, confirmation)

        return Command(
            goto="calculation",
            update={
                "user_profile": user_profile,
                "missing_fields": [],
                "collection_attempts": current_attempts + 1
            }
        )

    except ValidationError as e:
        # Extraer campos faltantes del error de validación
        missing = []
        for error in e.errors():
            if error["type"] == "missing":
                field_name = error["loc"][0] if error["loc"] else "unknown"
                missing.append(str(field_name))

        # Si no detectamos campos específicos, pedir todo
        if not missing:
            missing = ["age", "gender", "weight", "height", "activity_level", "objective"]

        # Construir mensaje amigable
        field_labels = {
            "age": "tu edad",
            "gender": "tu género (masculino/femenino)",
            "weight": "tu peso en kg",
            "height": "tu altura en cm",
            "activity_level": "tu nivel de actividad física",
            "objective": "tu objetivo (perder grasa, ganar músculo, o mantener peso)",
            "number_of_meals": "cuántas comidas haces al día",
            "excluded_foods": "alimentos que quieras excluir",
            "diet_type": "tipo de dieta preferida"
        }

        missing_labels = [field_labels.get(f, f) for f in missing[:3]]  # Máximo 3

        question = (
            f"Para crear tu plan nutricional personalizado, "
            f"necesito saber {', '.join(missing_labels)}. "
            f"¿Puedes proporcionarme esta información?"
        )

        await copilotkit_emit_message(config, question)

        return Command(
            goto="data_collection",
            update={
                "missing_fields": missing,
                "collection_attempts": current_attempts + 1,
                "messages": [AIMessage(content=question)]
            }
        )

    except Exception as e:
        # Error inesperado
        error_msg = (
            "Hubo un problema procesando tu información. "
            "¿Podrías decirme tu edad, peso, altura, y objetivo de forma clara?"
        )
        await copilotkit_emit_message(config, error_msg)

        return Command(
            goto="data_collection",
            update={
                "collection_attempts": current_attempts + 1,
                "messages": [AIMessage(content=error_msg)]
            }
        )
```

### 5.2 Calculation Node

```python
# src/nutrition_agent/nodes/calculation.py

from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from copilotkit import copilotkit_emit_state

from ..state import NutritionAgentState
from ..models.nutritional_targets import NutritionalTargets, MealDistribution
from shared.tools import (
    _calculate_bmr_mifflin,
    _get_activity_multiplier,
    get_meal_distribution as get_meal_dist_tool
)
from shared.enums import Objective, DietType


async def calculation_node(
    state: NutritionAgentState,
    config: RunnableConfig
) -> Command[Literal["recipe_generation"]]:
    """
    Nodo 2: Ejecuta cálculos determinísticos de TDEE y macros.

    Este nodo NO usa LLM - solo ejecuta las tools de cálculo.
    Esto garantiza precisión matemática y reduce costos.

    Returns:
        Command con goto="recipe_generation" y los targets calculados.
    """

    user_profile = state["user_profile"]

    # ─────────────────────────────────────────────────────────────────
    # PASO 1: Calcular TMB y TDEE
    # ─────────────────────────────────────────────────────────────────

    bmr = _calculate_bmr_mifflin(
        weight=user_profile.weight,
        height=user_profile.height,
        age=user_profile.age,
        gender=user_profile.gender
    )

    activity_multiplier = _get_activity_multiplier(user_profile.activity_level)
    tdee = bmr * activity_multiplier

    # ─────────────────────────────────────────────────────────────────
    # PASO 2: Ajustar según objetivo
    # ─────────────────────────────────────────────────────────────────

    objective_adjustments = {
        Objective.FAT_LOSS: 0.83,      # -17% déficit
        Objective.MUSCLE_GAIN: 1.15,   # +15% superávit
        Objective.MAINTENANCE: 1.0,    # Sin cambio
    }

    target_calories = round(tdee * objective_adjustments[user_profile.objective])

    # ─────────────────────────────────────────────────────────────────
    # PASO 3: Calcular macronutrientes
    # ─────────────────────────────────────────────────────────────────

    if user_profile.diet_type == DietType.KETO:
        # Keto: 25% proteína, 70% grasa, 5% carbohidratos
        protein_grams = int((target_calories * 0.25) / 4)
        fat_grams = int((target_calories * 0.70) / 9)
        carbs_grams = int((target_calories * 0.05) / 4)

        protein_percentage = 25.0
        fat_percentage = 70.0
        carbs_percentage = 5.0
    else:
        # Normal: Proteína indexada al peso, el resto se ajusta
        protein_mult = (
            2.2 if user_profile.objective in [Objective.FAT_LOSS, Objective.MUSCLE_GAIN]
            else 1.6
        )
        protein_grams = int(user_profile.weight * protein_mult)
        fat_grams = int(user_profile.weight * 0.9)

        protein_cals = protein_grams * 4
        fat_cals = fat_grams * 9
        remaining_cals = target_calories - protein_cals - fat_cals
        carbs_grams = max(0, int(remaining_cals / 4))

        # Calcular porcentajes reales
        total_macro_cals = (protein_grams * 4) + (carbs_grams * 4) + (fat_grams * 9)
        protein_percentage = round((protein_grams * 4 / total_macro_cals) * 100, 1)
        carbs_percentage = round((carbs_grams * 4 / total_macro_cals) * 100, 1)
        fat_percentage = round((fat_grams * 9 / total_macro_cals) * 100, 1)

    # Crear objeto NutritionalTargets
    nutritional_targets = NutritionalTargets(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        target_calories=target_calories,
        protein_grams=protein_grams,
        carbs_grams=carbs_grams,
        fat_grams=fat_grams,
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fat_percentage=fat_percentage,
        objective_label=user_profile.objective.value.replace("_", " ").title(),
        diet_type_label=user_profile.diet_type.value.title()
    )

    # ─────────────────────────────────────────────────────────────────
    # PASO 4: Obtener distribución de comidas
    # ─────────────────────────────────────────────────────────────────

    # Llamar a la tool existente
    distribution_dict = get_meal_dist_tool.invoke({
        "total_calories": target_calories,
        "number_of_meals": user_profile.number_of_meals
    })

    meal_distribution = MealDistribution(distribution=distribution_dict)

    # ─────────────────────────────────────────────────────────────────
    # PASO 5: Emitir estado y preparar siguiente fase
    # ─────────────────────────────────────────────────────────────────

    # Emitir al frontend
    await copilotkit_emit_state(config, {
        "phase": "calculation_complete",
        "nutritional_targets": nutritional_targets.model_dump(),
        "meal_distribution": meal_distribution.model_dump()
    })

    # Preparar estado para generación de recetas
    meal_names = list(distribution_dict.keys())
    first_meal_name = meal_names[0] if meal_names else "Desayuno"
    first_meal_kcal = distribution_dict.get(first_meal_name, target_calories / 3)

    return Command(
        goto="recipe_generation",
        update={
            "nutritional_targets": nutritional_targets,
            "meal_distribution": meal_distribution,
            "current_meal_index": 0,
            "current_meal_name": first_meal_name,
            "current_meal_target_kcal": first_meal_kcal,
            "meals_completed": []
        }
    )
```

### 5.3 Recipe Generation Node

```python
# src/nutrition_agent/nodes/recipe_generation.py

from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from copilotkit import copilotkit_emit_message, copilotkit_emit_state

from ..state import NutritionAgentState
from ..prompts.recipe_generation import RECIPE_GENERATION_PROMPT
from src.rewoo_agent.structured_output_meal import Meal
from shared.llm import get_llm
from shared.tools import calculate_recipe_nutrition


async def recipe_generation_node(
    state: NutritionAgentState,
    config: RunnableConfig
) -> Command[Literal["recipe_generation", "validation"]]:
    """
    Nodo 3: Genera comidas una a una con structured output.

    Este nodo es el TARGET PARA FINE-TUNING porque:
    1. Tiene entrada/salida claramente definida
    2. La calidad de las recetas es el diferenciador
    3. No afecta la lógica del grafo

    Flujo:
    1. Genera una Meal con LLM + structured output
    2. Valida nutrición con RAG (calculate_recipe_nutrition)
    3. Si es la última comida → validation
    4. Si hay más comidas → loop a sí mismo

    Returns:
        Command con goto="validation" si todas listas,
        o goto="recipe_generation" para la siguiente comida.
    """

    nutritional_targets = state["nutritional_targets"]
    meal_distribution = state["meal_distribution"]
    user_profile = state["user_profile"]

    current_index = state.get("current_meal_index", 0)
    current_meal_name = state.get("current_meal_name", "Desayuno")
    current_meal_kcal = state.get("current_meal_target_kcal", 600.0)
    meals_completed = state.get("meals_completed", [])

    # ─────────────────────────────────────────────────────────────────
    # PASO 1: Construir prompt para generar la comida
    # ─────────────────────────────────────────────────────────────────

    # Preparar restricciones
    excluded = user_profile.excluded_foods if user_profile.excluded_foods else ["ninguno"]
    excluded_str = ", ".join(excluded)

    # Información de macros para esta comida (proporcional)
    meal_count = len(meal_distribution.distribution)
    meal_protein = round(nutritional_targets.protein_grams / meal_count, 1)
    meal_carbs = round(nutritional_targets.carbs_grams / meal_count, 1)
    meal_fat = round(nutritional_targets.fat_grams / meal_count, 1)

    generation_prompt = RECIPE_GENERATION_PROMPT.format(
        meal_name=current_meal_name,
        target_kcal=current_meal_kcal,
        protein_grams=meal_protein,
        carbs_grams=meal_carbs,
        fat_grams=meal_fat,
        diet_type=nutritional_targets.diet_type_label,
        excluded_foods=excluded_str,
        objective=nutritional_targets.objective_label
    )

    # ─────────────────────────────────────────────────────────────────
    # PASO 2: Generar comida con structured output
    # ─────────────────────────────────────────────────────────────────

    # Notificar al usuario
    await copilotkit_emit_message(
        config,
        f"Generando {current_meal_name} ({int(current_meal_kcal)} kcal)..."
    )

    llm = get_llm(model="gpt-4o", temperature=0.7)  # Algo de creatividad
    llm_with_structure = llm.with_structured_output(Meal)

    try:
        meal: Meal = await llm_with_structure.ainvoke(
            [
                SystemMessage(content=generation_prompt),
                HumanMessage(content=f"Genera un {current_meal_name} para una dieta de {nutritional_targets.objective_label}.")
            ],
            config
        )

        # Asegurar que meal_time coincide
        meal.meal_time = _normalize_meal_time(current_meal_name)

    except Exception as e:
        # Fallback: crear comida básica
        meal = Meal(
            meal_time=_normalize_meal_time(current_meal_name),
            title=f"{current_meal_name} Balanceado",
            description="Una comida equilibrada y nutritiva.",
            total_calories=current_meal_kcal,
            ingredients=["Ingredientes por definir"],
            preparation=["Preparación por definir"]
        )

    # ─────────────────────────────────────────────────────────────────
    # PASO 3: Validar nutrición con RAG (opcional pero recomendado)
    # ─────────────────────────────────────────────────────────────────

    # Preparar ingredientes para RAG
    # Nota: En producción, parsearíamos los ingredientes de meal.ingredients
    # Por ahora, confiamos en el LLM y validamos en el nodo de Validation

    # ─────────────────────────────────────────────────────────────────
    # PASO 4: Agregar a lista y decidir siguiente paso
    # ─────────────────────────────────────────────────────────────────

    new_meals_completed = [*meals_completed, meal]

    # Emitir progreso
    await copilotkit_emit_state(config, {
        "phase": "recipe_generation",
        "current_meal": meal.model_dump(),
        "meals_completed_count": len(new_meals_completed),
        "total_meals": len(meal_distribution.distribution)
    })

    # Determinar siguiente comida
    meal_names = list(meal_distribution.distribution.keys())
    next_index = current_index + 1

    if next_index >= len(meal_names):
        # Todas las comidas generadas → ir a validación
        return Command(
            goto="validation",
            update={
                "meals_completed": [meal],  # operator.add lo agregará
                "current_meal_index": next_index
            }
        )
    else:
        # Hay más comidas → continuar generando
        next_meal_name = meal_names[next_index]
        next_meal_kcal = meal_distribution.distribution[next_meal_name]

        return Command(
            goto="recipe_generation",
            update={
                "meals_completed": [meal],  # operator.add lo agregará
                "current_meal_index": next_index,
                "current_meal_name": next_meal_name,
                "current_meal_target_kcal": next_meal_kcal
            }
        )


def _normalize_meal_time(meal_name: str) -> Literal["Desayuno", "Almuerzo", "Comida", "Cena"]:
    """Normaliza el nombre de la comida al Literal esperado por Meal."""
    name_lower = meal_name.lower()

    if "desayuno" in name_lower or "brunch" in name_lower:
        return "Desayuno"
    elif "almuerzo" in name_lower or "snack am" in name_lower:
        return "Almuerzo"
    elif "comida" in name_lower or "omad" in name_lower:
        return "Comida"
    else:
        return "Cena"
```

### 5.4 Validation Node

```python
# src/nutrition_agent/nodes/validation.py

from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, END

from copilotkit import copilotkit_emit_message, copilotkit_emit_state

from ..state import NutritionAgentState
from src.rewoo_agent.structured_output_meal import (
    DietPlan,
    Macronutrients,
    ShoppingListItem
)
from shared.tools import sum_total_kcal, sum_ingredients_kcal, consolidate_shopping_list


async def validation_node(
    state: NutritionAgentState,
    config: RunnableConfig
) -> Command[Literal["recipe_generation", "__end__"]]:
    """
    Nodo 4: Valida matemáticamente el plan y genera output final.

    Validaciones:
    1. Suma de calorías de comidas ≈ target (tolerancia 5%)
    2. Cada comida tiene ingredientes válidos
    3. Lista de compras consolidada

    Si hay errores:
    - Marca las comidas problemáticas
    - Vuelve a recipe_generation para regenerar

    Si todo OK:
    - Genera DietPlan final
    - Termina el grafo

    Returns:
        Command con goto=END si válido,
        o goto="recipe_generation" si hay errores.
    """

    nutritional_targets = state["nutritional_targets"]
    meals_completed = state.get("meals_completed", [])
    user_profile = state["user_profile"]

    validation_errors = []
    meals_needing_regeneration = []

    # ─────────────────────────────────────────────────────────────────
    # VALIDACIÓN 1: Suma total de calorías
    # ─────────────────────────────────────────────────────────────────

    meal_kcals = [meal.total_calories for meal in meals_completed]
    total_kcal_result = sum_total_kcal.invoke({"kcals_meals": meal_kcals})

    # Parsear resultado (formato: "X.XX kcal")
    try:
        total_kcal = float(total_kcal_result.replace(" kcal", ""))
    except ValueError:
        total_kcal = sum(meal_kcals)

    target = nutritional_targets.target_calories
    tolerance = 0.05  # 5% de tolerancia

    if abs(total_kcal - target) > (target * tolerance):
        diff = total_kcal - target
        validation_errors.append(
            f"Suma de calorías ({total_kcal:.0f}) difiere del objetivo ({target:.0f}) "
            f"por {diff:.0f} kcal (>{tolerance*100:.0f}% tolerancia)"
        )
        # Marcar la última comida para ajuste
        if meals_completed:
            meals_needing_regeneration.append(meals_completed[-1].meal_time)

    # ─────────────────────────────────────────────────────────────────
    # VALIDACIÓN 2: Verificar cada comida individualmente
    # ─────────────────────────────────────────────────────────────────

    for meal in meals_completed:
        if meal.total_calories <= 0:
            validation_errors.append(f"{meal.meal_time}: Calorías inválidas ({meal.total_calories})")
            meals_needing_regeneration.append(meal.meal_time)

        if not meal.ingredients or len(meal.ingredients) < 1:
            validation_errors.append(f"{meal.meal_time}: Sin ingredientes")
            meals_needing_regeneration.append(meal.meal_time)

    # ─────────────────────────────────────────────────────────────────
    # DECISIÓN: ¿Hay errores críticos?
    # ─────────────────────────────────────────────────────────────────

    if validation_errors and len(meals_needing_regeneration) > 0:
        # Hay errores → notificar y regenerar
        await copilotkit_emit_message(
            config,
            f"Detecté algunos ajustes necesarios: {', '.join(validation_errors[:2])}. "
            "Ajustando el plan..."
        )

        # Remover comidas problemáticas
        cleaned_meals = [
            m for m in meals_completed
            if m.meal_time not in meals_needing_regeneration
        ]

        # Volver a generar
        meal_distribution = state["meal_distribution"]
        meal_names = list(meal_distribution.distribution.keys())

        # Encontrar índice de la primera comida a regenerar
        for i, name in enumerate(meal_names):
            if _normalize_meal_time_reverse(name) in meals_needing_regeneration:
                return Command(
                    goto="recipe_generation",
                    update={
                        "validation_errors": validation_errors,
                        "meals_needing_regeneration": meals_needing_regeneration,
                        "meals_completed": [],  # Reset para evitar duplicados
                        "current_meal_index": i,
                        "current_meal_name": name,
                        "current_meal_target_kcal": meal_distribution.distribution[name]
                    }
                )

        # Fallback: regenerar desde el principio
        first_meal = meal_names[0]
        return Command(
            goto="recipe_generation",
            update={
                "validation_errors": validation_errors,
                "meals_completed": [],
                "current_meal_index": 0,
                "current_meal_name": first_meal,
                "current_meal_target_kcal": meal_distribution.distribution[first_meal]
            }
        )

    # ─────────────────────────────────────────────────────────────────
    # ÉXITO: Generar DietPlan final
    # ─────────────────────────────────────────────────────────────────

    # Consolidar lista de compras
    all_ingredients = []
    for meal in meals_completed:
        all_ingredients.extend(meal.ingredients)

    shopping_result = consolidate_shopping_list.invoke({
        "ingredients_raw": all_ingredients
    })

    # Parsear lista de compras
    shopping_items = []
    for line in shopping_result.split("\n"):
        if line.startswith("- "):
            # Formato: "- 200g de Pechuga De Pollo" o "- Sal"
            item_text = line[2:]  # Remover "- "
            parts = item_text.split(" de ", 1)
            if len(parts) == 2:
                shopping_items.append(ShoppingListItem(
                    quantity=parts[0].strip(),
                    food=parts[1].strip()
                ))
            else:
                shopping_items.append(ShoppingListItem(
                    quantity="Al gusto",
                    food=item_text.strip()
                ))

    # Crear DietPlan
    diet_plan = DietPlan(
        diet_type=f"{nutritional_targets.diet_type_label} - {nutritional_targets.objective_label}",
        total_calories=nutritional_targets.target_calories,
        macronutrients=Macronutrients(
            protein_percentage=nutritional_targets.protein_percentage,
            protein_grams=nutritional_targets.protein_grams,
            carbs_percentage=nutritional_targets.carbs_percentage,
            carbs_grams=nutritional_targets.carbs_grams,
            fat_percentage=nutritional_targets.fat_percentage,
            fat_grams=nutritional_targets.fat_grams
        ),
        daily_meals=meals_completed,
        shopping_list=shopping_items,
        day_identifier=1
    )

    # Emitir plan final
    await copilotkit_emit_state(config, {
        "phase": "complete",
        "final_diet_plan": diet_plan.model_dump()
    })

    await copilotkit_emit_message(
        config,
        f"¡Tu plan está listo! 🎯\n\n"
        f"**{diet_plan.diet_type}**\n"
        f"- Calorías: {diet_plan.total_calories:.0f} kcal\n"
        f"- Proteína: {diet_plan.macronutrients.protein_grams:.0f}g\n"
        f"- Carbohidratos: {diet_plan.macronutrients.carbs_grams:.0f}g\n"
        f"- Grasas: {diet_plan.macronutrients.fat_grams:.0f}g\n\n"
        f"Incluye {len(diet_plan.daily_meals)} comidas y una lista de compras."
    )

    return Command(
        goto=END,
        update={
            "final_diet_plan": diet_plan,
            "validation_errors": []
        }
    )


def _normalize_meal_time_reverse(name: str) -> str:
    """Convierte nombre de distribución a meal_time."""
    name_lower = name.lower()
    if "desayuno" in name_lower or "brunch" in name_lower:
        return "Desayuno"
    elif "almuerzo" in name_lower or "snack am" in name_lower:
        return "Almuerzo"
    elif "comida" in name_lower or "omad" in name_lower:
        return "Comida"
    else:
        return "Cena"
```

---

## 6. Ensamblaje del Grafo

```python
# src/nutrition_agent/graph.py

from langgraph.graph import StateGraph, END

from .state import NutritionAgentState
from .nodes.data_collection import data_collection_node
from .nodes.calculation import calculation_node
from .nodes.recipe_generation import recipe_generation_node
from .nodes.validation import validation_node


def create_nutrition_agent() -> StateGraph:
    """
    Crea el grafo del agente de planificación nutricional.

    Arquitectura: Structured Plan-and-Execute

    Flujo:
    START → data_collection → calculation → recipe_generation (loop) → validation → END

    Returns:
        StateGraph compilado listo para ejecución.
    """

    # Crear grafo con estado tipado
    graph = StateGraph(NutritionAgentState)

    # ─────────────────────────────────────────────────────────────────
    # REGISTRAR NODOS
    # ─────────────────────────────────────────────────────────────────

    graph.add_node("data_collection", data_collection_node)
    graph.add_node("calculation", calculation_node)
    graph.add_node("recipe_generation", recipe_generation_node)
    graph.add_node("validation", validation_node)

    # ─────────────────────────────────────────────────────────────────
    # DEFINIR EDGES
    # ─────────────────────────────────────────────────────────────────

    # Entrada inicial
    graph.set_entry_point("data_collection")

    # Los nodos usan Command(goto=...) para definir transiciones,
    # pero necesitamos registrar los edges posibles:

    # Desde data_collection: puede ir a sí mismo o a calculation
    graph.add_edge("data_collection", "calculation")  # Edge principal
    # El loop a sí mismo se maneja con Command(goto="data_collection")

    # Desde calculation: siempre va a recipe_generation
    graph.add_edge("calculation", "recipe_generation")

    # Desde recipe_generation: puede ir a sí mismo o a validation
    graph.add_edge("recipe_generation", "validation")  # Edge principal
    # El loop a sí mismo se maneja con Command(goto="recipe_generation")

    # Desde validation: puede ir a recipe_generation o a END
    graph.add_edge("validation", END)  # Edge principal
    # El loop a recipe_generation se maneja con Command

    # ─────────────────────────────────────────────────────────────────
    # COMPILAR
    # ─────────────────────────────────────────────────────────────────

    return graph.compile()


# Instancia global para uso en FastAPI
nutrition_agent = create_nutrition_agent()
```

---

## 7. Prompts

### 7.1 Data Collection Prompt

```python
# src/nutrition_agent/prompts/data_collection.py

DATA_COLLECTION_SYSTEM_PROMPT = """Eres un asistente de nutrición que ayuda a crear planes alimenticios personalizados.

Tu tarea es extraer la información del usuario de la conversación para crear su perfil nutricional.

INFORMACIÓN REQUERIDA:
1. age (int): Edad en años (18-100)
2. gender (str): "male" o "female"
3. weight (int): Peso en kilogramos (30-300)
4. height (int): Altura en centímetros (100-250)
5. activity_level (str): Uno de:
   - "sedentary": Poco o nada de ejercicio
   - "lightly_active": Ejercicio ligero 1-3 días/semana
   - "moderately_active": Ejercicio moderado 3-5 días/semana
   - "very_active": Ejercicio fuerte 6-7 días/semana
   - "extra_active": Trabajo físico + entrenamiento
6. objective (str): Uno de:
   - "fat_loss": Perder grasa
   - "muscle_gain": Ganar músculo
   - "maintenance": Mantener peso
7. diet_type (str, opcional): "normal" o "keto" (default: "normal")
8. excluded_foods (list[str], opcional): Alimentos a evitar
9. number_of_meals (int, opcional): Comidas al día (1-6, default: 3)

REGLAS DE EXTRACCIÓN:
- Si el usuario dice "masculino/hombre/varón" → gender: "male"
- Si el usuario dice "femenino/mujer" → gender: "female"
- Si el usuario dice "quiero bajar/perder peso" → objective: "fat_loss"
- Si el usuario dice "quiero subir/ganar peso/masa" → objective: "muscle_gain"
- Si el usuario dice "mantener/mantenerme" → objective: "maintenance"
- Convierte unidades si es necesario (ej: "1.80m" → 180 cm)
- Si no se especifica diet_type, asume "normal"
- Si no se especifica number_of_meals, asume 3

IMPORTANTE:
- Solo extrae información explícitamente mencionada
- No inventes datos que el usuario no haya proporcionado
- Si falta información crítica, la validación fallará y se le preguntará al usuario
"""
```

### 7.2 Recipe Generation Prompt

```python
# src/nutrition_agent/prompts/recipe_generation.py

RECIPE_GENERATION_PROMPT = """Eres un chef nutricionista experto que crea comidas deliciosas y nutritivas.

GENERA UNA COMIDA CON LAS SIGUIENTES ESPECIFICACIONES:

═══════════════════════════════════════════════════════════════
COMIDA: {meal_name}
CALORÍAS OBJETIVO: {target_kcal} kcal
═══════════════════════════════════════════════════════════════

DISTRIBUCIÓN DE MACROS APROXIMADA:
- Proteína: ~{protein_grams}g
- Carbohidratos: ~{carbs_grams}g
- Grasas: ~{fat_grams}g

TIPO DE DIETA: {diet_type}
OBJETIVO DEL USUARIO: {objective}
ALIMENTOS A EVITAR: {excluded_foods}

═══════════════════════════════════════════════════════════════
REGLAS DE GENERACIÓN:
═══════════════════════════════════════════════════════════════

1. TÍTULO: Descriptivo y apetecible (5-150 caracteres)
   Ejemplo: "Huevos revueltos con aguacate y tostada integral"

2. DESCRIPCIÓN: Breve explicación de la comida (10-500 caracteres)
   Ejemplo: "Un desayuno rico en proteínas y grasas saludables, perfecto para mantener la energía durante la mañana."

3. INGREDIENTES: Lista con cantidades en gramos
   Formato: "XXXg de [ingrediente]"
   Ejemplo:
   - "100g de huevo entero"
   - "50g de aguacate"
   - "60g de pan integral"

4. PREPARACIÓN: Pasos numerados, claros y concisos
   Ejemplo:
   - "1. Batir los huevos con sal y pimienta."
   - "2. Cocinar a fuego medio revolviendo constantemente."
   - "3. Servir con el aguacate en rodajas y la tostada."

5. ALTERNATIVA: Una opción de reemplazo (opcional)
   Ejemplo: "Omelette de claras con espinacas"

6. CALORÍAS: Debe ser cercano a {target_kcal} kcal (±50 kcal)

═══════════════════════════════════════════════════════════════
CONSIDERACIONES ESPECIALES:
═══════════════════════════════════════════════════════════════

- Si es DIETA KETO: Prioriza grasas, minimiza carbohidratos (<20g)
- Si OBJETIVO es FAT_LOSS: Prioriza proteína y volumen (verduras)
- Si OBJETIVO es MUSCLE_GAIN: Incluye más carbohidratos complejos
- NUNCA incluyas los alimentos de la lista de exclusión
- Los ingredientes deben ser accesibles en supermercados comunes
- La preparación no debe exceder 30 minutos
"""
```

---

## 8. Código Compartido

### 8.1 Factory de LLMs

```python
# src/shared/llm.py

import os
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(
    model: Literal["gpt-4o", "gpt-4o-mini", "gemini-2.5-flash"] = "gpt-4o",
    temperature: float = 0,
    **kwargs
) -> ChatOpenAI | ChatGoogleGenerativeAI:
    """
    Factory para obtener instancias de LLM con configuración de Helicone.

    Args:
        model: Modelo a usar
        temperature: Temperatura para generación (0 = determinístico)
        **kwargs: Argumentos adicionales para el LLM

    Returns:
        Instancia configurada del LLM
    """

    helicone_api_key = os.getenv("HELICONE_API_KEY")

    if model.startswith("gpt"):
        # OpenAI con Helicone proxy
        base_url = (
            "https://oai.helicone.ai/v1"
            if helicone_api_key
            else None
        )

        default_headers = (
            {"Helicone-Auth": f"Bearer {helicone_api_key}"}
            if helicone_api_key
            else {}
        )

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            base_url=base_url,
            default_headers=default_headers,
            **kwargs
        )

    elif model.startswith("gemini"):
        # Google Gemini
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            **kwargs
        )

    else:
        raise ValueError(f"Modelo no soportado: {model}")
```

### 8.2 Enums Compartidos

```python
# src/shared/enums.py

from enum import StrEnum


class ActivityLevel(StrEnum):
    """Niveles de actividad física estandarizados."""

    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class Objective(StrEnum):
    """Objetivos nutricionales."""

    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class DietType(StrEnum):
    """Tipos de dieta soportados."""

    NORMAL = "normal"
    KETO = "keto"
```

---

## 9. Integración con FastAPI

```python
# src/api/main.py (actualización)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent

# Importar ambos agentes
from src.agent.agent import graph as simple_agent
from src.nutrition_agent.graph import nutrition_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para recursos."""
    # Startup
    print("🚀 Starting Nutrition Agent API...")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Nutrition Agent API",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# COPILOTKIT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

# Endpoint para Simple Agent (testing)
simple_sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="simple_agent",
            description="Agente simple para pruebas de UI",
            graph=simple_agent,
        )
    ]
)

# Endpoint para Nutrition Agent (producción)
nutrition_sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="nutrition_agent",
            description="Agente de planificación nutricional personalizada",
            graph=nutrition_agent,
        )
    ]
)

# Registrar endpoints
add_fastapi_endpoint(app, simple_sdk, "/copilotkit/simple")
add_fastapi_endpoint(app, nutrition_sdk, "/copilotkit/nutrition")

# Endpoint legacy (mantener compatibilidad)
add_fastapi_endpoint(app, simple_sdk, "/copilotkit")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agents": ["simple_agent", "nutrition_agent"]
    }
```

---

## 10. Configuración de langgraph.json

```json
{
  "dependencies": ["."],
  "graphs": {
    "simple_agent": "./src/agent/agent.py:graph",
    "nutrition_agent": "./src/nutrition_agent/graph.py:nutrition_agent"
  },
  "env": ".env"
}
```

---

## 11. Plan de Migración Paso a Paso

### Fase 1: Preparación (Día 1)

```bash
# 1. Crear estructura de directorios
mkdir -p src/nutrition_agent/{nodes,models,prompts}
mkdir -p src/shared
touch src/nutrition_agent/__init__.py
touch src/nutrition_agent/nodes/__init__.py
touch src/nutrition_agent/models/__init__.py
touch src/nutrition_agent/prompts/__init__.py
touch src/shared/__init__.py

# 2. Mover código compartido
cp src/rewoo_agent/nodes/worker/tools.py src/shared/tools.py
# Editar para exportar solo funciones y clases necesarias
```

### Fase 2: Implementación Core (Días 2-3)

1. **Crear modelos** (`src/nutrition_agent/models/`)
   - `user_profile.py`
   - `nutritional_targets.py`

2. **Crear estado** (`src/nutrition_agent/state.py`)

3. **Implementar nodos** (orden recomendado):
   - `calculation.py` (más simple, no usa LLM)
   - `data_collection.py` (critical path)
   - `recipe_generation.py` (más complejo)
   - `validation.py`

4. **Crear grafo** (`src/nutrition_agent/graph.py`)

### Fase 3: Testing (Día 4)

```python
# tests/nutrition_agent/test_calculation.py
import pytest
from src.nutrition_agent.nodes.calculation import calculation_node
from src.nutrition_agent.models.user_profile import UserProfile
from shared.enums import ActivityLevel, Objective, DietType

@pytest.mark.asyncio
async def test_calculation_fat_loss():
    """Verifica cálculo correcto para fat loss."""
    profile = UserProfile(
        age=30,
        gender="male",
        weight=80,
        height=180,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        objective=Objective.FAT_LOSS,
        diet_type=DietType.NORMAL,
        number_of_meals=3
    )

    state = {"user_profile": profile}
    result = await calculation_node(state, {})

    # TDEE aprox para estos datos: ~2500
    # Fat loss (-17%): ~2075
    assert result.update["nutritional_targets"].target_calories < 2200
    assert result.update["nutritional_targets"].target_calories > 1900
```

### Fase 4: Integración (Día 5)

1. **Actualizar FastAPI** (`src/api/main.py`)
2. **Actualizar `langgraph.json`**
3. **Actualizar frontend** (`ui/src/app/layout.tsx`)

```tsx
// ui/src/app/layout.tsx
<CopilotKit
  runtimeUrl="http://localhost:8000/copilotkit/nutrition"
  agent="nutrition_agent"
>
  {children}
</CopilotKit>
```

### Fase 5: Validación A/B (Día 6-7)

1. **Ejecutar ambos agentes** con las mismas entradas
2. **Comparar métricas**:
   - Tokens consumidos (Helicone)
   - Calidad de respuestas (RAGAS)
   - Tiempo de ejecución
3. **Documentar resultados** en `spec/03-migration-results.md`

---

## 12. Checklist de Migración

- [ ] Crear estructura de directorios
- [ ] Mover código compartido a `src/shared/`
- [ ] Implementar `UserProfile` model
- [ ] Implementar `NutritionalTargets` model
- [ ] Implementar `NutritionAgentState`
- [ ] Implementar `calculation_node`
- [ ] Implementar `data_collection_node`
- [ ] Implementar `recipe_generation_node`
- [ ] Implementar `validation_node`
- [ ] Crear prompts
- [ ] Ensamblar grafo
- [ ] Tests unitarios por nodo
- [ ] Actualizar FastAPI
- [ ] Actualizar langgraph.json
- [ ] Actualizar frontend
- [ ] Test E2E completo
- [ ] Comparación A/B con ReWOO
- [ ] Documentar resultados

---

## 13. Notas para Fine-Tuning

### Dataset de Entrenamiento

El nodo `recipe_generation` es el target ideal para fine-tuning. Estructura del dataset:

```jsonl
{"messages": [{"role": "system", "content": "Eres un chef nutricionista..."}, {"role": "user", "content": "Genera un Desayuno: 500 kcal, proteína 30g, objetivo fat_loss"}, {"role": "assistant", "content": "{\"meal_time\": \"Desayuno\", \"title\": \"Huevos con aguacate\", ...}"}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "Genera una Cena: 600 kcal, keto, sin lácteos"}, {"role": "assistant", "content": "{...}"}]}
```

### Proceso de Fine-Tuning

1. **Generar 100-500 ejemplos** usando GPT-4o como "profesor"
2. **Fine-tune GPT-4o-mini** (más económico)
3. **Evaluar con RAGAS** (`answer_correctness`, `answer_similarity`)
4. **Reemplazar en `recipe_generation_node`**:

```python
# Antes
llm = get_llm(model="gpt-4o", temperature=0.7)

# Después
llm = get_llm(model="ft:gpt-4o-mini-2024-07-18:your-org::your-fine-tune-id", temperature=0.7)
```

---

**Fin del Spec Técnico**
