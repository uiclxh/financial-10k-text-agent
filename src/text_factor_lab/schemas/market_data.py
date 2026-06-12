from __future__ import annotations

from datetime import date, datetime

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware


class CRSPDailyReturnRecord(StrictBaseModel):
    permno: str = Field(min_length=1)
    permco: str | None = None
    date: date
    ticker: str | None = None
    ret: float | None = None
    retx: float | None = None
    prc: float | None = None
    shrout: float | None = None
    volume: float | None = None
    exchcd: int | None = None
    shrcd: int | None = None
    siccd: str | None = None
    source_version: str = Field(min_length=1)

    @field_validator(
        "permco",
        "ticker",
        "ret",
        "retx",
        "prc",
        "shrout",
        "volume",
        "exchcd",
        "shrcd",
        "siccd",
        mode="before",
    )
    @classmethod
    def parse_optional_values(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class CRSPDelistingReturnRecord(StrictBaseModel):
    permno: str = Field(min_length=1)
    dlstdt: date
    dlret: float | None = None
    dlstcd: str | None = None
    delisting_reason: str | None = None
    source_version: str = Field(min_length=1)

    @field_validator("dlret", "dlstcd", "delisting_reason", mode="before")
    @classmethod
    def parse_optional_values(cls, value: object) -> object:
        if value == "":
            return None
        return value


class DataLicenseManifestRecord(StrictBaseModel):
    data_stack: str = Field(min_length=1)
    market_data_provider: str = Field(min_length=1)
    filing_provider: str = Field(min_length=1)
    price_source: str = Field(min_length=1)
    return_source: str = Field(min_length=1)
    delisting_return_source: str | None = None
    link_source: str | None = None
    data_owner: str | None = None
    data_rights_scope: str | None = None
    input_files: dict[str, str] = Field(default_factory=dict)
    permitted_public_outputs: list[str] = Field(default_factory=list)
    license_note: str = Field(min_length=1)
    raw_data_committed: bool = False
    allow_public_yahoo_fallback: bool = False
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
