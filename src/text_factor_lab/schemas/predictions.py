from __future__ import annotations

from datetime import date
from math import isfinite

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel


class PredictionRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    event_date: date
    target_name: str = Field(min_length=1)
    prediction_value: float
    factor_score: float
    feature_version: str = Field(min_length=1)
    label_version: str = Field(min_length=1)
    training_window: str = Field(min_length=1)
    validation_window: str = Field(min_length=1)
    test_window: str = Field(min_length=1)

    @field_validator("prediction_value", "factor_score")
    @classmethod
    def validate_finite_float(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("prediction_value and factor_score must be finite")
        return value
