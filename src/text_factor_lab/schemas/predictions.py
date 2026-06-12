from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Literal

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

PredictionRole = Literal["validation", "test"]
PredictionFailureStage = Literal[
    "missing_train_rows",
    "missing_train_features",
    "missing_feature",
    "model_training_failed",
]


class PredictionRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    label_id: str | None = Field(default=None, min_length=1)
    role: PredictionRole | None = None
    model_expected: bool = True
    ticker: str = Field(min_length=1)
    event_date: date
    target_name: str = Field(min_length=1)
    prediction_value: float
    factor_score: float
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = Field(default=None, gt=0)
    feature_version: str = Field(min_length=1)
    label_version: str = Field(min_length=1)
    training_window: str = Field(min_length=1)
    validation_window: str = Field(min_length=1)
    test_window: str = Field(min_length=1)

    @field_validator("prediction_value", "factor_score", "market_cap")
    @classmethod
    def validate_finite_float(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not isfinite(value):
            raise ValueError("prediction_value and factor_score must be finite")
        return value


class ModelPredictionFailureRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    label_id: str = Field(min_length=1)
    role: PredictionRole
    ticker: str = Field(min_length=1)
    event_date: date
    target_name: str = Field(min_length=1)
    failure_stage: PredictionFailureStage
    failure_reason: str = Field(min_length=1)
    model_expected: bool = True
    recommended_fix: str = Field(min_length=1)
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
