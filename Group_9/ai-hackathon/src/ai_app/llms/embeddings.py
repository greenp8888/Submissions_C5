from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from ai_app.config import Settings

try:  # pragma: no cover - optional dependency path
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency path
    SentenceTransformer = None


class LocalEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache_path = settings.data_dir / "cache" / "embedding_cache.json"
        self._cache = self._load_cache()
        self._model = None

    def embed(self, text: str) -> list[float]:
        checksum = text_checksum(text)
        if checksum in self._cache:
            return self._cache[checksum]
        if self._model_available():
            vector = [float(value) for value in self._model.encode(text, normalize_embeddings=True).tolist()]
        else:
            vector = _hash_embed_text(text, dim=self.settings.embed_dim)
        self._cache[checksum] = vector
        self._persist_cache()
        return vector

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def _model_available(self) -> bool:
        if self._model is not None:
            return True
        if SentenceTransformer is None:
            return False
        try:
            self._model = SentenceTransformer(self.settings.embedding_model_name)
        except Exception:
            self._model = None
        return self._model is not None

    def _load_cache(self) -> dict[str, list[float]]:
        if not self.cache_path.exists():
            return {}
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {str(key): [float(value) for value in values] for key, values in payload.items()}

    def _persist_cache(self) -> None:
        self.cache_path.write_text(json.dumps(self._cache), encoding="utf-8")


def text_checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_embed_text(text: str, dim: int = 64) -> list[float]:
    vector = [0.0] * dim
    tokens = [token.strip(".,:;!?()[]{}").lower() for token in text.split() if token.strip()]
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(dim):
            vector[index] += digest[index % len(digest)] / 255.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
