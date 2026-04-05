
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    tavily_api_key: str | None
    openrouter_model: str
    openrouter_pdf_router_model: str | None  # small OpenRouter model: per-PDF retrieval phrases
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

    @staticmethod
    def load() -> "Settings":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Add it to your environment or .env file."
            )

        return Settings(
            openrouter_api_key=api_key,
            tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip() or None,
            openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip(),
            openrouter_pdf_router_model=os.getenv("OPENROUTER_PDF_ROUTER_MODEL", "").strip() or None,
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
        )
