from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Literal

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

SpecificationRole = Literal["primary", "robustness", "exploratory"]


class TestedSpecificationRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    spec_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    label_window: str = Field(min_length=1)
    text_source: str = Field(min_length=1)
    section: str = Field(min_length=1)
    feature_method: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    hyperparameter_grid_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    split_method: str = Field(min_length=1)
    portfolio_method: str = Field(min_length=1)
    weighting: str = Field(min_length=1)
    signal_direction: str = Field(default="not_applicable", min_length=1)
    target_aware_policy: str = Field(default="none", min_length=1)
    sector_neutral: bool
    transaction_cost_bps_one_way: float | None = Field(default=None, ge=0)
    metric_name: str = Field(min_length=1)
    raw_metric: float
    raw_p_value: float | None = Field(default=None, ge=0, le=1)
    p_value_method: str = Field(default="unspecified", min_length=1)
    specification_role: SpecificationRole = "exploratory"
    preregistered: bool = False
    specification_rationale: str = "Auto-classified by the specification registry policy."
    created_at_utc: datetime

    @field_validator("transaction_cost_bps_one_way", "raw_metric", "raw_p_value")
    @classmethod
    def validate_finite_float(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not isfinite(value):
            raise ValueError("inference numeric fields must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class MultipleTestingFamilyRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    base_family_id: str | None = None
    specification_role: SpecificationRole = "exploratory"
    number_of_tests: int = Field(ge=0)
    methods_applied: list[str]
    raw_p_values: list[float]
    bonferroni_adjusted_p_values: list[float]
    holm_adjusted_p_values: list[float]
    bh_fdr_adjusted_p_values: list[float]
    best_raw_spec_id: str | None = None
    best_raw_p_value: float | None = Field(default=None, ge=0, le=1)
    best_adjusted_spec_id: str | None = None
    best_adjusted_p_value: float | None = Field(default=None, ge=0, le=1)
    discoveries_at_5pct: int = Field(ge=0)
    discoveries_at_10pct: int = Field(ge=0)
    created_at_utc: datetime

    @field_validator(
        "raw_p_values",
        "bonferroni_adjusted_p_values",
        "holm_adjusted_p_values",
        "bh_fdr_adjusted_p_values",
    )
    @classmethod
    def validate_p_value_lists(cls, values: list[float]) -> list[float]:
        if any(not isfinite(value) or value < 0 or value > 1 for value in values):
            raise ValueError("p-value lists must contain finite values in [0, 1]")
        return values

    @field_validator("best_raw_p_value", "best_adjusted_p_value")
    @classmethod
    def validate_optional_p_value(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not isfinite(value):
            raise ValueError("best p-values must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class MultipleTestingReportRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    report_version: str = Field(min_length=1)
    specification_count: int = Field(ge=0)
    primary_specification_count: int = Field(default=0, ge=0)
    robustness_specification_count: int = Field(default=0, ge=0)
    exploratory_specification_count: int = Field(default=0, ge=0)
    p_value_count: int = Field(ge=0)
    family_count: int = Field(ge=0)
    role_family_counts: dict[str, int] = Field(default_factory=dict)
    primary_discoveries_at_5pct: int = Field(default=0, ge=0)
    primary_discoveries_at_10pct: int = Field(default=0, ge=0)
    robustness_discoveries_at_10pct: int = Field(default=0, ge=0)
    exploratory_discoveries_at_10pct: int = Field(default=0, ge=0)
    methods_applied: list[str]
    families: list[MultipleTestingFamilyRecord]
    created_at_utc: datetime

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
