<div align="right">
  <a href="README.md">English</a> | <a href="README-es.md">Español</a>
</div>

# Agent January ReWOO (English)

AI agent system for nutritional planning using the **ReWOO** (Reasoning WithOut Observation) architecture with LangGraph.

## Table of Contents

- [Description](#description)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Observability with Helicone](#observability-with-helicone)
- [Evaluation with RAGAS](#evaluation-with-ragas)

## Description

This project implements an AI agent specialized in nutrition that uses the ReWOO architecture to generate personalized meal plans. The system:

- **Plans first**: Generates a high-level plan before executing tools
- **Uses variable substitution**: Allows dependencies between steps (#E1, #E2, etc.)
- **Validates mathematically**: Verifies caloric and macronutrient calculations
- **Produces structured output**: Generates diet plans with validated Pydantic format

## System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          Frontend (Next.js 16)          │
                    │     CopilotKit React UI Components      │
                    └──────────────────┬──────────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────────┐
                    │           FastAPI Server                │
                    │     /copilotkit (CopilotKit SDK)        │
                    │     /health, /chat_memory               │
                    └──────────────────┬──────────────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                 │
              ▼                                                 ▼
┌─────────────────────────┐                   ┌─────────────────────────────────┐
│    Simple Agent         │                   │       ReWOO Agent               │
│  (Quick UI test)        │                   │   (Main Agent)                  │
│                         │                   │                                 │
│  START -> agent -> END  │                   │   ┌─────────┐                   │
│                         │                   │   │ Planner │ Generates plan    │
│  - MessagesState        │                   │   │         │ with tools and    │
│  - GPT-4o               │                   │   │         │ #E variables      │
└─────────────────────────┘                   │   └────┬────┘                   │
                                              │        │                        │
                                              │        ▼                        │
                                              │   ┌─────────┐                   │
                                              │   │ Worker  │ Executes tools    │
                                              │   │         │ with substitution │
                                              │   └────┬────┘                   │
                                              │        │                        │
                                              │        ▼                        │
                                              │   ┌─────────┐                   │
                                              │   │ Solver  │ Generates final   │
                                              │   │         │ DietPlan response │
                                              │   └─────────┘                   │
                                              └─────────────────────────────────┘
                                                          │
                                                          ▼
                                              ┌─────────────────────────┐
                                              │   PostgreSQL + Checkpointer   │
                                              │   (State persistence)         │
                                              └───────────────────────────────┘
```

### ReWOO Flow

1. **Planner**: Receives the user's task and generates a structured plan with tools and substitution variables
2. **Worker**: Executes each tool in the plan, resolving variables (#E1, #E2) with previous results
3. **Solver**: Consolidates observations and generates the final structured response (DietPlan)

### Available Tools

| Tool | Description |
|------|-------------|
| `generate_nutritional_plan` | Calculates TDEE and macros based on user profile |
| `food_facts_search` | Searches nutritional information via RAG |
| `sum_ingredients_kcal` | Validates caloric sums of ingredients |
| `sum_total_kcal` | Sums calories from all meals |
| `get_meal_distribution` | Distributes calories per meal |
| `consolidate_shopping_list` | Generates consolidated shopping list |
| `fetch_recipe_nutrition_facts` | Queries vector database for nutrition |

## Tech Stack

### Backend (Python 3.12)
- **LangGraph** - Agent orchestration
- **LangChain** - LLM and tools abstraction
- **FastAPI** - REST API with async support
- **CopilotKit** - Frontend-backend integration
- **PostgreSQL** - Persistence with `langgraph-checkpoint-postgres`
- **Pydantic v2** - Strict schema validation

### Frontend (ui/)
- **Next.js 16** - App Router
- **React 19** - Modern UI
- **CopilotKit React** - Chat components (Sidebar, Core)
- **Tailwind CSS 4** - Styling

### Observability and Evaluation
- **Helicone** - Proxy for LLM call monitoring
- **RAGAS** - Evaluation framework for RAG systems
- **LangSmith** - Tracing and debugging

## Quick Start

### 1. Prerequisites
- Python 3.12
- Node.js 20+
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 2. Configure Environment Variables
```bash
cp .env_example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - HELICONE_API_KEY
# - VECTOR_STORE_ID
# - LANGSMITH_API_KEY (optional)
# - PostgreSQL variables
```

### 3. Install Dependencies
```bash
# Backend
make install
# or: uv sync

# Frontend
cd ui && npm install
```

### 4. Start Services
```bash
# Start PostgreSQL
make docker-up

# Start Backend (development)
make server-run
# or: uv run fastapi dev src/api/main.py

# Start Frontend (in another terminal)
cd ui && npm run dev
```

### 5. Access
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Sync dependencies with uv |
| `make docker-up` | Start PostgreSQL in Docker |
| `make docker-stop` | Stop containers |
| `make server-run` | Start FastAPI in development mode |
| `make server-run-d` | Docker + FastAPI in one command |
| `make lang-dev` | Start LangGraph dev server |

## Project Structure

```
agent_january_rewoo/
├── src/
│   ├── agent/                 # Simple agent (UI test)
│   │   ├── agent.py           # Compiled StateGraph
│   │   ├── node.py            # Node with GPT-4o
│   │   ├── state.py           # MessagesState
│   │   └── llm.py             # Helicone config
│   │
│   ├── rewoo_agent/           # ReWOO Agent (main)
│   │   ├── graph.py           # ReWOO StateGraph
│   │   ├── state.py           # ReWOOState
│   │   ├── llm.py             # LLM with Helicone proxy
│   │   ├── structured_output_meal.py  # Pydantic models
│   │   ├── nodes/
│   │   │   ├── planner/       # Plan generation
│   │   │   │   ├── node.py    # Planner logic
│   │   │   │   └── prompt.py  # Planning prompt
│   │   │   ├── worker/        # Tool execution
│   │   │   │   ├── tools.py   # 6 nutritional tools
│   │   │   │   ├── node.py    # Worker logic
│   │   │   │   └── prompt.py  # Worker prompt
│   │   │   ├── solver/        # Final response generation
│   │   │   ├── reviewer/      # Plan review (planned)
│   │   │   └── documenter/    # Documentation (planned)
│   │   └── routes/            # Additional routes
│   │
│   ├── api/
│   │   └── main.py            # FastAPI + CopilotKit endpoints
│   │
│   ├── database/
│   │   ├── config.py          # Pydantic Settings
│   │   └── session.py         # PostgresSaver + Lifespan
│   │
│   └── models/                # Shared models
│
├── ui/                        # Next.js Frontend
│   └── src/app/
│       ├── layout.tsx         # CopilotKit Provider
│       └── page.tsx           # CopilotSidebar
│
├── tests/
│   ├── tools/                 # Tool tests
│   └── evaluation/            # RAGAS evaluations
│
├── docker-compose.yml         # PostgreSQL service
├── langgraph.json             # LangGraph CLI config
├── pyproject.toml             # Python dependencies
└── Makefile                   # Development commands
```

## Observability with Helicone

The project uses **Helicone** as a proxy for all OpenAI calls, providing:

- Detailed logs of each request/response
- Response caching to reduce costs
- Latency and token usage metrics
- Real-time monitoring dashboard

```python
# src/rewoo_agent/llm.py
from langchain_openai import ChatOpenAI

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        base_url="https://oai.h7i.ai/v1",  # Helicone proxy
        default_headers={
            "Helicone-Auth": f"Bearer {os.getenv('HELICONE_API_KEY')}",
            "Helicone-Cache-Enabled": "true",
        },
    )
```

Access your dashboard at: https://www.helicone.ai/

## Evaluation with RAGAS

**RAGAS** (Retrieval Augmented Generation Assessment) will be used to evaluate the quality of the agent's responses:

- **Faithfulness**: Information accuracy relative to the source
- **Answer Relevancy**: Response relevance to the question
- **Context Precision**: Precision of retrieved context
- **Context Recall**: Completeness of context

```python
# Evaluation example (tests/evaluation/)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

# Evaluate nutritional agent responses
results = evaluate(
    dataset=test_dataset,
    metrics=[faithfulness, answer_relevancy],
)
```

## Development Status

- [x] Functional Simple Agent with UI
- [x] CopilotKit Integration
- [x] PostgreSQL Checkpointer
- [x] Nutritional tools (6 tools)
- [x] Planner with prompts
- [ ] Worker with variable substitution
- [ ] Solver with structured output
- [ ] Complete RAGAS evaluations
- [ ] Reviewer and Documenter nodes

## License

This project is licensed under the terms of the [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE) license.

You may use, share, and adapt the content for **non-commercial purposes** as long as appropriate credit is given to the original author. For more details, see the full [LICENSE](LICENSE) file.

[More information about the CC BY-NC 4.0 license](https://creativecommons.org/)
