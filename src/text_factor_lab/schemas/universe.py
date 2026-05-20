from __future__ import annotations

from datetime import date, datetime

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware


class UniverseRecord(StrictBaseModel):
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    historical_ticker: str = Field(min_length=1)
    cik: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    selection_date: date
    market_cap_at_selection: float | None = None
    entry_date: date | None = None
    exit_date: date | None = None
    delisting_date: date | None = None
    mapping_source: str = Field(min_length=1)
    mapping_available_time_utc: datetime

    @field_validator("ticker", "historical_ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("cik")
    @classmethod
    def normalize_cik(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit():
            raise ValueError("cik must contain only digits")
        if len(cleaned) > 10:
            raise ValueError("cik must not exceed 10 digits")
        return cleaned.zfill(10)

    @field_validator("mapping_available_time_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("mapping_available_time_utc must be timezone-aware")
        return value

    @field_validator("market_cap_at_selection", mode="before")
    @classmethod
    def parse_optional_market_cap(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("entry_date", "exit_date", "delisting_date", mode="before")
    @classmethod
    def parse_optional_dates(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_date_order(self) -> UniverseRecord:
        if self.entry_date and self.exit_date and self.entry_date > self.exit_date:
            raise ValueError("entry_date must be before or equal to exit_date")
        if self.entry_date and self.delisting_date and self.entry_date > self.delisting_date:
            raise ValueError("entry_date must be before or equal to delisting_date")
        if self.exit_date and self.delisting_date and self.exit_date > self.delisting_date:
            raise ValueError("exit_date must be before or equal to delisting_date")
        return self


class UniverseQualityReport(StrictBaseModel):
    universe_name: str
    source_path: str
    rows_total: int
    unique_entities: int
    unique_tickers: int
    duplicate_entity_ids: list[str]
    duplicate_tickers: list[str]
    placeholder_mapping_rows: int
    missing_market_cap_rows: int
    delisted_rows: int
    selection_date_after_sample_start_rows: int
    mapping_available_after_selection_rows: int
    coverage: float = Field(ge=0, le=1)
    warnings: list[str]
    formal_run_blockers: list[str]
    is_research_grade: bool
