from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError


T = TypeVar("T", bound=BaseModel)


def parse_model(data: dict, model: type[T]) -> T | None:
    if not data:
        return None
    try:
        return model.model_validate(data)
    except ValidationError:
        return None
