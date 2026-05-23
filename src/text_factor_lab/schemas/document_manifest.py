from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

DocumentType = Literal["10-K", "10-Q", "earnings_call"]


class DocumentManifestRecord(StrictBaseModel):
    document_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    cik: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    document_type: DocumentType
    fiscal_year: int
    fiscal_period: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url_or_path: str = Field(min_length=1)
    retrieval_time_utc: datetime
    available_time_utc: datetime
    event_time_utc: datetime
    event_date: date
    raw_filing_date: date | None = None
    acceptance_time_utc: datetime | None = None
    market_open_utc: datetime | None = None
    market_close_utc: datetime | None = None
    is_trading_day: bool | None = None
    is_early_close: bool | None = None
    event_date_policy: str | None = None
    resolved_event_date: date | None = None
    resolved_event_time_version: str | None = None
    timezone: str = Field(min_length=1)
    hash_sha256: str = Field(min_length=64, max_length=64)
    license_note: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)

    @field_validator(
        "retrieval_time_utc",
        "available_time_utc",
        "event_time_utc",
        "acceptance_time_utc",
        "market_open_utc",
        "market_close_utc",
    )
    @classmethod
    def validate_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if not is_timezone_aware(value):
            raise ValueError("datetime fields must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_time_order(self) -> DocumentManifestRecord:
        if self.available_time_utc < self.event_time_utc:
            raise ValueError("available_time_utc must be after or equal to event_time_utc")
        return self

