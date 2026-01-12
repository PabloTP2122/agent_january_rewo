# Contexto del Proyecto: Agent January ReWOO

Este documento sirve como memoria y contexto para el desarrollo del proyecto. Contiene detalles sobre la arquitectura, el stack tecnologico y el estado actual del sistema.

## 1. Vision General

El proyecto es un sistema de agentes de IA especializado en **planificacion nutricional** que utiliza la arquitectura **ReWOO** (Reasoning WithOut Observation) con LangGraph. El sistema expone estos agentes a traves de un backend FastAPI que se conecta a una interfaz de usuario moderna construida con Next.js y CopilotKit.

### Objetivo Principal
Generar planes alimenticios personalizados con:
- Calculo de TDEE y macronutrientes
- Validacion matematica de calorias
- Busqueda de informacion nutricional via RAG
- Salida estructurada con modelos Pydantic

## 2. Stack Tecnologico

### Backend & AI (`src/`)
| Componente | Tecnologia | Version |
|------------|------------|---------|
| Lenguaje | Python | 3.12 |
| Orquestacion | LangGraph | latest |
| LLM Framework | LangChain | 1.x |
| API | FastAPI | 0.115.x |
| Modelo Principal | OpenAI GPT-4o | - |
| Observabilidad | **Helicone** | Proxy |
| Evaluacion | **RAGAS** | 0.0.19+ |
| Vector Store | ChromaDB | 1.4+ |
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

