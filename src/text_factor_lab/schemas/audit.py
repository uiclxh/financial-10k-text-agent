from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware
from text_factor_lab.schemas.run_status import AuditStatus, RunType

AuditCheckStatus = Literal["pass", "warn", "fail"]
AuditCheckSeverity = Literal["info", "warn", "fail"]
CoverageFailureStage = Literal[
    "ok_predicted",
    "not_oos_expected",
    "missing_split_assignment",
    "outside_configured_split_window",
    "missing_feature",
    "missing_model_prediction",
    "missing_price_window",
    "missing_benchmark",
    "label_window_unavailable",
    "filtered_by_portfolio_rule",
    "model_not_expected_for_target",
]


class AuditCheckRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    check_id: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    severity: AuditCheckSeverity
    status: AuditCheckStatus
    message: str = Field(min_length=1)
    affected_artifacts: list[str]
    observed_value: float | int | str | None = None
    threshold: float | int | str | None = None
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class AuditReportRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    run_type: RunType
    audit_status: AuditStatus
    formal_result_allowed: bool
    coverage: float = Field(ge=0, le=1)
    check_count: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    warn_count: int = Field(ge=0)
    checks: list[AuditCheckRecord]
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class CoverageFailureRecord(StrictBaseModel):
    label_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    event_date: date
    split_id: str | None = None
    expected_role: str | None = None
    failure_stage: CoverageFailureStage
    failure_reason: str = Field(min_length=1)
    expected_model_id: str | None = None
    observed_artifacts: list[str]
    recommended_fix: str = Field(min_length=1)
