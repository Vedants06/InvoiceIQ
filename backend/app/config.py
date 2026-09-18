"""Application configuration.

All secrets/configuration come from environment variables (or a local .env
file). Nothing secret is ever shipped to the frontend.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InvoiceIQ"
    # SQLite by default so the app runs with zero infrastructure.
    # Postgres is supported by setting DATABASE_URL, e.g.
    # postgresql+psycopg://user:password@localhost:5432/invoiceiq
    database_url: str = f"sqlite:///{BASE_DIR / 'invoiceiq.db'}"

    # OpenAI (optional: Demo Mode and deterministic logic work without it)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Uploads
    upload_dir: str = str(BASE_DIR / "uploads")
    max_upload_mb: int = 10

    # Comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:5173"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    return settings
