from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOREVIA_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://norevia:norevia@127.0.0.1:5432/norevia"
    redis_url: str = "redis://127.0.0.1:6379/0"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    oidc_issuer: str | None = None
    oidc_audience: str = "norevia-api"
    raw_storage_path: Path = Path("raw")
    allow_development_identity: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
