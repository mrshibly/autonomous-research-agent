"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider ──────────────────────────────────────────────
    llm_provider: Literal["groq", "openai", "ollama"] = "groq"

    # Groq (default — free tier)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenAI (optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Ollama (optional — local, free)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # ── Embedding Provider ────────────────────────────────────────
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Search Provider ───────────────────────────────────────────
    search_provider: Literal["duckduckgo", "serpapi"] = "duckduckgo"
    serpapi_key: str = ""

    # ── Database ──────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./research.db"

    # ── CORS ──────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Rate Limiting ─────────────────────────────────────────────
    rate_limit: str = "10/minute"

    # ── Research Defaults ─────────────────────────────────────────
    max_papers: int = 5
    pubmed_email: str = "your-email@example.com"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()
