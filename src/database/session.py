from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from langgraph.checkpoint.postgres import PostgresSaver

from .config import db_settings

DB_URI = db_settings.POSTGRES_URL

# Global checkpointer instance
_checkpointer: PostgresSaver | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global _checkpointer
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        _checkpointer = checkpointer
        _checkpointer.setup()
        yield


def get_checkpointer() -> PostgresSaver:
    if _checkpointer is None:
        raise RuntimeError(
            "Checkpointer not initialized. Make sure lifespan is running."
        )
    return _checkpointer


CheckpointerDep = Annotated[PostgresSaver, Depends(get_checkpointer)]
