from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from ag_ui_langgraph.agent import CompiledStateGraph
from copilotkit import LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Error

from database.config import db_settings
from database.session import CheckpointerDep, db_lifespan, get_checkpointer
from nutrition_agent import make_graph

load_dotenv()


def _register_agent(app: FastAPI, graph: CompiledStateGraph) -> None:
    """Register the nutrition agent AG-UI endpoint on the app."""
    add_langgraph_fastapi_endpoint(
        app=app,
        agent=LangGraphAGUIAgent(
            name="nutrition_agent",
            description="Agente de planificación nutricional personalizada",
            graph=graph,
        ),
        path="/",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    if db_settings.CHECKPOINTER_TYPE == "postgres":
        async with db_lifespan(app):
            graph = make_graph(get_checkpointer())
            _register_agent(app, graph)
            yield
    else:
        from langgraph.checkpoint.memory import MemorySaver

        graph = make_graph(MemorySaver())
        _register_agent(app, graph)
        yield


app = FastAPI(lifespan=lifespan)

origins = [o.strip() for o in db_settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")  # type: ignore[misc]
async def health() -> dict:
    return {
        "status": "ok",
        "checkpointer": db_settings.CHECKPOINTER_TYPE,
    }


@app.get("/health/checkpointer")  # type: ignore[misc]
async def health_checkpointer(checkpointer: CheckpointerDep) -> dict:
    try:
        await checkpointer.conn.execute("SELECT 1")
    except Error as e:
        return {
            "type": type(checkpointer).__name__,
            "is_active": False,
            "error": str(e),
        }
    else:
        return {
            "type": type(checkpointer).__name__,
            "is_active": True,
        }


def main() -> None:
    """Run the uvicorn server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # noqa: S104
        port=8123,
        reload=True,
    )


if __name__ == "__main__":
    main()
