from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .config import db_settings

DB_URI = db_settings.POSTGRES_URL

_checkpointer: AsyncPostgresSaver | None = None


@asynccontextmanager
async def db_lifespan(app: FastAPI) -> Any:
    """Manage AsyncPostgresSaver lifecycle using from_conn_string."""
    global _checkpointer
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        _checkpointer = checkpointer
        try:
            yield
        finally:
            _checkpointer = None


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError(
            "Checkpointer not initialized. Make sure db_lifespan is running."
        )
    return _checkpointer


CheckpointerDep = Annotated[AsyncPostgresSaver, Depends(get_checkpointer)]
