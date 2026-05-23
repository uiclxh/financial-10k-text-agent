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


class SecurityMasterRecord(StrictBaseModel):
    entity_id: str = Field(min_length=1)
    permno: str | None = None
    permco: str | None = None
    gvkey: str | None = None
    cik: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    historical_ticker: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    name_start_date: date | None = None
    name_end_date: date | None = None
    exchange: str = Field(min_length=1)
    share_class: str = Field(min_length=1)
    security_type: str = Field(min_length=1)
    sic: str | None = None
    naics: str | None = None
    gics_sector: str | None = None
    gics_industry: str | None = None
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    available_time_utc: datetime

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

    @field_validator(
        "permno",
        "permco",
        "gvkey",
        "sic",
        "naics",
        "gics_sector",
        "gics_industry",
        "name_start_date",
        "name_end_date",
        mode="before",
    )
    @classmethod
    def parse_optional_values(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("available_time_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("available_time_utc must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_name_date_order(self) -> SecurityMasterRecord:
        if (
            self.name_start_date
            and self.name_end_date
            and self.name_start_date > self.name_end_date
        ):
            raise ValueError("name_start_date must be before or equal to name_end_date")
        return self


class UniverseMembershipRecord(StrictBaseModel):
    universe_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    selection_date: date
    entry_date: date
    exit_date: date | None = None
    delisting_date: date | None = None
    selection_rank: int | None = Field(default=None, gt=0)
    market_cap_at_selection: float | None = Field(default=None, gt=0)
    price_at_selection: float | None = Field(default=None, gt=0)
    shares_outstanding_at_selection: float | None = Field(default=None, gt=0)
    liquidity_filter_pass: bool
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator(
        "exit_date",
        "delisting_date",
        "selection_rank",
        "market_cap_at_selection",
        "price_at_selection",
        "shares_outstanding_at_selection",
        mode="before",
    )
    @classmethod
    def parse_optional_values(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("liquidity_filter_pass", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return value

    @model_validator(mode="after")
    def validate_interval(self) -> UniverseMembershipRecord:
        if self.entry_date < self.selection_date:
            raise ValueError("entry_date must be on or after selection_date")
        if self.exit_date and self.entry_date > self.exit_date:
            raise ValueError("entry_date must be before or equal to exit_date")
        if self.delisting_date and self.entry_date > self.delisting_date:
            raise ValueError("entry_date must be before or equal to delisting_date")
        if self.exit_date and self.delisting_date and self.exit_date > self.delisting_date:
            raise ValueError("exit_date must be before or equal to delisting_date")
        return self


class EntityLinkHistoryRecord(StrictBaseModel):
    entity_id: str = Field(min_length=1)
    cik: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    permno: str | None = None
    gvkey: str | None = None
    link_start_date: date
    link_end_date: date | None = None
    link_type: str = Field(min_length=1)
    link_confidence: float = Field(ge=0, le=1)
    source: str = Field(min_length=1)

    @field_validator("ticker")
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

    @field_validator("permno", "gvkey", "link_end_date", mode="before")
    @classmethod
    def parse_optional_values(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_link_dates(self) -> EntityLinkHistoryRecord:
        if self.link_end_date and self.link_start_date > self.link_end_date:
            raise ValueError("link_start_date must be before or equal to link_end_date")
        return self


class UniverseQualityReport(StrictBaseModel):
    universe_name: str
    universe_data_level: str = "exploratory"
    source_path: str
    security_master_path: str | None = None
    membership_path: str | None = None
    entity_link_history_path: str | None = None
    rows_total: int
    security_master_rows: int = 0
    membership_rows: int = 0
    entity_link_rows: int = 0
    unique_entities: int
    unique_tickers: int
    duplicate_entity_ids: list[str]
    duplicate_tickers: list[str]
    placeholder_mapping_rows: int
    missing_market_cap_rows: int
    delisted_rows: int
    selection_date_after_sample_start_rows: int
    mapping_available_after_selection_rows: int
    membership_without_security_master_rows: int = 0
    membership_without_entity_link_rows: int = 0
    low_confidence_link_rows: int = 0
    membership_selection_after_sample_start_rows: int = 0
    membership_missing_market_cap_rows: int = 0
    membership_delisted_rows: int = 0
    coverage: float = Field(ge=0, le=1)
    warnings: list[str]
    formal_run_blockers: list[str]
    is_research_grade: bool
