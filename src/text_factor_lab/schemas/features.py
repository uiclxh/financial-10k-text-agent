from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware


class FeatureRecord(StrictBaseModel):
    feature_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    event_time_utc: datetime
    prediction_time_utc: datetime
    feature_time_utc: datetime
    feature_family: str = Field(min_length=1)
    feature_name: str = Field(min_length=1)
    feature_value: float | str
    feature_version: str = Field(min_length=1)
    source_document_id: str = Field(min_length=1)
    source_chunk_id: str | None = None

    @field_validator("event_time_utc", "prediction_time_utc", "feature_time_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("datetime fields must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_no_lookahead(self) -> FeatureRecord:
        if self.feature_time_utc > self.prediction_time_utc:
            raise ValueError("feature_time_utc must be before or equal to prediction_time_utc")
        return self
