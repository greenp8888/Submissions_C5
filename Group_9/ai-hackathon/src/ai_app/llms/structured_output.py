from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def parse_model(data: dict, model: type[T]) -> T | None:
    if not data:
        return None
    return model.model_validate(data)

