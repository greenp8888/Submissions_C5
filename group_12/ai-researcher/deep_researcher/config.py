
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Used by the UI and Settings validation — Anthropic tier: budget / Haiku only (no Sonnet or Opus).
ANTHROPIC_BUDGET_MODELS: tuple[str, ...] = (
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
)

LLM_PROVIDER_OPENROUTER = "openrouter"
LLM_PROVIDER_ANTHROPIC = "anthropic"


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    llm_provider: str  # "openrouter" | "anthropic"
    openrouter_api_key: str
    tavily_api_key: str | None
    openrouter_model: str
    openrouter_pdf_router_model: str | None  # small OpenRouter model: per-PDF retrieval phrases
    anthropic_api_key: str | None
    anthropic_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    web_results_per_query: int
    max_workers_pdf_io: int
    pdf_multimodal_hf: bool  # BLIP captions for embedded PDF images (needs torch+transformers)
    pdf_sentiment_hf: bool  # DistilBERT sentiment on early text (needs transformers)
    pdf_max_images_per_document: int
    asr_hf_model: str
    asr_max_seconds: float
    max_research_rounds: int
    max_followup_queries: int
    max_evidence_items: int
    analyst_evidence_limit: int

    @staticmethod
    def load(
        *,
        llm_provider_override: str | None = None,
        openrouter_api_key_override: str | None = None,
        openrouter_model_override: str | None = None,
        anthropic_api_key_override: str | None = None,
        anthropic_model_override: str | None = None,
    ) -> "Settings":
        """Load settings from environment, optionally overridden by UI values (non-empty overrides win)."""

        raw_provider = (llm_provider_override or "").strip().lower() or os.getenv(
            "LLM_PROVIDER", LLM_PROVIDER_OPENROUTER
        ).strip().lower()
        if raw_provider == LLM_PROVIDER_ANTHROPIC:
            provider = LLM_PROVIDER_ANTHROPIC
        else:
            provider = LLM_PROVIDER_OPENROUTER

        api_key = (openrouter_api_key_override or "").strip() or os.getenv("OPENROUTER_API_KEY", "").strip()
        anthropic_key = (anthropic_api_key_override or "").strip() or os.getenv(
            "ANTHROPIC_API_KEY", ""
        ).strip() or None
        if anthropic_key == "":
            anthropic_key = None

        openrouter_model = (openrouter_model_override or "").strip() or os.getenv(
            "OPENROUTER_MODEL", "openai/gpt-4o-mini"
        ).strip()

        default_ant = ANTHROPIC_BUDGET_MODELS[0]
        anthropic_model = (anthropic_model_override or "").strip() or os.getenv(
            "ANTHROPIC_MODEL", default_ant
        ).strip()

        if provider == LLM_PROVIDER_ANTHROPIC:
            if not anthropic_key:
                raise ValueError(
                    "Anthropic is selected but no API key was found. Paste your key in the UI or set ANTHROPIC_API_KEY."
                )
            if anthropic_model not in ANTHROPIC_BUDGET_MODELS:
                raise ValueError(
                    "Only budget Claude (Haiku) models are allowed. Choose one of: "
                    + ", ".join(ANTHROPIC_BUDGET_MODELS)
                )
            api_key = api_key or ""
        else:
            if not api_key:
                raise ValueError(
                    "OpenRouter is selected but no API key was found. Paste your key in the UI or set OPENROUTER_API_KEY."
                )
            anthropic_model = anthropic_model if anthropic_model in ANTHROPIC_BUDGET_MODELS else default_ant

        return Settings(
            llm_provider=provider,
            openrouter_api_key=api_key,
            tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip() or None,
            openrouter_model=openrouter_model,
            openrouter_pdf_router_model=os.getenv("OPENROUTER_PDF_ROUTER_MODEL", "").strip() or None,
            anthropic_api_key=anthropic_key,
            anthropic_model=anthropic_model,
            embedding_model=os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            ).strip(),
            chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            top_k=int(os.getenv("TOP_K", "4")),
            web_results_per_query=int(os.getenv("WEB_RESULTS_PER_QUERY", "3")),
            max_workers_pdf_io=max(1, int(os.getenv("PDF_PARALLEL_WORKERS", "4"))),
            pdf_multimodal_hf=_env_bool("PDF_MULTIMODAL_HF"),
            pdf_sentiment_hf=_env_bool("PDF_SENTIMENT_HF"),
            pdf_max_images_per_document=max(0, int(os.getenv("PDF_MAX_IMAGES_PER_DOCUMENT", "6"))),
            asr_hf_model=os.getenv("ASR_HF_MODEL", "openai/whisper-small").strip(),
            asr_max_seconds=float(os.getenv("ASR_MAX_SECONDS", "180")),
            max_research_rounds=max(1, min(5, int(os.getenv("MAX_RESEARCH_ROUNDS", "1")))),
            max_followup_queries=max(1, min(12, int(os.getenv("MAX_FOLLOWUP_QUERIES", "6")))),
            max_evidence_items=max(20, min(500, int(os.getenv("MAX_EVIDENCE_ITEMS", "120")))),
            analyst_evidence_limit=max(8, min(64, int(os.getenv("ANALYST_EVIDENCE_LIMIT", "24")))),
        )
