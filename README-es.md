<div align="right">
  <a href="README.md">English</a> | <a href="README-es.md">Español</a>
</div>

# Agent January ReWOO (Español)

Sistema de agentes de IA para planificación nutricional utilizando la arquitectura **ReWOO** (Reasoning WithOut Observation) con LangGraph.

## Tabla de Contenidos

- [Descripcion](#descripcion)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Stack Tecnologico](#stack-tecnologico)
- [Inicio Rapido](#inicio-rapido)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Observabilidad con Helicone](#observabilidad-con-helicone)
- [Evaluacion con RAGAS](#evaluacion-con-ragas)

## Descripcion

Este proyecto implementa un agente de IA especializado en nutricion que utiliza la arquitectura ReWOO para generar planes alimenticios personalizados. El sistema:

- **Planifica primero**: Genera un plan de alto nivel antes de ejecutar herramientas
- **Usa sustitucion de variables**: Permite dependencias entre pasos (#E1, #E2, etc.)
- **Valida matematicamente**: Verifica calculos caloricos y de macronutrientes
- **Produce salida estructurada**: Genera planes de dieta con formato Pydantic validado

## Arquitectura del Sistema

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
│  (Prueba rapida UI)     │                   │   (Agente Principal)            │
│                         │                   │                                 │
│  START -> agent -> END  │                   │   ┌─────────┐                   │
│                         │                   │   │ Planner │ Genera plan con   │
│  - MessagesState        │                   │   │         │ herramientas y    │
│  - GPT-4o               │                   │   │         │ variables #E      │
└─────────────────────────┘                   │   └────┬────┘                   │
                                              │        │                        │
                                              │        ▼                        │
                                              │   ┌─────────┐                   │
                                              │   │ Worker  │ Ejecuta tools     │
                                              │   │         │ con sustitucion   │
                                              │   └────┬────┘                   │
                                              │        │                        │
                                              │        ▼                        │
                                              │   ┌─────────┐                   │
                                              │   │ Solver  │ Genera respuesta  │
                                              │   │         │ final DietPlan    │
                                              │   └─────────┘                   │
                                              └─────────────────────────────────┘
                                                          │
                                                          ▼
                                              ┌─────────────────────────┐
                                              │   PostgreSQL + Checkpointer   │
                                              │   (Persistencia de estado)    │
                                              └───────────────────────────────┘
```

### Flujo ReWOO

1. **Planner**: Recibe la tarea del usuario y genera un plan estructurado con herramientas y variables de sustitucion
2. **Worker**: Ejecuta cada herramienta del plan, resolviendo las variables (#E1, #E2) con resultados anteriores
3. **Solver**: Consolida las observaciones y genera la respuesta final estructurada (DietPlan)

### Herramientas Disponibles

| Herramienta | Descripcion |
|-------------|-------------|
| `generate_nutritional_plan` | Calcula TDEE y macros segun perfil del usuario |
| `food_facts_search` | Busca informacion nutricional via RAG |
| `sum_ingredients_kcal` | Valida sumas caloricas de ingredientes |
| `sum_total_kcal` | Suma calorias de todas las comidas |
| `get_meal_distribution` | Distribuye calorias por comida |
| `consolidate_shopping_list` | Genera lista de compras consolidada |
| `fetch_recipe_nutrition_facts` | Consulta base vectorial para nutricion |

## Stack Tecnologico

### Backend (Python 3.12)
- **LangGraph** - Orquestacion de agentes
- **LangChain** - Abstraccion de LLMs y herramientas
- **FastAPI** - API REST con soporte asincrono
- **CopilotKit** - Integracion frontend-backend
- **PostgreSQL** - Persistencia con `langgraph-checkpoint-postgres`
- **Pydantic v2** - Validacion estricta de esquemas

### Frontend (ui/)
- **Next.js 16** - App Router
- **React 19** - UI moderna
- **CopilotKit React** - Componentes de chat (Sidebar, Core)
- **Tailwind CSS 4** - Estilos

### Observabilidad y Evaluacion
- **Helicone** - Proxy para monitoreo de LLM calls
- **RAGAS** - Framework de evaluacion para sistemas RAG
- **LangSmith** - Tracing y debugging

## Inicio Rapido

### 1. Requisitos Previos
- Python 3.12
- Node.js 20+
- Docker y Docker Compose
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes Python)

### 2. Configurar Variables de Entorno
```bash
cp .env_example .env
# Editar .env con tus API keys:
# - OPENAI_API_KEY
# - HELICONE_API_KEY
# - VECTOR_STORE_ID
# - LANGSMITH_API_KEY (opcional)
# - Variables de PostgreSQL
```

### 3. Instalar Dependencias
```bash
# Backend
make install
# o: uv sync

# Frontend
cd ui && npm install
```

### 4. Levantar Servicios
```bash
# Iniciar PostgreSQL
make docker-up

# Iniciar Backend (desarrollo)
make server-run
# o: uv run fastapi dev src/api/main.py

# Iniciar Frontend (en otra terminal)
cd ui && npm run dev
```

### 5. Acceder
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Comandos Makefile

| Comando | Descripcion |
|---------|-------------|
| `make install` | Sincroniza dependencias con uv |
| `make docker-up` | Levanta PostgreSQL en Docker |
| `make docker-stop` | Detiene contenedores |
| `make server-run` | Inicia FastAPI en modo desarrollo |
| `make server-run-d` | Docker + FastAPI en un comando |
| `make lang-dev` | Inicia LangGraph dev server |

## Estructura del Proyecto

```
agent_january_rewoo/
├── src/
│   ├── agent/                 # Agente simple (prueba UI)
│   │   ├── agent.py           # StateGraph compilado
│   │   ├── node.py            # Nodo con GPT-4o
│   │   ├── state.py           # MessagesState
│   │   └── llm.py             # Config Helicone
│   │
│   ├── rewoo_agent/           # Agente ReWOO (principal)
│   │   ├── graph.py           # StateGraph ReWOO
│   │   ├── state.py           # ReWOOState
│   │   ├── llm.py             # LLM con Helicone proxy
│   │   ├── structured_output_meal.py  # Modelos Pydantic
│   │   ├── nodes/
│   │   │   ├── planner/       # Generacion de planes
│   │   │   │   ├── node.py    # Logica del Planner
│   │   │   │   └── prompt.py  # Prompt de planificacion
│   │   │   ├── worker/        # Ejecucion de herramientas
│   │   │   │   ├── tools.py   # 6 herramientas nutricionales
│   │   │   │   ├── node.py    # Logica del Worker
│   │   │   │   └── prompt.py  # Prompt del Worker
│   │   │   ├── solver/        # Generacion de respuesta final
│   │   │   ├── reviewer/      # Revision de planes (planeado)
│   │   │   └── documenter/    # Documentacion (planeado)
│   │   └── routes/            # Rutas adicionales
│   │
│   ├── api/
│   │   └── main.py            # FastAPI + CopilotKit endpoints
│   │
│   ├── database/
│   │   ├── config.py          # Pydantic Settings
│   │   └── session.py         # PostgresSaver + Lifespan
│   │
│   └── models/                # Modelos compartidos
│
├── ui/                        # Frontend Next.js
│   └── src/app/
│       ├── layout.tsx         # CopilotKit Provider
│       └── page.tsx           # CopilotSidebar
│
├── tests/
│   ├── tools/                 # Tests de herramientas
│   └── evaluation/            # Evaluaciones RAGAS
│
├── docker-compose.yml         # PostgreSQL service
├── langgraph.json             # Config LangGraph CLI
├── pyproject.toml             # Dependencias Python
└── Makefile                   # Comandos de desarrollo
```

## Observabilidad con Helicone

El proyecto utiliza **Helicone** como proxy para todas las llamadas a OpenAI, proporcionando:

- Logs detallados de cada request/response
- Cache de respuestas para reducir costos
- Metricas de latencia y uso de tokens
- Dashboard de monitoreo en tiempo real

```python
# src/rewoo_agent/llm.py
from langchain_openai import ChatOpenAI

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        base_url="https://oai.h7i.ai/v1",  # Proxy Helicone
        default_headers={
            "Helicone-Auth": f"Bearer {os.getenv('HELICONE_API_KEY')}",
            "Helicone-Cache-Enabled": "true",
        },
    )
```

Accede a tu dashboard en: https://www.helicone.ai/

## Evaluacion con RAGAS

**RAGAS** (Retrieval Augmented Generation Assessment) se utilizara para evaluar la calidad de las respuestas del agente:

- **Faithfulness**: Precision de la informacion respecto a la fuente
- **Answer Relevancy**: Relevancia de la respuesta a la pregunta
- **Context Precision**: Precision del contexto recuperado
- **Context Recall**: Exhaustividad del contexto

```python
# Ejemplo de evaluacion (tests/evaluation/)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

# Evaluar respuestas del agente nutricional
results = evaluate(
    dataset=test_dataset,
    metrics=[faithfulness, answer_relevancy],
)
```

## Estado del Desarrollo

- [x] Agente Simple funcional con UI
- [x] Integracion CopilotKit
- [x] PostgreSQL Checkpointer
- [x] Herramientas nutricionales (6 tools)
- [x] Planner con prompts
- [ ] Worker con sustitucion de variables
- [ ] Solver con structured output
- [ ] Evaluaciones RAGAS completas
- [ ] Reviewer y Documenter nodes

## Licencia

Este proyecto está licenciado bajo los términos de la licencia [Creative Commons Atribución-NoComercial 4.0 Internacional](LICENSE).

Puedes usar, compartir y adaptar el contenido para **fines no comerciales** siempre que se dé el crédito adecuado al autor original. Para más detalles, consulta el archivo [LICENSE](LICENSE) completo.

[Más información sobre la licencia CC BY-NC 4.0](https://creativecommons.org/)
