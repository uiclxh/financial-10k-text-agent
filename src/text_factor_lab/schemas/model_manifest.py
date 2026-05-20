from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware


class ModelManifestRecord(StrictBaseModel):
    model_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_family: str = Field(min_length=1)
    model_level: int = Field(ge=0)
    model_version: str = Field(min_length=1)
    hyperparameters: dict
    random_seed: int
    training_window: str = Field(min_length=1)
    validation_window: str = Field(min_length=1)
    test_window: str = Field(min_length=1)
    feature_version: str = Field(min_length=1)
    label_version: str = Field(min_length=1)
    code_commit: str | None = None
    train_observation_count: int | None = Field(default=None, ge=0)
    validation_observation_count: int | None = Field(default=None, ge=0)
    test_observation_count: int | None = Field(default=None, ge=0)
    feature_count: int | None = Field(default=None, ge=0)
    created_at_utc: datetime | None = None

    @field_validator("created_at_utc")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class TuningLogRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    parameter_grid: dict[str, list[float | int | str]]
    searched_parameters: list[dict[str, float | int | str]]
    validation_metric: str = Field(min_length=1)
    validation_scores: list[float]
    selected_parameters: dict[str, float | int | str]
    selection_reason: str = Field(min_length=1)
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
