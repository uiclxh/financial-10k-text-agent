from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Literal

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

ReturnType = Literal["log", "simple"]


class LabelRecord(StrictBaseModel):
    label_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    event_time_utc: datetime
    prediction_time_utc: datetime
    label_start_date: date
    label_end_date: date
    target_name: str = Field(min_length=1)
    target_value: float
    benchmark_method: str = Field(min_length=1)
    return_type: ReturnType
    adjustment_method: str = Field(min_length=1)
    label_version: str = Field(min_length=1)

    @field_validator("event_time_utc", "prediction_time_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("datetime fields must be timezone-aware")
        return value

    @field_validator("target_value")
    @classmethod
    def validate_finite_target(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("target_value must be finite")
        return value

    @model_validator(mode="after")
    def validate_label_window(self) -> LabelRecord:
        if self.label_start_date > self.label_end_date:
            raise ValueError("label_start_date must be before or equal to label_end_date")
        if self.prediction_time_utc.date() >= self.label_start_date:
            raise ValueError("prediction_time_utc must be before label_start_date")
        return self

