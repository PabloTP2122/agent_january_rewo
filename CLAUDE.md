# Contexto del Proyecto: Agent January ReWOO

Este documento sirve como memoria y contexto para el desarrollo del proyecto. Contiene detalles sobre la arquitectura, el stack tecnologico y el estado actual del sistema.

## 1. Vision General

El proyecto es un sistema de agentes de IA especializado en **planificacion nutricional** que utiliza la arquitectura **ReWOO** (Reasoning WithOut Observation) con LangGraph. El sistema expone estos agentes a traves de un backend FastAPI que se conecta a una interfaz de usuario moderna construida con Next.js y CopilotKit.

### Objetivo Principal
Generar planes alimenticios personalizados con:
- Calculo de TDEE y macronutrientes
- Validacion matematica de calorias
- Busqueda de informacion nutricional via RAG (Pinecone)
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

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Next.js 16 + CopilotKit React Components              │   │
│  │   - CopilotSidebar (Chat UI)                            │   │
│  │   - useCoAgent (Shared State bidireccional)             │   │
│  │   - useCoAgentStateRender (Generative UI)               │   │
│  │   - useFrontendTool (Tools del cliente)                 │   │
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
│  │   - POST /chat_memory/{chat_id} (No implementado)       │   │
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
│  - CopilotKitState      │             │  │  tools y vars #E    │     │
│  - Historial de chat    │             │  └──────────┬──────────┘     │
│  - Frontend actions     │             │             │                │
│                         │             │             ▼                │
│  Modelos soportados:    │             │  ┌─────────────────────┐     │
│  - GPT-4o (OpenAI)      │             │  │     WORKER          │     │
│  - Gemini 2.5 Flash     │             │  │  Ejecuta tools con  │     │
│                         │             │  │  sustitucion #E     │     │
│  Registrado en:         │             │  └──────────┬──────────┘     │
│  langgraph.json         │             │             │                │
│                         │             │             ▼                │
│  Features CopilotKit:   │             │  ┌─────────────────────┐     │
│  - copilotkit_emit_msg  │             │  │     SOLVER          │     │
│  - copilotkit_emit_state│             │  │  Genera DietPlan    │     │
│  - customize_config     │             │  │  estructurado       │     │
└─────────────────────────┘             │  └─────────────────────┘     │
                                        │                              │
                                        │  Nodos Planeados:            │
                                        │  - Reviewer                  │
                                        │  - Documenter                │
                                        │  - Intent Router             │
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
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Pinecone (Vector Store)                               │   │
│  │   - Indice de informacion nutricional                   │   │
│  │   - Embeddings: text-embedding-3-small                  │   │
│  │   - RAG para busqueda de alimentos                      │   │
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
│  │  - Cache        │  │  - Debug        │  │  - Correctness │  │
│  │  - Logs         │  │  - Traces       │  │  - Similarity  │  │
│  │  - Metricas     │  │  - Runs         │  │  - RAG Quality │  │
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
├── agent/                      # Agente Simple (UI Testing)
│   ├── __init__.py
│   ├── agent.py               # StateGraph: START -> agent -> END
│   ├── node.py                # simple_node_agentui con CopilotKit
│   │                          #   - copilotkit_emit_message
│   │                          #   - copilotkit_emit_state
│   │                          #   - copilotkit_customize_config
│   │                          #   - Soporte multi-modelo (OpenAI/Gemini)
│   ├── state.py               # class State(CopilotKitState)
│   └── llm.py                 # get_llm() con Helicone proxy
│
├── rewoo_agent/               # Agente Principal ReWOO
│   ├── __init__.py
│   ├── graph.py               # StateGraph ReWOO (en desarrollo)
│   │                          #   - Carga de entorno
│   │                          #   - Verificacion PINECONE_API_KEY
│   ├── state.py               # ReWOOState con campos:
│   │                          #   - task, user_profile
│   │                          #   - plan_string, steps
│   │                          #   - results (Annotated[dict, operator.update])
│   │                          #   - final_diet_plan (DietPlan)
│   ├── llm.py                 # ChatOpenAI con Helicone proxy
│   ├── structured_output_meal.py  # Modelos Pydantic:
│   │                              #   - DietPlan
│   │                              #   - Meal, Macronutrients
│   │                              #   - BasicMacronutrients
│   │                              #   - ShoppingListItem
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── planner/
│   │   │   ├── __init__.py
│   │   │   ├── node.py        # get_plan(): regex parsing de #E
│   │   │   └── prompt.py      # Prompt de nutricion clinica
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   ├── node.py        # (vacio - en desarrollo)
│   │   │   ├── prompt.py      # (vacio - en desarrollo)
│   │   │   └── tools.py       # 6 herramientas + StrictBaseModel
│   │   │                      #   1. generate_nutritional_plan
│   │   │                      #   2. sum_total_kcal
│   │   │                      #   3. sum_ingredients_kcal
│   │   │                      #   4. get_meal_distribution
│   │   │                      #   5. consolidate_shopping_list
│   │   │                      #   6. calculate_recipe_nutrition (RAG)
│   │   ├── solver/
│   │   │   └── __init__.py    # (planeado)
│   │   ├── reviewer/
│   │   │   └── __init__.py    # (planeado)
│   │   └── documenter/
│   │       └── __init__.py    # (planeado)
│   └── routes/
│       ├── __init__.py
│       └── intent/            # (en desarrollo)
│           ├── __init__.py
│           ├── prompt.py      # (vacio)
│           └── route.py       # (vacio)
│
├── api/
│   └── main.py                # FastAPI app:
│                              #   - CopilotKitRemoteEndpoint
│                              #   - LangGraphAgent
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
    └── __ini__.py             # Modelos compartidos (typo en nombre)
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
└── 00-worker-tools-refactor-plan.md
    # Plan de refactorizacion de tools.py:
    # - Consolidacion DRY (StrictBaseModel)
    # - Limpieza de respuestas
    # - Estandarizacion de idioma
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

