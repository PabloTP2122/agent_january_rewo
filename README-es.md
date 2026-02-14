<div align="right">
  <a href="README.md">English</a> | <a href="README-es.md"><strong>Español</strong></a>
</div>

# Nutrition Agent — Planificacion Nutricional con IA y LangGraph

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-purple)
![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)

Agente de IA para planificacion nutricional que genera planes alimenticios personalizados mediante recoleccion conversacional de datos, calculo determinista de macronutrientes y generacion paralela de recetas — con validacion automatizada y revision humana (HITL).

### Puntos Clave

- **Arquitectura Plan-and-Execute** con 6 nodos especializados y 3 edges condicionales
- **Generacion paralela en batch** via `asyncio.gather()` (~60% reduccion de latencia vs secuencial)
- **Validacion antes de HITL** — verificacion automatica de calorias con auto-retry antes de la revision humana
- **Salida estructurada** con seguimiento de calorias por ingrediente (modelo `Ingredient` con campo `kcal`)
- **Datos nutricionales via RAG** con Pinecone como vector store
- **56 tests unitarios** en 10 archivos + framework de evaluacion RAGAS
- **27 componentes React** en 5 categorias con desarrollo mock-first
- **Protocolo AG-UI** para streaming del estado del agente al frontend en tiempo real

## Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Flujo del Grafo](#flujo-del-grafo)
- [Decisiones de Diseno Clave](#decisiones-de-diseno-clave)
- [Evolucion Arquitectonica](#evolucion-arquitectonica)
- [Stack Tecnologico](#stack-tecnologico)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Testing y Calidad](#testing-y-calidad)
- [Inicio Rapido](#inicio-rapido)
- [Estado del Desarrollo](#estado-del-desarrollo)
- [Licencia](#licencia)

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│   Next.js 16 · CopilotKit · 27 Componentes React               │
│   Vista dividida (Chat 34% + Canvas 66%) · Responsive           │
│   runtimeUrl → http://localhost:8123/                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │ Protocolo AG-UI (streaming)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                        CAPA API                                  │
│   FastAPI (puerto 8123) · Bridge ag-ui-langgraph                │
│   LangGraphAGUIAgent("nutrition_agent") · CORS                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NUTRITION AGENT                                │
│   Plan-and-Execute · 6 Nodos · 3 Edges Condicionales            │
│                                                                  │
│   data_collection ──► calculation ──► recipe_gen_batch           │
│        (LLM)          (determinista)    (LLM, paralelo)         │
│                                              │                   │
│                                              ▼                   │
│                                         validation               │
│                                        (determinista)            │
│                                              │                   │
│                              ┌───────────────┤                   │
│                              ▼               ▼                   │
│                      recipe_gen_single   meal_review_batch       │
│                         (LLM)              (HITL)               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │ Pinecone │ │ Helicone │
        │Checkpoint│ │   RAG    │ │LLM Proxy │
        └──────────┘ └──────────┘ └──────────┘
```

## Flujo del Grafo

El agente de nutricion usa una arquitectura Plan-and-Execute con routing condicional basado en resultados de validacion y feedback del usuario:

```
    START → data_collection ←──┐ (loop si faltan campos)
                │               │
                ▼               │
           calculation ─────────┘
                │
                ▼
    recipe_generation_batch ◄──────────────────┐
                │                              │
                ▼                              │
           validation ─────────────────────────┤ (N fallos → regen batch)
                │           │                  │
                │      (1 fallo)               │
                │           ↓                  │
                │   recipe_generation_single ──┘
                │
                ▼  (pasa / retries ≥ 2)
       meal_review_batch (HITL interrupt)
                │
        ┌───────┼──────────────────────┐
        │       │                      │
     aprobar  cambiar_comida     regenerar_todo
        │       ↓                      │
        ▼   recipe_gen_single    recipe_gen_batch
       END
```

**Detalle de nodos:**

| Nodo | Tipo | Proposito |
|------|------|-----------|
| `data_collection` | LLM | Extraccion conversacional del `UserProfile` via structured output |
| `calculation` | Determinista | TDEE, macros, distribucion de comidas via tools co-localizadas (sin LLM) |
| `recipe_generation_batch` | LLM | Generacion paralela de todas las comidas via `asyncio.gather()` |
| `recipe_generation_single` | LLM | Regeneracion dirigida de una comida (fix de validacion o solicitud del usuario) |
| `validation` | Determinista | Verificacion de calorias por comida + global, generacion de `MealNotice`, routing |
| `meal_review_batch` | HITL | Pausa con `interrupt()` para revision humana del plan completo |

## Decisiones de Diseno Clave

| # | Decision | Justificacion |
|---|----------|---------------|
| 1 | **Validacion antes de HITL** | Los humanos solo revisan comidas validadas — reduce ciclos de feedback. Auto-retry (max 2) con regeneracion dirigida antes de presentar al usuario. |
| 2 | **Generacion paralela en batch** | N-1 comidas generadas via `asyncio.gather()`, ultima secuencial para cerrar el presupuesto calorico. ~60% reduccion de latencia vs generacion secuencial. |
| 3 | **Modelo `Ingredient` estructurado** | `Ingredient(nombre, cantidad_display, peso_gramos, kcal)` reemplaza `list[str]` — permite validacion por ingrediente sin parsing regex. |
| 4 | **Sistema `MealNotice`** | Feedback de validacion por comida con niveles de severidad (warning: 2-5% desviacion, error: >5%) — feedback granular en vez de pasa/no pasa. |
| 5 | **Co-localizacion de tools** | Cada tool vive junto al nodo que la consume (`nodes/calculation/tools.py`) en vez de un monolitico `shared/tools.py` — mejor cohesion, testing mas facil, ownership claro. |
| 6 | **`StrictBaseModel` para schemas de tools** | `extra="forbid"` en todos los schemas de input — previene alucinacion de campos extra por el LLM. |
| 7 | **Nodos deterministas para matematicas** | Los nodos de calculo y validacion no usan LLM — las operaciones matematicas son demasiado importantes para delegar a modelos probabilisticos. |

## Evolucion Arquitectonica

Este proyecto comenzo con la arquitectura **ReWOO** (Reasoning WithOut Observation) y fue migrado a **Plan-and-Execute** tras identificar limitaciones fundamentales:

| Criterio | ReWOO | Plan-and-Execute |
|----------|:-----:|:----------------:|
| Recuperacion de Errores | 2/5 | 5/5 |
| Recoleccion Conversacional | 1/5 | 5/5 |
| Soporte HITL | 3/5 | 4/5 |
| Viabilidad de Fine-tuning | 3/5 | 5/5 |
| Debuggability | 2/5 | 4/5 |
| Reactividad | 2/5 | 5/5 |
| Eficiencia de Tokens | 5/5 | 4/5 |
| **Total** | **18/35** | **32/35** |

**Por que ReWOO no funciono:**
- **No reactivo** — no podia ajustar si las queries RAG fallaban a mitad del plan
- **Sin recoleccion conversacional** — requeria perfil de usuario completo de entrada
- **Parsing regex fragil** — la sustitucion de variables `#E1`, `#E2` era dificil de debuggear
- **Ejecucion todo-o-nada** — un fallo en un paso mataba todo el plan

El agente ReWOO se preserva en `src/rewoo_agent/` para comparacion A/B. El analisis arquitectonico completo esta documentado en [`spec/01-architecture-analysis-rewoo-vs-alternatives.md`](spec/01-architecture-analysis-rewoo-vs-alternatives.md).

## Stack Tecnologico

### Backend

| Tecnologia | Version | Por que |
|------------|---------|---------|
| Python | 3.12 | Type hints, `asyncio`, pattern matching |
| LangGraph | latest | Grafos de agentes con estado, routing condicional y HITL via `interrupt()` |
| FastAPI | 0.115.x | API async con patron lifespan para gestion de conexiones DB |
| Protocolo AG-UI | ≥0.0.21 | Streaming del estado del agente al frontend via bridge CopilotKit |
| Pydantic v2 | latest | Validacion estricta con `StrictBaseModel` (anti-alucinacion) |
| Pinecone | ≥0.2.13 | Vector store para queries RAG de datos nutricionales |
| PostgreSQL | 15 | Persistencia de estado HITL via `langgraph-checkpoint-postgres` |
| Helicone | proxy | Observabilidad LLM, cache de respuestas, tracking de costos |
| OpenAI GPT-4o | primario | LLM principal para generacion de structured output |

### Frontend

| Tecnologia | Version | Por que |
|------------|---------|---------|
| Next.js | 16.1.6 | App Router, React 19, server components |
| CopilotKit | ^1.50.1 | Protocolo AG-UI, `useCoAgent`, `useLangGraphInterrupt` |
| TypeScript | ^5 | Tipos estrictos que espejean modelos Pydantic de Python exactamente |
| React Hook Form + Zod | latest | Validacion de formularios que coincide con constraints de Python |
| Tailwind CSS | ^4 | Layout responsive 66/34 con toggle para movil |

### Calidad y Observabilidad

| Herramienta | Proposito |
|-------------|-----------|
| Ruff | Linting — reglas E, F, UP, B, SIM, I, S |
| mypy (strict) | Chequeo de tipos estatico con `disallow_untyped_defs` |
| pytest | 56 tests unitarios en 10 archivos |
| RAGAS | Evaluacion de salidas LLM (faithfulness, answer relevancy) |
| pre-commit | Gates de calidad automatizados antes de cada commit |
| LangSmith | Tracing y debugging de ejecucion del agente |
| Helicone | Logging de requests/responses LLM con cache |

## Estructura del Proyecto

```
src/
├── nutrition_agent/              # Agente principal (Plan-and-Execute)
│   ├── graph.py                  # StateGraph: 6 nodos, 3 edges condicionales
│   ├── state.py                  # NutritionAgentState (14 campos)
│   ├── models/
│   │   ├── user_profile.py       # UserProfile (edad, genero, peso, altura...)
│   │   ├── nutritional_targets.py # NutritionalTargets (TDEE, macros)
│   │   ├── diet_plan.py          # DietPlan, Meal, Ingredient, MealNotice
│   │   └── tools.py              # Schemas de tools con StrictBaseModel
│   ├── nodes/
│   │   ├── data_collection/      # LLM: extraccion conversacional del perfil
│   │   ├── calculation/          # Determinista: TDEE + macros + tools
│   │   ├── recipe_generation/    # LLM: batch + single + tool RAG
│   │   ├── validation/           # Determinista: verificacion calorica + tools
│   │   └── meal_review/          # HITL: revision batch con interrupt()
│   └── prompts/                  # Templates de prompts LLM
│
├── shared/                       # Utilidades transversales
│   ├── tools.py                  # sum_ingredients_kcal (validacion compartida)
│   ├── enums.py                  # ActivityLevel, Objective, DietType, MealTime
│   └── llm.py                   # Factory LLM con proxy Helicone
│
├── api/main.py                   # FastAPI + bridge ag-ui-langgraph (puerto 8123)
├── database/                     # Ciclo de vida del checkpointer PostgreSQL
└── agent/                        # Agente simple (testing de UI)

ui/                               # Frontend Next.js 16
├── components/
│   ├── canvas/    (7)            # DietPlanCanvas, MealCard, MacrosTable...
│   ├── forms/     (3)            # UserProfileForm, ExcludedFoodInput...
│   ├── hitl/      (4)            # MealPlanReview, MealReviewCard...
│   ├── layout/    (4)            # MainLayout, Canvas, ChatPanel...
│   └── ui/        (9)            # Button, Card, Badge, Spinner...
├── hooks/         (3)            # useAgentPhase, useMockData, useMediaQuery
└── lib/                          # types.ts, validations.ts, config.ts

tests/
├── tools/         (7 archivos)   # Tests unitarios para todas las tools
├── nodes/         (1 archivo)    # Tests del nodo de validacion (20+ casos)
├── quick_tool_tests/ (2 archivos)# Smoke tests RAG + calculo
└── evaluation/                   # Scripts RAGAS + datasets ground truth
```

## Testing y Calidad

**56 funciones de test** en 10 archivos cubriendo:

- **Tests unitarios de tools** (7 archivos) — `generate_nutritional_plan`, `get_meal_distribution`, `sum_ingredients_kcal`, `sum_total_kcal`, `consolidate_shopping_list`, `calculate_recipe_nutrition`
- **Tests del nodo de validacion** (20+ casos) — presupuesto calorico por comida, verificacion de total global, generacion de `MealNotice`, logica de routing hints, consolidacion de lista de compras, casos edge
- **Smoke tests** — integracion de tool RAG, nodo de calculo end-to-end
- **Evaluacion RAGAS** — `answer_correctness`, `answer_similarity` con datasets ground truth

**Pipeline anti-alucinacion:**
1. `StrictBaseModel` (`extra="forbid"`) en todos los schemas de input de tools
2. Constraints con enums para `ActivityLevel`, `Objective`, `DietType`, `MealTime`, `Gender`
3. Structured output Pydantic v2 para todos los nodos LLM
4. Validacion de calorias por comida → verificacion total global → generacion de `MealNotice`
5. Auto-retry con regeneracion dirigida antes de revision humana

## Inicio Rapido

### Requisitos Previos
- Python 3.12 · Node.js 20+ · Docker · [uv](https://github.com/astral-sh/uv)

### 1. Configurar Entorno
```bash
cp .env_example .env
# Requeridas: OPENAI_API_KEY, PINECONE_API_KEY
# Opcionales: HELICONE_API_KEY, LANGSMITH_API_KEY, GOOGLE_API_KEY
```

### 2. Instalar Dependencias
```bash
# Backend
make install    # o: uv sync

# Frontend
cd ui && npm install
```

### 3. Iniciar Servicios

**Modo desarrollo** (checkpointer en memoria):
```bash
make server-run                    # Backend en :8123
cd ui && npm run dev               # Frontend en :3000
```

**Modo produccion** (checkpointer PostgreSQL):
```bash
make server-run-d                  # Docker + Backend en :8123
cd ui && npm run dev               # Frontend en :3000
```

### Endpoints
| Endpoint | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend (AG-UI) | http://localhost:8123/ |
| Health Check | http://localhost:8123/health |
| LangGraph Studio | `make lang-dev` |

### Comandos Makefile

| Comando | Descripcion |
|---------|-------------|
| `make install` | Sincroniza dependencias Python con uv |
| `make docker-up` | Inicia PostgreSQL en Docker |
| `make docker-stop` | Detiene contenedores Docker |
| `make server-run` | FastAPI en modo desarrollo (checkpointer en memoria) |
| `make server-run-d` | Docker + FastAPI (checkpointer postgres) |
| `make server-prod` | Modo produccion (alias de `server-run-d`) |
| `make lang-dev` | Servidor de desarrollo LangGraph (Studio) |

## Estado del Desarrollo

### Completado
- [x] Arquitectura Plan-and-Execute (6 nodos, 3 edges condicionales)
- [x] Recoleccion conversacional de datos con structured output
- [x] Calculo determinista de TDEE/macros
- [x] Generacion paralela de recetas en batch (`asyncio.gather()`)
- [x] Regeneracion dirigida de comida individual
- [x] Validacion antes de HITL con auto-retry (max 2)
- [x] MealNotice feedback de validacion por comida
- [x] Revision batch HITL via `interrupt()`
- [x] Modelo `Ingredient` estructurado con kcal por ingrediente
- [x] Datos nutricionales RAG via Pinecone
- [x] Checkpointer PostgreSQL para recuperacion HITL
- [x] 56 tests unitarios + evaluacion RAGAS
- [x] Frontend: 27 componentes en 5 categorias (modo mock)
- [x] Integracion protocolo AG-UI
- [x] Observabilidad Helicone + LangSmith

### En Progreso
- [ ] Frontend Fase 2: Reemplazar mocks con `useCoAgent` + `useLangGraphInterrupt` en vivo
- [ ] Fine-tuning del nodo `recipe_generation` con GPT-4o-mini
- [ ] Tests de integracion E2E (ejecucion completa del grafo)
- [ ] Despliegue a produccion (Docker, monitoreo, escalado)

## Licencia

Este proyecto esta licenciado bajo la [Creative Commons Atribucion-NoComercial 4.0 Internacional](LICENSE).

Puedes usar, compartir y adaptar el contenido para **fines no comerciales** con el credito apropiado. Consulta el archivo [LICENSE](LICENSE) completo para mas detalles.
