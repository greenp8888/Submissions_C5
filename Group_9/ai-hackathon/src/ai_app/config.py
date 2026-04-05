from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="AI_HACKATHON_",
    )

    app_name: str = "AI Hackathon Deep Researcher"
    debug: bool = False
    openrouter_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENROUTER_API_KEY", "AI_HACKATHON_OPENROUTER_API_KEY"))
    openrouter_model: str = Field(default="openai/gpt-4o-mini", validation_alias=AliasChoices("OPENROUTER_MODEL", "AI_HACKATHON_OPENROUTER_MODEL"))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    tavily_api_key: str | None = Field(default=None, validation_alias=AliasChoices("TAVILY_API_KEY", "AI_HACKATHON_TAVILY_API_KEY"))
    top_k: int = 5
    embed_dim: int = 64
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias=AliasChoices("AI_HACKATHON_EMBEDDING_MODEL_NAME", "EMBEDDING_MODEL_NAME"))
    data_dir: Path = Path(".data")

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "collections").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "exports").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cache").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "prompts").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