| Componente | Estado | Notas |
|------------|--------|-------|
| Simple Agent | **Funcional** | Multi-modelo (OpenAI/Gemini) |
| CopilotKit Integration | **Funcional** | Sidebar + Shared State + Generative UI |
| Frontend Tools | **Funcional** | showNotification implementada |
| PostgreSQL Checkpointer | **Funcional** | Lifespan pattern |
| ReWOO Planner | **En progreso** | Prompt y parsing listos |
| ReWOO Worker | **En progreso** | Tools completas, node vacio |
| ReWOO Graph | **En progreso** | Solo carga de env |
| ReWOO Solver | Planeado | - |
| Intent Router | Planeado | Estructura creada |
| Reviewer/Documenter | Planeado | - |
| RAGAS Evaluations | **Documentado** | Script de ejemplo listo |
| Helicone Observability | **Configurado** | Proxy activo |
| Pinecone RAG | **Funcional** | ResourceLoader singleton |

## 10. Proximos Pasos

1. **Completar Worker Node**: Implementar ejecucion de tools con sustitucion de #E
2. **Implementar Solver**: Generar DietPlan final con structured output
3. **Conectar ReWOO Graph**: Ensamblar StateGraph completo (planner -> worker -> solver)
4. **Implementar Intent Router**: Clasificacion y routing de intenciones
5. **Agregar Evaluaciones RAGAS**: Ejecutar metricas de calidad
6. **Implementar Reviewer**: Validacion de planes generados
7. **Tests de Integracion**: E2E del flujo completo
8. **Corregir typo**: Renombrar `src/models/__ini__.py` a `__init__.py`

## 11. Convenciones

- Mantener separacion clara entre logica del agente (grafos) y capa de exposicion (API)
- Usar Pydantic v2 con `StrictBaseModel` (extra="forbid") para validacion estricta
- Documentar herramientas con descripciones claras para el LLM
- Preferir enums sobre strings para evitar alucinaciones
- Usar Helicone para todas las llamadas LLM en produccion
- Soporte multi-modelo: OpenAI como primario, Google Gemini como fallback
- CopilotKit: Usar hooks avanzados (useCoAgent, useCoAgentStateRender, useFrontendTool)

## 12. Referencias de Codigo

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

### Planner con Regex Parsing
```python
# src/rewoo_agent/nodes/planner/node.py:9
regex_pattern = r"Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*" r"\[([^\]]+)\]"
# Captura: (descripcion, variable, tool, argumentos)
```

### ResourceLoader para RAG
```python
# src/rewoo_agent/nodes/worker/tools.py:447
class ResourceLoader:
    @classmethod
    def get_retriever(cls) -> Any:
        # PineconeVectorStore.from_existing_index()
        # retriever con k=1
```
