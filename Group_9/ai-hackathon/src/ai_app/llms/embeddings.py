from __future__ import annotations

import hashlib
import math


def embed_text(text: str, dim: int = 64) -> list[float]:
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

