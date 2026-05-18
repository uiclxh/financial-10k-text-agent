from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """Project base model: reject unknown fields to keep artifacts stable."""

    model_config = ConfigDict(extra="forbid")


def is_timezone_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None
