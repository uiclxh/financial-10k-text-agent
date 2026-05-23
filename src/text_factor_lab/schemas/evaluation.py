from __future__ import annotations

from datetime import date, datetime
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


class PortfolioWeightRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    portfolio_variant: str = "equal_weight"
    weighting: str = "equal_weight"
    sector_neutral: bool = False
    rebalance_date: date
    holding_start_date: date
    holding_end_date: date
    ticker: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = Field(default=None, gt=0)
    factor_score: float
    rank: int = Field(ge=1)
    quantile: int = Field(ge=1)
    side: Literal["long", "short", "neutral"]
    raw_weight: float
    normalized_weight: float
    previous_weight: float
    trade_weight: float
    created_at_utc: datetime

    @field_validator(
        "factor_score",
        "raw_weight",
        "normalized_weight",
        "previous_weight",
        "trade_weight",
    )
    @classmethod
    def validate_finite_weight_metric(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("portfolio weight fields must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class PortfolioReturnRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    portfolio_variant: str = "equal_weight"
    weighting: str = "equal_weight"
    sector_neutral: bool = False
    date: date
    rebalance_date: date
    gross_long_return: float
    gross_short_return: float
    gross_long_short_return: float
    transaction_cost: float
    net_long_short_return: float
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    turnover: float = Field(ge=0)
    active_position_count: int = Field(ge=0)
    created_at_utc: datetime

    @field_validator(
        "gross_long_return",
        "gross_short_return",
        "gross_long_short_return",
        "transaction_cost",
        "net_long_short_return",
        "long_exposure",
        "short_exposure",
        "gross_exposure",
        "net_exposure",
    )
    @classmethod
    def validate_finite_return_metric(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("portfolio return fields must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value


class PortfolioMetricRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    split_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    portfolio_variant: str = "equal_weight"
    portfolio_method: str = Field(min_length=1)
    weighting: str = Field(min_length=1)
    sector_neutral: bool = False
    observation_count: int = Field(ge=0)
    cumulative_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    hit_rate: float = Field(ge=0, le=1)
    average_turnover: float = Field(ge=0)
    average_gross_exposure: float = Field(ge=0)
    average_net_exposure: float
    created_at_utc: datetime

    @field_validator(
        "cumulative_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "average_net_exposure",
    )
    @classmethod
    def validate_finite_metric(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("portfolio metric fields must be finite")
        return value

    @field_validator("created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("created_at_utc must be timezone-aware")
        return value
