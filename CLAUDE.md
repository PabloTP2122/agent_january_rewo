# Contexto del Proyecto: Agent January - Nutrition Planner

Este documento sirve como memoria y contexto para el desarrollo del proyecto. Contiene detalles sobre la arquitectura, el stack tecnologico y el estado actual del sistema.

## 1. Vision General

El proyecto es un sistema de agentes de IA especializado en **planificacion nutricional** que utiliza la arquitectura **Structured Plan-and-Execute** con LangGraph. El sistema expone estos agentes a traves de un backend FastAPI que se conecta a una interfaz de usuario moderna construida con Next.js y CopilotKit.

> **IMPORTANTE**: El proyecto esta en proceso de **migracion de ReWOO a Plan-and-Execute**.
> Ver `spec/prd.md` para el documento de requisitos completo.

### Objetivo Principal
Generar planes alimenticios personalizados con:
- Recoleccion conversacional del perfil de usuario
- Calculo de TDEE y macronutrientes (determinista, sin LLM)
- Generacion de recetas por comida individual
- Human-in-the-Loop (HITL) para revision por comida
- Validacion matematica de calorias
- Busqueda de informacion nutricional via RAG (Pinecone)
- Salida estructurada con modelos Pydantic

## 1.1 Decision de Arquitectura: ReWOO → Plan-and-Execute

### Evaluacion Comparativa

| Criterio | ReWOO | Plan-and-Execute |
|----------|-------|------------------|
| Manejo de Errores | 2/5 | 5/5 |
| Recoleccion Conversacional | 1/5 | 5/5 |
| Viabilidad Fine-tuning | 3/5 | 5/5 |
| Eficiencia de Tokens | 5/5 | 4/5 |
| Debugging/Mantenibilidad | 2/5 | 4/5 |
| Reactividad | 2/5 | 5/5 |
| Soporte HITL | 3/5 | 4/5 |
| **TOTAL** | **18/35** | **32/35** |

### Problemas Identificados con ReWOO
1. **No reactivo** - No puede ajustar si RAG falla
2. **Sin recoleccion conversacional** - Perfil debe estar completo de entrada
3. **Parsing regex fragil** - Dificil depurar sustitucion `#E1`, `#E2`
4. **Ejecucion todo-o-nada** - Si un paso falla, todo el plan falla
5. **No apto para fine-tuning** - Planner/Executor acoplados

### Ventajas de Plan-and-Execute
1. **Recuperacion por paso** - Puede replanificar ante fallas
2. **Recoleccion integrada** - Extraccion conversacional de UserProfile
3. **Structured outputs** - Sin regex, usa validacion Pydantic
4. **HITL granular** - Revision por comida, no plan completo
5. **Target fine-tuning** - Nodo `recipe_generation` aislado para GPT-4o-mini

## 2. Stack Tecnologico

### Backend & AI (`src/`)
| Componente | Tecnologia | Version |
|------------|------------|---------|
| Lenguaje | Python | 3.12 |
| Orquestacion | LangGraph | latest |
| LLM Framework | LangChain | 1.x |
| API | FastAPI | 0.115.x |
| Modelo Principal | OpenAI GPT-4o | - |
| Modelo Alternativo | Google Gemini 2.5 Flash | - |
| Observabilidad | **Helicone** | Proxy |
| Evaluacion | **RAGAS** | 0.0.19+ |
| Vector Store | **Pinecone** | 0.2.13+ |
| Embeddings | OpenAI text-embedding-3-small | - |
| Persistencia | PostgreSQL | 15 |
| Checkpointing | langgraph-checkpoint-postgres | 2.0+ |
| UI Integration | CopilotKit | 0.1.72 |

### Frontend (`ui/`)
| Componente | Tecnologia | Version |
|------------|------------|---------|
| Framework | Next.js | 16.1.1 |
| Lenguaje | TypeScript | 5.x |
| React | React | 19.2.3 |
| Estilos | Tailwind CSS | 4.x |
| Chat UI | @copilotkit/react-ui | 1.50.1 |
| Core | @copilotkit/react-core | 1.50.1 |
| Runtime | @copilotkit/runtime | 1.50.1 |

