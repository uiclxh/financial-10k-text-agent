from __future__ import annotations

from datetime import datetime
from typing import Literal

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


class FeatureManifestRecord(StrictBaseModel):
    feature_version: str = Field(min_length=1)
    feature_method: Literal["dictionary_tone", "tfidf"]
    dictionary_source: str | None = None
    dictionary_version: str | None = None
    dictionary_license_note: str | None = None
    dictionary_term_count: int | None = Field(default=None, ge=0)
    tfidf_params: dict[str, object] | None = None
    fit_scope: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    text_scope: str = Field(min_length=1)
    train_doc_count: int = Field(ge=0)
    validation_doc_count: int = Field(ge=0)
    test_doc_count: int = Field(ge=0)
    vocabulary_size: int = Field(ge=0)
    created_at_utc: datetime
    input_hashes: dict[str, str]

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_method_payload(self) -> FeatureManifestRecord:
        if self.feature_method == "dictionary_tone":
            if not self.dictionary_source or not self.dictionary_version:
                raise ValueError("dictionary_tone manifest requires dictionary metadata")
            if self.dictionary_term_count is None:
                raise ValueError("dictionary_tone manifest requires dictionary_term_count")
        if self.feature_method == "tfidf" and not self.tfidf_params:
            raise ValueError("tfidf manifest requires tfidf_params")
        return self
