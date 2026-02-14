<div align="right">
  <a href="README.md"><strong>English</strong></a> | <a href="README-es.md">Español</a>
</div>

# Nutrition Agent — AI Meal Planning with LangGraph

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-purple)
![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)

AI-powered nutrition planning agent that generates personalized meal plans through conversational data collection, deterministic macro calculation, and parallel recipe generation — with automated validation and human-in-the-loop review.

### Highlights

- **Plan-and-Execute architecture** with 6 specialized nodes and 3 conditional routing edges
- **Parallel batch meal generation** via `asyncio.gather()` (~60% latency reduction vs sequential)
- **Validation-before-HITL** — automated calorie checking with auto-retry before human review
- **Structured output** with per-ingredient calorie tracking (`Ingredient` model with `kcal` field)
- **RAG-powered nutritional data** via Pinecone vector store
- **56 unit tests** across 10 test files + RAGAS evaluation framework
- **27 React components** across 5 categories with mock-first development
- **AG-UI protocol** for real-time agent state streaming to frontend

## Table of Contents

- [System Architecture](#system-architecture)
- [Agent Graph Flow](#agent-graph-flow)
- [Key Design Decisions](#key-design-decisions)
- [Architecture Evolution](#architecture-evolution)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Testing & Quality](#testing--quality)
- [Quick Start](#quick-start)
- [Development Status](#development-status)
- [License](#license)

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│   Next.js 16 · CopilotKit · 27 React Components                │
│   Split view (Chat 34% + Canvas 66%) · Responsive               │
│   runtimeUrl → http://localhost:8123/                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │ AG-UI Protocol (streaming)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│   FastAPI (port 8123) · ag-ui-langgraph bridge                  │
│   LangGraphAGUIAgent("nutrition_agent") · CORS                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NUTRITION AGENT                                │
│   Plan-and-Execute · 6 Nodes · 3 Conditional Edges              │
│                                                                  │
│   data_collection ──► calculation ──► recipe_gen_batch           │
│        (LLM)          (deterministic)    (LLM, parallel)        │
│                                              │                   │
│                                              ▼                   │
│                                         validation               │
│                                        (deterministic)           │
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

## Agent Graph Flow

The nutrition agent uses a Plan-and-Execute architecture with conditional routing based on validation results and user feedback:

```
    START → data_collection ←──┐ (loop if missing fields)
                │               │
                ▼               │
           calculation ─────────┘
                │
                ▼
    recipe_generation_batch ◄──────────────────┐
                │                              │
                ▼                              │
           validation ─────────────────────────┤ (N fails → batch regen)
                │           │                  │
                │      (1 fail)                │
                │           ↓                  │
                │   recipe_generation_single ──┘
                │
                ▼  (pass / retries ≥ 2)
       meal_review_batch (HITL interrupt)
                │
        ┌───────┼──────────────────────┐
        │       │                      │
     approve  change_meal        regenerate_all
        │       ↓                      │
        ▼   recipe_gen_single    recipe_gen_batch
       END
```

**Node details:**

| Node | Type | Purpose |
|------|------|---------|
| `data_collection` | LLM | Conversational extraction of `UserProfile` via structured output |
| `calculation` | Deterministic | TDEE, macros, meal distribution via co-located tools (no LLM) |
| `recipe_generation_batch` | LLM | Parallel generation of all meals via `asyncio.gather()` |
| `recipe_generation_single` | LLM | Targeted single-meal regeneration (validation fix or user request) |
| `validation` | Deterministic | Per-meal + global calorie checks, `MealNotice` generation, routing |
| `meal_review_batch` | HITL | `interrupt()` pause for human review of complete plan |

## Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Validation before HITL** | Humans only review validated meals — reduces back-and-forth feedback loops. Auto-retry (max 2) with targeted regeneration before presenting to user. |
| 2 | **Parallel batch generation** | N-1 meals generated via `asyncio.gather()`, last meal sequential to close the calorie budget. ~60% latency reduction vs sequential generation. |
| 3 | **Structured `Ingredient` model** | `Ingredient(nombre, cantidad_display, peso_gramos, kcal)` replaces `list[str]` — enables per-ingredient calorie validation without regex parsing. |
| 4 | **`MealNotice` system** | Per-meal validation feedback with severity levels (warning: 2-5% deviation, error: >5%) — granular feedback instead of pass/fail. |
| 5 | **Tool co-location** | Each tool lives with its consuming node (`nodes/calculation/tools.py`) instead of a monolithic `shared/tools.py` — better cohesion, easier testing, clearer ownership. |
| 6 | **`StrictBaseModel` for tool schemas** | `extra="forbid"` on all tool input schemas — prevents LLM hallucination of extra fields. |
| 7 | **Deterministic nodes for math** | Calculation and validation nodes use no LLM — mathematical operations are too important to delegate to probabilistic models. |

## Architecture Evolution

This project started with the **ReWOO** (Reasoning WithOut Observation) architecture and was migrated to **Plan-and-Execute** after identifying fundamental limitations:

| Criteria | ReWOO | Plan-and-Execute |
|----------|:-----:|:----------------:|
| Error Recovery | 2/5 | 5/5 |
| Conversational Data Collection | 1/5 | 5/5 |
| HITL Support | 3/5 | 4/5 |
| Fine-tuning Viability | 3/5 | 5/5 |
| Debuggability | 2/5 | 4/5 |
| Reactivity | 2/5 | 5/5 |
| Token Efficiency | 5/5 | 4/5 |
| **Total** | **18/35** | **32/35** |

**Why ReWOO didn't work:**
- **Not reactive** — couldn't adjust if RAG queries failed mid-plan
- **No conversational collection** — required complete user profile upfront
- **Fragile regex parsing** — `#E1`, `#E2` variable substitution was hard to debug
- **All-or-nothing execution** — one step failure killed the entire plan

The ReWOO agent is preserved in `src/rewoo_agent/` for A/B comparison. The full architectural analysis is documented in [`spec/01-architecture-analysis-rewoo-vs-alternatives.md`](spec/01-architecture-analysis-rewoo-vs-alternatives.md).

## Tech Stack

### Backend

| Technology | Version | Why |
|------------|---------|-----|
| Python | 3.12 | Type hints, `asyncio`, pattern matching |
| LangGraph | latest | Stateful agent graphs with conditional routing and HITL via `interrupt()` |
| FastAPI | 0.115.x | Async API with lifespan pattern for DB connection management |
| AG-UI Protocol | ≥0.0.21 | Streaming agent state to frontend via CopilotKit bridge |
| Pydantic v2 | latest | Strict validation with `StrictBaseModel` (anti-hallucination) |
| Pinecone | ≥0.2.13 | Vector store for nutritional data RAG queries |
| PostgreSQL | 15 | HITL state persistence via `langgraph-checkpoint-postgres` |
| Helicone | proxy | LLM observability, response caching, cost tracking |
| OpenAI GPT-4o | primary | Main LLM for structured output generation |

### Frontend

| Technology | Version | Why |
|------------|---------|-----|
| Next.js | 16.1.6 | App Router, React 19, server components |
| CopilotKit | ^1.50.1 | AG-UI protocol, `useCoAgent`, `useLangGraphInterrupt` |
| TypeScript | ^5 | Strict types mirroring Python Pydantic models exactly |
| React Hook Form + Zod | latest | Form validation matching Python field constraints |
| Tailwind CSS | ^4 | Responsive 66/34 split layout with mobile toggle |

### Quality & Observability

| Tool | Purpose |
|------|---------|
| Ruff | Linting — E, F, UP, B, SIM, I, S rules |
| mypy (strict) | Static type checking with `disallow_untyped_defs` |
| pytest | 56 unit tests across 10 test files |
| RAGAS | LLM output evaluation (faithfulness, answer relevancy) |
| pre-commit | Automated quality gates before each commit |
| LangSmith | Agent execution tracing and debugging |
| Helicone | LLM request/response logging with caching |

## Project Structure

```
src/
├── nutrition_agent/              # Main agent (Plan-and-Execute)
│   ├── graph.py                  # StateGraph: 6 nodes, 3 conditional edges
│   ├── state.py                  # NutritionAgentState (14 fields)
│   ├── models/
│   │   ├── user_profile.py       # UserProfile (age, gender, weight, height...)
│   │   ├── nutritional_targets.py # NutritionalTargets (TDEE, macros)
│   │   ├── diet_plan.py          # DietPlan, Meal, Ingredient, MealNotice
│   │   └── tools.py              # StrictBaseModel tool schemas
│   ├── nodes/
│   │   ├── data_collection/      # LLM: conversational profile extraction
│   │   ├── calculation/          # Deterministic: TDEE + macros + tools
│   │   ├── recipe_generation/    # LLM: batch + single + RAG tool
│   │   ├── validation/           # Deterministic: calorie checks + tools
│   │   └── meal_review/          # HITL: interrupt() batch review
│   └── prompts/                  # LLM prompt templates
│
├── shared/                       # Cross-cutting utilities
│   ├── tools.py                  # sum_ingredients_kcal (shared validation)
│   ├── enums.py                  # ActivityLevel, Objective, DietType, MealTime
│   └── llm.py                   # LLM factory with Helicone proxy
│
├── api/main.py                   # FastAPI + ag-ui-langgraph bridge (port 8123)
├── database/                     # PostgreSQL checkpointer lifecycle
└── agent/                        # Simple agent (UI testing)

ui/                               # Next.js 16 frontend
├── components/
│   ├── canvas/    (7)            # DietPlanCanvas, MealCard, MacrosTable...
│   ├── forms/     (3)            # UserProfileForm, ExcludedFoodInput...
│   ├── hitl/      (4)            # MealPlanReview, MealReviewCard...
│   ├── layout/    (4)            # MainLayout, Canvas, ChatPanel...
│   └── ui/        (9)            # Button, Card, Badge, Spinner...
├── hooks/         (3)            # useAgentPhase, useMockData, useMediaQuery
└── lib/                          # types.ts, validations.ts, config.ts

tests/
├── tools/         (7 files)      # Unit tests for all nutritional tools
├── nodes/         (1 file)       # Validation node tests (20+ cases)
├── quick_tool_tests/ (2 files)   # RAG + calculation smoke tests
└── evaluation/                   # RAGAS scripts + ground truth datasets
```

## Testing & Quality

**56 test functions** across 10 test files covering:

- **Tool unit tests** (7 files) — `generate_nutritional_plan`, `get_meal_distribution`, `sum_ingredients_kcal`, `sum_total_kcal`, `consolidate_shopping_list`, `calculate_recipe_nutrition`
- **Validation node tests** (20+ cases) — per-meal calorie budget, global total verification, `MealNotice` generation, routing hint logic, shopping list consolidation, edge cases
- **Smoke tests** — RAG tool integration, calculation node end-to-end
- **RAGAS evaluation** — `answer_correctness`, `answer_similarity` with ground truth datasets

**Anti-hallucination pipeline:**
1. `StrictBaseModel` (`extra="forbid"`) on all tool input schemas
2. Enum constraints for `ActivityLevel`, `Objective`, `DietType`, `MealTime`, `Gender`
3. Pydantic v2 structured output for all LLM nodes
4. Per-meal calorie validation → global total check → `MealNotice` generation
5. Auto-retry with targeted regeneration before human review

## Quick Start

### Prerequisites
- Python 3.12 · Node.js 20+ · Docker · [uv](https://github.com/astral-sh/uv)

### 1. Environment Setup
```bash
cp .env_example .env
# Required: OPENAI_API_KEY, PINECONE_API_KEY
# Optional: HELICONE_API_KEY, LANGSMITH_API_KEY, GOOGLE_API_KEY
```

### 2. Install Dependencies
```bash
# Backend
make install    # or: uv sync

# Frontend
cd ui && npm install
```

### 3. Start Services

**Development mode** (in-memory checkpointer):
```bash
make server-run                    # Backend on :8123
cd ui && npm run dev               # Frontend on :3000
```

**Production mode** (PostgreSQL checkpointer):
```bash
make server-run-d                  # Docker + Backend on :8123
cd ui && npm run dev               # Frontend on :3000
```

### Endpoints
| Endpoint | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend (AG-UI) | http://localhost:8123/ |
| Health Check | http://localhost:8123/health |
| LangGraph Studio | `make lang-dev` |

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Sync Python dependencies with uv |
| `make docker-up` | Start PostgreSQL in Docker |
| `make docker-stop` | Stop Docker containers |
| `make server-run` | FastAPI dev mode (memory checkpointer) |
| `make server-run-d` | Docker + FastAPI (postgres checkpointer) |
| `make server-prod` | Production mode (alias for `server-run-d`) |
| `make lang-dev` | LangGraph dev server (Studio) |

## Development Status

### Completed
- [x] Plan-and-Execute architecture (6 nodes, 3 conditional edges)
- [x] Conversational data collection with structured output
- [x] Deterministic TDEE/macro calculation
- [x] Parallel batch recipe generation (`asyncio.gather()`)
- [x] Targeted single-meal regeneration
- [x] Validation-before-HITL with auto-retry (max 2)
- [x] MealNotice per-meal validation feedback
- [x] HITL batch review via `interrupt()`
- [x] Structured `Ingredient` model with per-ingredient kcal
- [x] RAG nutritional data via Pinecone
- [x] PostgreSQL checkpointer for HITL recovery
- [x] 56 unit tests + RAGAS evaluation
- [x] Frontend: 27 components across 5 categories (mock mode)
- [x] AG-UI protocol integration
- [x] Helicone + LangSmith observability

### In Progress
- [ ] Frontend Phase 2: Replace mocks with live `useCoAgent` + `useLangGraphInterrupt`
- [ ] Fine-tuning `recipe_generation` node with GPT-4o-mini
- [ ] E2E integration tests (full graph execution)
- [ ] Production deployment (Docker, monitoring, scaling)

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE) license.

You may use, share, and adapt the content for **non-commercial purposes** with appropriate credit. See the full [LICENSE](LICENSE) file for details.
