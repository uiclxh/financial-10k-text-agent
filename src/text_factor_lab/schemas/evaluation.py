from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Literal

from pydantic import Field, field_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

EvaluationRole = Literal["validation", "test", "all"]


class EvaluationMetricRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    role: EvaluationRole
    observation_count: int = Field(ge=0)
    rmse: float
    mae: float
    r_squared: float
    directional_accuracy: float = Field(ge=0, le=1)
    pearson_ic: float
    rank_ic: float
    created_at_utc: datetime

    @field_validator("rmse", "mae", "r_squared", "pearson_ic", "rank_ic")
    @classmethod
    def validate_finite_metric(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("evaluation metrics must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class PortfolioBacktestRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    role: Literal["test"]
    portfolio_method: str = Field(min_length=1)
    weighting: str = Field(min_length=1)
    rebalance_frequency: str = Field(min_length=1)
    long_count: int = Field(ge=0)
    short_count: int = Field(ge=0)
    gross_long_short_return: float
    turnover: float = Field(ge=0)
    transaction_cost_bps_one_way: float = Field(ge=0)
    net_long_short_return: float
    sharpe_ratio: float
    newey_west_lag: int = Field(ge=0)
    newey_west_t_stat: float
    created_at_utc: datetime

    @field_validator(
        "gross_long_short_return",
        "net_long_short_return",
        "sharpe_ratio",
        "newey_west_t_stat",
    )
    @classmethod
    def validate_finite_metric(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("portfolio metrics must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
