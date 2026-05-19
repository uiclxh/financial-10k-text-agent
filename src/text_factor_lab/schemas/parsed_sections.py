from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware
from text_factor_lab.schemas.document_manifest import DocumentType

ParserStatus = Literal["parsed", "missing", "failed"]
SectionKey = Literal["item_1", "item_1a", "item_3", "item_7"]


class ParsedSectionRecord(StrictBaseModel):
    section_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    cik: str = Field(min_length=1)
    document_type: DocumentType
    fiscal_year: int
    section_key: SectionKey
    section_name: str = Field(min_length=1)
    parser_status: ParserStatus
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    text_length: int = Field(ge=0)
    text_hash_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    source_hash_sha256: str = Field(min_length=64, max_length=64)
    artifact_path: str | None = None
    parser_version: str = Field(min_length=1)
    failure_reason: str | None = None
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_status_payload(self) -> ParsedSectionRecord:
        if self.parser_status == "parsed":
            if self.char_start is None or self.char_end is None:
                raise ValueError("parsed sections require char_start and char_end")
            if self.char_end <= self.char_start:
                raise ValueError("parsed sections require char_end > char_start")
            if self.text_length <= 0:
                raise ValueError("parsed sections require text_length > 0")
            if self.text_hash_sha256 is None:
                raise ValueError("parsed sections require text_hash_sha256")
            if self.failure_reason is not None:
                raise ValueError("parsed sections must not include failure_reason")
        else:
            if self.failure_reason is None:
                raise ValueError("missing or failed sections require failure_reason")
            if self.text_length != 0:
                raise ValueError("missing or failed sections must have text_length=0")
        return self
