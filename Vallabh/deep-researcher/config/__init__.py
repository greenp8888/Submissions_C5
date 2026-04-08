"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    MAX_SOURCES_PER_QUERY: int = int(os.getenv("MAX_SOURCES_PER_QUERY", "5"))
    MAX_RETRIEVAL_ROUNDS: int = int(os.getenv("MAX_RETRIEVAL_ROUNDS", "2"))
    ENABLE_GAP_FILLING: bool = os.getenv("ENABLE_GAP_FILLING", "true").lower() == "true"

    @classmethod
    def validate(cls) -> list[str]:
        issues = []
        if not cls.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY is required")
        if not cls.TAVILY_API_KEY:
            issues.append("TAVILY_API_KEY not set — web search will be disabled")
        return issues


settings = Settings()