## 3. Arquitectura del Sistema

### 3.1 Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Next.js 16 + CopilotKit React Components              │   │
│  │   - CopilotSidebar (Chat UI)                            │   │
│  │   - useCoAgent (Shared State bidireccional)             │   │
│  │   - useCoAgentStateRender (Generative UI)               │   │
│  │   - MealReview.tsx (HITL UI para revision de comidas)   │   │
│  │   - runtimeUrl -> http://localhost:8000/copilotkit      │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
                                │ HTTP/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   FastAPI Server (src/api/main.py)                      │   │
│  │   Endpoints:                                             │   │
│  │   - POST /copilotkit/* (CopilotKit SDK)                 │   │
│  │   - GET  /health                                         │   │
│  │   Middleware: CORS (localhost:3000)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────┐
│  SIMPLE AGENT   │  │  NUTRITION AGENT    │  │   REWOO AGENT      │
│  (src/agent/)   │  │(src/nutrition_agent)│  │ (src/rewoo_agent/) │
│                 │  │     [PRINCIPAL]     │  │    [DEPRECADO]     │
│  Proposito:     │  │                     │  │                    │
│  Testing UI     │  │  Arquitectura:      │  │  Mantener para     │
│                 │  │  Plan-and-Execute   │  │  comparacion A/B   │
│  Flujo:         │  │                     │  │                    │
│  START->END     │  │  5 Nodos:           │  │  Ver seccion 4.2   │
│                 │  │  - data_collection  │  │  para detalles     │
│                 │  │  - calculation      │  │                    │
│                 │  │  - recipe_gen       │  │                    │
│                 │  │  - meal_review(HITL)│  │                    │
│                 │  │  - validation       │  │                    │
└─────────────────┘  └─────────────────────┘  └────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SHARED LAYER (src/shared/)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   tools.py    - 6 herramientas nutricionales            │   │
│  │   enums.py    - ActivityLevel, Objective, DietType      │   │
│  │   llm.py      - Factory LLM con Helicone proxy          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   PostgreSQL 15 (Docker)                                │   │
│  │   - langgraph_rewoo database                            │   │
│  │   - PostgresSaver checkpointer (para HITL recovery)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Pinecone (Vector Store)                               │   │
│  │   - Indice de informacion nutricional                   │   │
│  │   - Embeddings: text-embedding-3-small                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │    Helicone     │  │    LangSmith    │  │     RAGAS      │  │
│  │  (LLM Proxy)    │  │   (Tracing)     │  │  (Evaluacion)  │  │
│  │  - Cache/Logs   │  │  - Debug/Traces │  │  - Correctness │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo del Nutrition Agent (Plan-and-Execute)

```
┌─────────────────┐
│      START      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     missing_fields?
│ data_collection │────────────────────┐
│   (LLM)         │                    │ loop
└────────┬────────┘                    │
         │ complete                    │
         ▼                             │
┌─────────────────┐                    │
│   calculation   │◄───────────────────┘
│ (Determinista)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     more meals?
│recipe_generation│────────────────────┐
│   (LLM)         │                    │
└────────┬────────┘                    │
         │                             │
         ▼                             │
┌─────────────────┐     rejected?      │
│   meal_review   │────────────────────┤
│ (HITL interrupt)│                    │
└────────┬────────┘                    │
         │ approved                    │
         ▼                             │
┌─────────────────┐◄───────────────────┘
│   validation    │
│ (Determinista)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│       END       │
│   (DietPlan)    │
└─────────────────┘
```

## 4. Descripcion de Agentes

### 4.1 Nutrition Agent (PRINCIPAL - Plan-and-Execute)

Ubicacion: `src/nutrition_agent/`

#### Estado de la Implementacion
```python
class NutritionAgentState(CopilotKitState):
    # Fase 1: Recoleccion de Datos
    user_profile: UserProfile | None
    missing_fields: list[str]

    # Fase 2: Calculos
    nutritional_targets: NutritionalTargets | None
    meal_distribution: dict[str, float] | None

    # Fase 3: Generacion de Recetas
    current_meal_index: int
    meals_completed: Annotated[list[Meal], operator.add]

    # Fase 4: HITL Review
    review_decision: Literal["approve", "change", "skip_all"] | None
    user_feedback: str | None
    skip_remaining_reviews: bool
    meals_approved: list[int]

    # Fase 5: Validacion
    validation_errors: list[str]
    final_diet_plan: DietPlan | None
```

#### Nodos del Grafo

| Nodo | Tipo | Descripcion |
|------|------|-------------|
| `data_collection` | LLM | Extrae UserProfile conversacionalmente |
| `calculation` | Determinista | Calcula TDEE, macros, distribucion (sin LLM) |
| `recipe_generation` | LLM | Genera comidas individuales (target fine-tuning) |
| `meal_review` | HITL | Pausa para revision del usuario via `interrupt()` |
| `validation` | Determinista | Verifica calorias, ensambla DietPlan |

#### Modelos Principales

```python
class UserProfile(BaseModel):
    age: int                      # 18-100
    gender: Literal["male", "female"]
    weight: float                 # kg
    height: float                 # cm
    activity_level: ActivityLevel
    objective: Objective
    diet_type: DietType = "normal"
    excluded_foods: list[str] = []
    number_of_meals: int = 3      # 1-6

class NutritionalTargets(BaseModel):
    bmr: float                    # Tasa Metabolica Basal
    tdee: float                   # Gasto Energetico Total
    target_calories: float        # Ajustado por objetivo
    protein_grams: float
    protein_percentage: float
    carbs_grams: float
    carbs_percentage: float
    fat_grams: float
    fat_percentage: float
```

#### HITL (Human-in-the-Loop)

El nodo `meal_review` usa `interrupt()` de LangGraph para pausar el grafo:

```python
# src/nutrition_agent/nodes/meal_review.py
def meal_review(state: NutritionAgentState) -> dict:
    if state.get("skip_remaining_reviews"):
        return {"review_decision": "approve"}

    # Pausa el grafo y espera input del usuario
    decision = interrupt({
        "meal": state["meals_completed"][-1],
        "options": ["approve", "change", "skip_all"]
    })

    return {"review_decision": decision}
```

Frontend con CopilotKit:
```tsx
// ui/src/components/MealReview.tsx
useCoAgentStateRender({
    name: "nutrition_agent",
    render: ({ state }) => {
        if (state.review_decision === null) {
            return <MealReviewCard
                meal={state.meals_completed.at(-1)}
                onApprove={() => /* ... */}
                onChange={(feedback) => /* ... */}
                onSkipAll={() => /* ... */}
            />;
        }
        return null;
    }
});
```

---

### 4.2 ReWOO Agent (LEGACY - Para comparacion A/B)

> **NOTA**: Este agente esta deprecado. Se mantiene para comparacion A/B durante la migracion.

Ubicacion: `src/rewoo_agent/`

ReWOO (Reasoning WithOut Observation) es una arquitectura que separa la planificacion de la ejecucion:

### Componentes

1. **Planner** (`src/rewoo_agent/nodes/planner/`)
   - Genera un plan de alto nivel para resolver el problema
   - Identifica herramientas y argumentos necesarios
   - Usa sustitucion de variables (#E1, #E2, etc.) para dependencias
   - Prompt especializado en nutricion clinica
   - Variables del prompt: `{objetivo}`, `{calorias}`, `{comidas}`, `{alimentacion}`, `{alimento_no_incluir}`

2. **Worker** (`src/rewoo_agent/nodes/worker/`)
   - Ejecuta herramientas segun el plan
   - Resuelve variables con resultados anteriores
   - 6 herramientas nutricionales disponibles
   - Usa `StrictBaseModel` para validacion anti-alucinacion

3. **Solver** (`src/rewoo_agent/nodes/solver/`)
   - Genera respuesta final basada en observaciones
   - Produce DietPlan estructurado (Pydantic v2)

4. **Intent Router** (`src/rewoo_agent/routes/intent/`) - Planeado
   - Clasificacion de intenciones del usuario
   - Routing a flujos especializados

### Sustitucion de Variables

```
Plan: Calcular el gasto energético y macros objetivo.
#E1 = generate_nutritional_plan[age: 30, gender: "male", weight: 80,
height: 180, activity_level: "moderately_active", objective: "fat_loss",
diet_type: "normal"]

