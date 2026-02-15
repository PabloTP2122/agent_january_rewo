from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Run mode: "memory" (default) or "postgres" (production)
    CHECKPOINTER_TYPE: str

    # Comma-separated CORS origins
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Cloud platforms (Railway, Render, Fly.io) provide a single DATABASE_URL
    DATABASE_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator, misc]
    @property
    def POSTGRES_URL(self) -> str:
        if self.DATABASE_URL and self.CHECKPOINTER_TYPE == "postgres":
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = _base_config


db_settings = DatabaseSettings()  # type: ignore[unused-ignore]
