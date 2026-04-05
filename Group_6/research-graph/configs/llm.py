import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "openrouter"

OLLAMA_CONFIG = {
    "model": os.getenv("OLLAMA_MODEL", "gpt-oss:20b"),
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
    "top_p": float(os.getenv("OLLAMA_TOP_P", "0.9")),
}

OPENROUTER_CONFIG = {
    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
    "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.1")),
    "top_p": float(os.getenv("OPENROUTER_TOP_P", "0.9")),
    "site_url": os.getenv("OPENROUTER_SITE_URL", ""),
    "site_name": os.getenv("OPENROUTER_SITE_NAME", "Research Graph"),
}

RETRIEVAL_CONFIG = {
    "max_hops": int(os.getenv("MAX_RETRIEVAL_HOPS", "2")),
    "strict_grounding": os.getenv("STRICT_GROUNDING", "true").lower() == "true",
}

RAG_CONFIG = {
    "embedding_model": os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    ),
    "chunk_size": int(os.getenv("CHUNK_SIZE", "1000")),
    "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "200")),
    "max_retrieval_k": int(os.getenv("MAX_RETRIEVAL_K", "5")),
}