Plan: Obtener distribución calórica para 3 comidas.
#E2 = get_meal_distribution[total_calories: #E1.target_calories, number_of_meals: 3]

Plan: Consultar información nutricional de ingredientes del Desayuno.
#E3 = calculate_recipe_nutrition[ingredientes: [
  {nombre: "huevo entero", peso_gramos: 100},
  {nombre: "aguacate", peso_gramos: 50},
  {nombre: "pan integral", peso_gramos: 60}
]]

Plan: Verificar calorías del desayuno contra distribución de #E2.
#E4 = sum_ingredients_kcal[ingredients: #E3.kcals_por_ingrediente,
expected_kcal_sum: #E2.Desayuno]

Plan: (Repetir #E3 y #E4 para Comida y Cena...)

Plan: Verificar suma total de comidas contra objetivo de #E1.
#E9 = sum_total_kcal[kcals_meals: [#E4, #E6, #E8]]

Plan: Consolidar ingredientes en lista de compras.
#E10 = consolidate_shopping_list[ingredients_raw: ["200g huevo", "50g aguacate", ...]]
```

## 5. Estructura Detallada del Proyecto

### Backend (`src/`)

```
src/
├── __init__.py
│
├── shared/                     # [NUEVO] Codigo compartido entre agentes
│   ├── __init__.py
│   ├── tools.py               # 6 herramientas nutricionales (migradas)
│   ├── enums.py               # ActivityLevel, Objective, DietType
│   └── llm.py                 # Factory LLM con Helicone proxy
│
├── nutrition_agent/           # [PRINCIPAL] Agente Plan-and-Execute
│   ├── __init__.py
│   ├── graph.py               # StateGraph con 5 nodos + edges
│   ├── state.py               # NutritionAgentState(CopilotKitState)
│   ├── llm.py                 # Configuracion LLM especifica
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_profile.py    # UserProfile model
│   │   ├── nutritional_targets.py  # NutritionalTargets model
│   │   └── diet_plan.py       # DietPlan, Meal, Macronutrients
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── data_collection.py # Extraccion conversacional UserProfile
│   │   ├── calculation.py     # TDEE/Macros (determinista, sin LLM)
│   │   ├── recipe_generation.py # Generacion de Meal (LLM, fine-tuning target)
│   │   ├── meal_review.py     # HITL con interrupt()
│   │   └── validation.py      # Verificacion matematica + DietPlan
│   └── prompts/
│       ├── __init__.py
│       ├── data_collection.py # Prompt extraccion UserProfile
│       └── recipe_generation.py # Prompt generacion Meal
│
├── agent/                      # Agente Simple (UI Testing)
│   ├── __init__.py
│   ├── agent.py               # StateGraph: START -> agent -> END
│   ├── node.py                # simple_node_agentui con CopilotKit
│   ├── state.py               # class State(CopilotKitState)
│   └── llm.py                 # get_llm() con Helicone proxy
│
├── rewoo_agent/               # [DEPRECADO] Agente ReWOO (para A/B testing)
│   ├── __init__.py
│   ├── graph.py               # StateGraph ReWOO
│   ├── state.py               # ReWOOState
│   ├── llm.py                 # ChatOpenAI con Helicone proxy
│   ├── structured_output_meal.py  # Modelos Pydantic originales
│   ├── nodes/
│   │   ├── planner/           # Funcional: regex parsing #E
│   │   ├── worker/            # tools.py completo, node.py vacio
│   │   ├── solver/            # Planeado
│   │   ├── reviewer/          # Planeado
│   │   └── documenter/        # Planeado
│   └── routes/intent/         # En desarrollo
│
├── api/
│   └── main.py                # FastAPI app:
│                              #   - CopilotKitRemoteEndpoint
│                              #   - LangGraphAgent (nutrition_agent)
│                              #   - CORS middleware
│                              #   - /health endpoint
│
├── database/
│   ├── __init__.py
│   ├── config.py              # DatabaseSettings (pydantic-settings)
│   └── session.py             # PostgresSaver lifecycle (HITL recovery)
│
└── models/
    └── __init__.py            # Modelos compartidos
```

### Frontend (`ui/`)

```
ui/
├── src/app/
│   ├── layout.tsx             # CopilotKit Provider
│   │                          #   - runtimeUrl hardcodeado
│   │                          #   - agent="simple_agent"
│   ├── page.tsx               # Pagina principal con:
│   │                          #   - useCoAgent (shared state)
│   │                          #   - useCoAgentStateRender (generative UI)
│   │                          #   - useFrontendTool (showNotification)
│   │                          #   - CopilotSidebar
│   ├── globals.css            # Tailwind styles
│   └── favicon.ico
├── package.json               # Deps: copilotkit, next, react
└── next.config.ts
```

### Tests (`tests/`)

```
tests/
├── __init__.py
├── tools/
│   ├── __init__.py
│   └── test_generate_nutritional_plan.py
│       # - test_muscle_gain_calculation
│       # - test_invalid_enum_raises_error
│       # - test_edge_case_negative_carbs
├── quick_tool_tests/
│   ├── __init__.py
│   └── calculate_recipe_nutrition_test.py
│       # - Test rapido de la herramienta RAG
│       # - Casos: alimento existente + ficticio
└── evaluation/
    ├── __init__.py
    └── eval_fetch_recipe_nutrition_facts.py
        # Documentacion de evaluacion RAGAS:
        # - answer_correctness
        # - answer_similarity
        # - Ground truth dataset
```

### Especificaciones (`spec/`)

```
spec/
├── prd.md                      # PRD completo de la migracion
├── 00-worker-tools-refactor-plan.md
│   # Plan de refactorizacion de tools.py
├── 01-architecture-analysis-rewoo-vs-alternatives.md
│   # Analisis arquitectonico (ReWOO vs Plan-and-Execute vs ReAct)
├── 01-architecture-decision-tree.md
│   # Arbol de decision para seleccion de arquitectura
├── 02-implementation-examples.md
│   # Ejemplos de codigo para Plan-and-Execute y ReAct
├── 02-migration-implementation-plan.md
│   # Plan detallado de migracion tecnica
├── 03-agregar-HITL.md
│   # Especificacion de Human-in-the-Loop
└── flujo-grafo-detail.md
    # Documentacion detallada del flujo del grafo
```

## 6. Herramientas del Worker

### StrictBaseModel (Anti-Alucinacion)
```python
class StrictBaseModel(BaseModel):
    """Base para todos los schemas de input de tools."""
    model_config = {"extra": "forbid"}
```

### 1. generate_nutritional_plan
```python
@tool("generate_nutritional_plan", args_schema=NutritionalInput)
def generate_nutritional_plan(
    age: int,           # 18-100
    gender: str,        # male|female|masculine|feminine
    weight: int,        # 30-300 kg
    height: int,        # 100-250 cm
    activity_level: ActivityLevel,  # sedentary -> extra_active
    objective: Objective,           # fat_loss|muscle_gain|maintenance
    diet_type: DietType = "normal"  # normal|keto
) -> str:
    # Calcula TMB (Mifflin-St Jeor), TDEE, Macros
```

### 2. sum_total_kcal
```python
@tool("sum_total_kcal", args_schema=SumTotalInput)
def sum_total_kcal(kcals_meals: list[float]) -> str:
    # Suma lista de calorias
```

### 3. sum_ingredients_kcal
```python
@tool("sum_ingredients_kcal", args_schema=VerifyIngredientsInput)
def sum_ingredients_kcal(
    ingredients: list[float],
    expected_kcal_sum: float
) -> str:
    # Verifica suma con tolerancia 0.5 kcal
```

### 4. get_meal_distribution
```python
@tool("get_meal_distribution", args_schema=MealDistInput)
def get_meal_distribution(
    total_calories: float,  # 500-10000
    number_of_meals: int    # 1-6
) -> dict[str, float]:
    # Distribuye calorias: Desayuno, Comida, Cena, etc.
    # Patrones predefinidos para 1-6 comidas
```

### 5. consolidate_shopping_list
```python
@tool("consolidate_shopping_list", args_schema=ConsolidateInput)
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    # Parsea regex, normaliza unidades (kg->g, l->ml), suma duplicados
```

### 6. calculate_recipe_nutrition (RAG)
```python
@tool("calculate_recipe_nutrition", args_schema=RecipeAnalysisInput)
async def calculate_recipe_nutrition(
    ingredientes: list[IngredientInput]
) -> dict:
    # RAG query a Pinecone vector store
    # Usa ResourceLoader singleton
    # Retorna NutritionResult con ProcessedItem list
```

#### ResourceLoader (Singleton para conexiones RAG)
```python
class ResourceLoader:
    _retriever = None
    _extractor_llm = None

    @classmethod
    def get_retriever(cls) -> Any:
        # PineconeVectorStore con text-embedding-3-small
        # search_kwargs={"k": 1}

    @classmethod
    def get_extractor_chain(cls) -> RunnableSerializable:
        # ChatOpenAI gpt-4o-mini con structured output NutriFacts
```

## 7. Modelos de Salida Estructurada

### DietPlan (Modelo Principal)
```python
class DietPlan(BaseModel):
    diet_type: str              # "Alta en Proteina", "Cetogenica"
    total_calories: float       # 500-10000
    macronutrients: Macronutrients
    daily_meals: list[Meal]     # 1-7 comidas
    shopping_list: list[ShoppingListItem]
    day_identifier: int         # Dia del plan
```

### Meal
```python
class Meal(BaseModel):
    meal_time: Literal["Desayuno", "Almuerzo", "Comida", "Cena"]
    title: str                  # 5-150 chars
    description: str            # 10-500 chars
    total_calories: float       # 0-2000
    ingredients: list[str]      # Con cantidad en g
    alternative: str            # Opcional
    preparation: list[str]      # Pasos numerados
```

### Macronutrients
```python
class Macronutrients(BaseModel):
    protein_percentage: float   # 0-100
    protein_grams: float
    carbs_percentage: float     # 0-100
    carbs_grams: float
    fat_percentage: float       # 0-100
    fat_grams: float
```

### BasicMacronutrients (Version simplificada)
```python
class BasicMacronutrients(BaseModel):
    protein_percentage: float
    protein_grams: float
    carbs_percentage: float
    fat_percentage: float
    # Sin *_grams para carbs y fat
```

## 8. Configuracion y Variables de Entorno

### .env requerido
```bash
# LLM (al menos una requerida)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...          # Alternativa para Gemini

# Observabilidad
HELICONE_API_KEY=sk-helicone-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=agent-january
LANGSMITH_TRACING_V2=true

# RAG (Pinecone)
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=...
EMBEDDING_MODEL=text-embedding-3-small  # Opcional

# Database
POSTGRES_DB=langgraph_rewoo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432

# Search
TAVILY_API_KEY=tvly-...
```

## 9. Estado Actual del Desarrollo

### 9.1 Infraestructura Compartida

| Componente | Estado | Notas |
|------------|--------|-------|
| Simple Agent | **Funcional** | Multi-modelo (OpenAI/Gemini) |
| CopilotKit Integration | **Funcional** | Sidebar + Shared State + Generative UI |
| PostgreSQL Checkpointer | **Funcional** | Lifespan pattern, HITL recovery |
| Helicone Observability | **Configurado** | Proxy activo |
| Pinecone RAG | **Funcional** | ResourceLoader singleton |
| RAGAS Evaluations | **Documentado** | Script de ejemplo listo |

### 9.2 Nutrition Agent (Plan-and-Execute) - PRINCIPAL

| Componente | Estado | Notas |
|------------|--------|-------|
| Estructura directorios | **Creada** | Scaffolding completo |
| state.py | Pendiente | NutritionAgentState |
| graph.py | Pendiente | StateGraph con 5 nodos |
| models/user_profile.py | Pendiente | UserProfile model |
| models/nutritional_targets.py | Pendiente | NutritionalTargets model |
| models/diet_plan.py | Pendiente | Migrar de rewoo_agent |
| nodes/data_collection.py | Pendiente | Extraccion conversacional |
| nodes/calculation.py | Pendiente | TDEE/Macros determinista |
| nodes/recipe_generation.py | Pendiente | LLM meal generation |
| nodes/meal_review.py | Pendiente | HITL con interrupt() |
| nodes/validation.py | Pendiente | Verificacion matematica |
| prompts/ | Pendiente | Prompts para LLM nodes |
| src/shared/tools.py | Pendiente | Migrar de rewoo_agent |
| src/shared/enums.py | Pendiente | ActivityLevel, Objective, etc. |
| ui/MealReview.tsx | Pendiente | Componente HITL UI |

### 9.3 ReWOO Agent - DEPRECADO (Para A/B Testing)

| Componente | Estado | Notas |
|------------|--------|-------|
| ReWOO Planner | **Funcional** | Prompt y regex parsing listos |
| ReWOO Worker Tools | **Funcional** | 6 herramientas completas |
| ReWOO Worker Node | Incompleto | Node vacio |
| ReWOO Solver | Incompleto | Estructura solo |
| ReWOO Graph | Incompleto | Solo carga de env |

## 10. Proximos Pasos (Roadmap de Migracion)

### Fase 1: Fundacion (Dia 1)
- [ ] Crear `src/shared/` directory
- [ ] Mover tools de `rewoo_agent/nodes/worker/tools.py` a `shared/tools.py`
- [ ] Crear `shared/enums.py` con ActivityLevel, Objective, DietType
- [ ] Crear `shared/llm.py` con factory Helicone

### Fase 2: Modelos (Dia 2)
- [ ] Implementar `models/user_profile.py`
- [ ] Implementar `models/nutritional_targets.py`
- [ ] Migrar `models/diet_plan.py` (DietPlan, Meal, Macronutrients)
- [ ] Implementar `state.py` (NutritionAgentState)

### Fase 3: Nodos Core (Dias 3-4)
- [ ] Implementar `nodes/calculation.py` (determinista)
- [ ] Implementar `nodes/data_collection.py` + prompt
- [ ] Implementar `nodes/recipe_generation.py` + prompt

### Fase 4: HITL & Validacion (Dia 5)
- [ ] Implementar `nodes/meal_review.py` (interrupt-based)
- [ ] Implementar `nodes/validation.py`
- [ ] Ensamblar `graph.py` (StateGraph con edges)

### Fase 5: Integracion (Dia 6)
- [ ] Actualizar `src/api/main.py` para registrar nutrition_agent
- [ ] Actualizar `langgraph.json`
- [ ] Actualizar frontend (agent name, MealReview.tsx)

### Fase 6: Testing & Evaluacion (Dia 7)
- [ ] Unit tests por nodo
- [ ] Integration test (flujo completo)
- [ ] Comparacion A/B: ReWOO vs Plan-and-Execute
- [ ] Setup evaluacion RAGAS

## 11. Convenciones

### Arquitectura
- Mantener separacion clara entre logica del agente (grafos) y capa de exposicion (API)
- Codigo compartido va en `src/shared/` (tools, enums, llm)
- Cada agente tiene su propio directorio con estructura consistente

### Validacion & Anti-Alucinacion
- Usar Pydantic v2 con `StrictBaseModel` (extra="forbid") para validacion estricta
- Preferir enums sobre strings para evitar alucinaciones
- Documentar herramientas con descripciones claras para el LLM

### LLM & Observabilidad
- Usar Helicone para todas las llamadas LLM en produccion
- Soporte multi-modelo: OpenAI como primario, Google Gemini como fallback
- GPT-4o para desarrollo, GPT-4o-mini como target de fine-tuning

### CopilotKit
- Usar hooks avanzados (useCoAgent, useCoAgentStateRender)
- HITL via `interrupt()` en backend + `renderAndWait` en frontend
- State compartido bidireccional entre frontend y backend

### Plan-and-Execute Especificas
- Nodos deterministas (calculation, validation) NO usan LLM
- Nodos LLM (data_collection, recipe_generation) usan structured output
- El nodo `recipe_generation` es el target para fine-tuning
- HITL debe ofrecer opcion "Approve All" para evitar N pausas

## 12. Referencias de Codigo

### Nutrition Agent - Data Collection (Plan-and-Execute)
```python
# src/nutrition_agent/nodes/data_collection.py (propuesto)
async def data_collection(state: NutritionAgentState) -> dict:
    if state.get("user_profile"):
        return {}  # Ya completo, saltar

    llm = get_llm().with_structured_output(UserProfile)
    result = await llm.ainvoke([
        SystemMessage(DATA_COLLECTION_PROMPT),
        *state["messages"]
    ])
    return {"user_profile": result, "missing_fields": []}
```

### Nutrition Agent - HITL Interrupt
```python
# src/nutrition_agent/nodes/meal_review.py (propuesto)
from langgraph.types import interrupt

def meal_review(state: NutritionAgentState) -> dict:
    if state.get("skip_remaining_reviews"):
        return {"review_decision": "approve"}

    decision = interrupt({
        "meal": state["meals_completed"][-1],
        "options": ["approve", "change", "skip_all"]
    })
    return {"review_decision": decision}
```

### Simple Agent Node con CopilotKit
```python
# src/agent/node.py:47
async def simple_node_agentui(state: State, config: RunnableConfig) -> Command[str]:
    frontend_tools = state.get("copilotkit", {}).get("actions", [])
    all_tools = [*backend_tools, *frontend_tools]
    model = llm.bind_tools(all_tools) if all_tools else llm
    response = await model.ainvoke([SystemMessage(...), *state["messages"]], config)
    return Command(goto=END, update={"messages": [response]})
```

### ResourceLoader para RAG (src/shared/)
```python
# src/shared/tools.py (despues de migracion)
class ResourceLoader:
    @classmethod
    def get_retriever(cls) -> Any:
        # PineconeVectorStore.from_existing_index()
        # retriever con k=1
```

## 13. Documentacion de Referencia

| Documento | Ubicacion | Contenido |
|-----------|-----------|-----------|
| PRD Completo | `spec/prd.md` | Requisitos, arquitectura, plan de implementacion |
| Analisis Arquitectonico | `spec/01-architecture-analysis-rewoo-vs-alternatives.md` | Comparacion detallada |
| Ejemplos de Codigo | `spec/02-implementation-examples.md` | Implementaciones de referencia |
| Especificacion HITL | `spec/03-agregar-HITL.md` | Detalle de Human-in-the-Loop |
| Flujo del Grafo | `spec/flujo-grafo-detail.md` | Diagramas y transiciones |