## 3. Arquitectura del Sistema

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Next.js 16 + CopilotKit React Components              │   │
│  │   - CopilotSidebar (Chat UI)                            │   │
│  │   - runtimeUrl -> NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL    │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   FastAPI Server (src/api/main.py)                      │   │
│  │   Endpoints:                                             │   │
│  │   - POST /copilotkit/* (CopilotKit SDK)                 │   │
│  │   - GET  /health                                         │   │
│  │   - POST /chat_memory/{chat_id}                         │   │
│  │   Middleware: CORS (localhost:3000)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         │                                             │
         ▼                                             ▼
┌─────────────────────────┐             ┌──────────────────────────────┐
│    SIMPLE AGENT         │             │        REWOO AGENT           │
│    (src/agent/)         │             │     (src/rewoo_agent/)       │
│                         │             │                              │
│  Proposito:             │             │  Proposito:                  │
│  Prueba rapida de UI    │             │  Agente principal de         │
│  con CopilotKit         │             │  planificacion nutricional   │
│                         │             │                              │
│  Flujo:                 │             │  Arquitectura ReWOO:         │
│  START -> agent -> END  │             │  ┌─────────────────────┐     │
│                         │             │  │     PLANNER         │     │
│  Estado:                │             │  │  Genera plan con    │     │
│  - MessagesState        │             │  │  tools y vars #E    │     │
│  - Historial de chat    │             │  └──────────┬──────────┘     │
│                         │             │             │                │
│  Modelo:                │             │             ▼                │
│  - GPT-4o via OpenAI    │             │  ┌─────────────────────┐     │
│                         │             │  │     WORKER          │     │
│  Registrado en:         │             │  │  Ejecuta tools con  │     │
│  langgraph.json         │             │  │  sustitucion #E     │     │
│                         │             │  └──────────┬──────────┘     │
└─────────────────────────┘             │             │                │
                                        │             ▼                │
                                        │  ┌─────────────────────┐     │
                                        │  │     SOLVER          │     │
                                        │  │  Genera DietPlan    │     │
                                        │  │  estructurado       │     │
                                        │  └─────────────────────┘     │
                                        │                              │
                                        │  Nodos Planeados:            │
                                        │  - Reviewer                  │
                                        │  - Documenter                │
                                        └──────────────────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   PostgreSQL 15 (Docker)                                │   │
│  │   - langgraph_rewoo database                            │   │
│  │   - PostgresSaver checkpointer                          │   │
│  │   - Persistencia de estado de conversacion              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │    Helicone     │  │    LangSmith    │  │     RAGAS      │  │
│  │  (LLM Proxy)    │  │   (Tracing)     │  │  (Evaluacion)  │  │
│  │                 │  │                 │  │                │  │
│  │  - Cache        │  │  - Debug        │  │  - Faithfulness│  │
│  │  - Logs         │  │  - Traces       │  │  - Relevancy   │  │
│  │  - Metricas     │  │  - Runs         │  │  - Precision   │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Descripcion de ReWOO

ReWOO (Reasoning WithOut Observation) es una arquitectura que separa la planificacion de la ejecucion:

### Componentes

1. **Planner** (`src/rewoo_agent/nodes/planner/`)
   - Genera un plan de alto nivel para resolver el problema
   - Identifica herramientas y argumentos necesarios
   - Usa sustitucion de variables (#E1, #E2, etc.) para dependencias
   - Prompt especializado en nutricion clinica

2. **Worker** (`src/rewoo_agent/nodes/worker/`)
   - Ejecuta herramientas segun el plan
   - Resuelve variables con resultados anteriores
   - 6 herramientas nutricionales disponibles

3. **Solver** (`src/rewoo_agent/nodes/solver/`)
   - Genera respuesta final basada en observaciones
   - Produce DietPlan estructurado (Pydantic v2)

### Sustitucion de Variables

```
Plan: Calcular TDEE del usuario
#E1 = generate_nutritional_plan[age: 30, weight: 80, ...]

Plan: Buscar info nutricional para el 30% de #E1
#E2 = food_facts_search[query: "huevo, aguacate"]

Plan: Verificar suma de ingredientes
#E3 = sum_ingredients_kcal[ingredients: [150, 160], expected: #E1 * 0.3]
```

## 5. Estructura Detallada del Proyecto

### Backend (`src/`)

```
src/
├── agent/                      # Agente Simple (UI Testing)
│   ├── __init__.py
│   ├── agent.py               # StateGraph: START -> agent -> END
│   ├── node.py                # simple_node_agentui con GPT-4o
│   ├── state.py               # class State(MessagesState)
│   └── llm.py                 # get_llm() con Helicone proxy
│
├── rewoo_agent/               # Agente Principal ReWOO
│   ├── __init__.py
│   ├── graph.py               # StateGraph ReWOO (en desarrollo)
│   ├── state.py               # ReWOOState con campos:
│   │                          #   - task, user_profile
│   │                          #   - plan_string, steps
│   │                          #   - results (Annotated dict)
│   │                          #   - final_diet_plan (DietPlan)
│   ├── llm.py                 # ChatOpenAI con Helicone
│   ├── structured_output_meal.py  # Modelos Pydantic:
│   │                              #   - DietPlan
│   │                              #   - Meal, Macronutrients
│   │                              #   - ShoppingListItem
│   └── nodes/
│       ├── __init__.py
│       ├── planner/
│       │   ├── node.py        # get_plan(): regex parsing de #E
│       │   └── prompt.py      # Prompt de nutricion clinica
│       ├── worker/
│       │   ├── node.py        # (vacio - en desarrollo)
│       │   ├── prompt.py      # (vacio - en desarrollo)
│       │   └── tools.py       # 6 herramientas:
│       │                      #   1. generate_nutritional_plan
│       │                      #   2. sum_total_kcal
│       │                      #   3. sum_ingredients_kcal
│       │                      #   4. get_meal_distribution
│       │                      #   5. consolidate_shopping_list
│       │                      #   6. fetch_recipe_nutrition_facts
│       ├── solver/
│       │   └── __init__.py    # (planeado)
│       ├── reviewer/
│       │   └── __init__.py    # (planeado)
│       └── documenter/
│           └── __init__.py    # (planeado)
│
├── api/
│   └── main.py                # FastAPI app:
│                              #   - CopilotKitRemoteEndpoint
│                              #   - LangGraphAGUIAgent
│                              #   - CORS middleware
│                              #   - /health, /chat_memory
│
├── database/
│   ├── __init__.py
│   ├── config.py              # DatabaseSettings (pydantic-settings)
│   │                          #   - POSTGRES_URL computed_field
│   └── session.py             # PostgresSaver lifecycle:
│                              #   - lifespan context manager
│                              #   - CheckpointerDep dependency
│
└── models/
    └── __init__.py            # Modelos compartidos
```

### Frontend (`ui/`)

```
ui/
├── src/app/
│   ├── layout.tsx             # CopilotKit Provider
│   │                          #   - runtimeUrl from env
│   ├── page.tsx               # CopilotSidebar component
│   │                          #   - defaultOpen: true
│   │                          #   - Chat UI integrado
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
└── evaluation/
    └── __init__.py            # Evaluaciones RAGAS (planeado)
```

## 6. Herramientas del Worker

### 1. generate_nutritional_plan
```python
@tool("generate_nutritional_plan", args_schema=NutritionalInput)
def generate_nutritional_plan(
    age: int,           # 18-100
    gender: str,        # male|female
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
    total_calories: float,
    number_of_meals: int  # 1-6
) -> dict[str, float]:
    # Distribuye calorias: Desayuno, Comida, Cena, etc.
```

### 5. consolidate_shopping_list
```python
@tool("consolidate_shopping_list", args_schema=ConsolidateInput)
def consolidate_shopping_list(ingredients_raw: list[str]) -> str:
    # Parsea, normaliza unidades (kg->g), suma duplicados
```

### 6. fetch_recipe_nutrition_facts
```python
@tool("fetch_recipe_nutrition_facts", args_schema=RecipeInput)
def fetch_recipe_nutrition_facts(
    ingredients: list[IngredientInput]
) -> dict[str, Any]:
    # RAG query a vector store (OpenAI File Search)
    # Retorna RecipeAnalysisOutput
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
    title: str
    description: str
    total_calories: float
    ingredients: list[str]
    alternative: str
    preparation: list[str]
```

## 8. Configuracion y Variables de Entorno

### .env requerido
```bash
# LLM
OPENAI_API_KEY=sk-...

# Observabilidad
HELICONE_API_KEY=sk-helicone-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=agent-january
LANGSMITH_TRACING_V2=true

# RAG
VECTOR_STORE_ID=vs_...
PINECONE_API_KEY=pcsk_...

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

| Componente | Estado | Notas |
|------------|--------|-------|
| Simple Agent | Funcional | Registrado en langgraph.json |
| CopilotKit Integration | Funcional | Sidebar + Backend |
| PostgreSQL Checkpointer | Funcional | Lifespan pattern |
| ReWOO Planner | En progreso | Prompt y parsing listos |
| ReWOO Worker | En progreso | Tools definidas, node vacio |
| ReWOO Solver | Planeado | - |
| Reviewer/Documenter | Planeado | - |
| RAGAS Evaluations | Planeado | Estructura creada |
| Helicone Observability | Configurado | Proxy activo |

## 10. Proximos Pasos

1. **Completar Worker Node**: Implementar ejecucion de tools con sustitucion de #E
2. **Implementar Solver**: Generar DietPlan final con structured output
3. **Conectar ReWOO Graph**: Ensamblar StateGraph completo
4. **Agregar Evaluaciones RAGAS**: Metricas de calidad
5. **Implementar Reviewer**: Validacion de planes
6. **Tests de Integracion**: E2E del flujo completo

## 11. Convenciones

- Mantener separacion clara entre logica del agente (grafos) y capa de exposicion (API)
- Usar Pydantic v2 con `model_config = {"extra": "forbid"}` para validacion estricta
- Documentar herramientas con descripciones claras para el LLM
- Preferir enums sobre strings para evitar alucinaciones
- Usar Helicone para todas las llamadas LLM en produccion
