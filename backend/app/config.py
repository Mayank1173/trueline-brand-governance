"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime settings.

    All variables use the ``TRUELINE_`` prefix. A local ``.env`` file in the
    current working directory is read when present; environment variables
    always take precedence.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TRUELINE_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Trueline Review API"
    app_version: str = "0.1.0"
    environment: str = "local"

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'trueline.db').as_posix()}"
    auto_create_tables: bool = True
    seed_demo_data: bool = True

    max_draft_chars: int = Field(default=20_000, gt=0)
    max_purpose_chars: int = Field(default=200, gt=0)
    max_request_bytes: int = Field(default=1_000_000, gt=0)

    cors_origins: str = "http://localhost:3000"
    ruleset_version: str = "demo-ruleset-2026.10"
    ai_enabled: bool = False
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("TRUELINE_DATABASE_URL must not be empty")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",")]
        return [origin for origin in origins if origin]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


def get_settings() -> Settings:
    """Return settings from the process environment (not cached for tests)."""

    return Settings()
