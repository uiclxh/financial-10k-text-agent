from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from math import sqrt
from pathlib import Path
from typing import Any, Literal

import numpy as np

from text_factor_lab.data.prices import PricePanel, ReturnType
from text_factor_lab.schemas import (
    FactorPanelRecord,
    PortfolioMetricRecord,
    PortfolioReturnRecord,
    PortfolioWeightRecord,
)

ResolvedSignalDirection = Literal["long_high_score", "long_low_score"]
TargetAwarePortfolioPolicy = Literal["none", "long_low_vol", "risk_scaled"]


@dataclass(frozen=True)
class MonthlyPortfolioBuildResult:
    factor_panel: list[FactorPanelRecord]
    portfolio_weights: list[PortfolioWeightRecord]
    portfolio_returns: list[PortfolioReturnRecord]
    portfolio_metrics: list[PortfolioMetricRecord]


@dataclass(frozen=True)
class MonthlyVariant:
    name: str
    weighting: str
    sector_neutral: bool
    signal_direction: ResolvedSignalDirection
    target_aware_policy: TargetAwarePortfolioPolicy


def build_monthly_portfolio_artifacts(
    *,
    run_id: str,
    rows: list[Any],
    price_panel: PricePanel | None,
    portfolio_return_type: ReturnType,
    transaction_cost_bps_one_way: float,
    signal_direction: ResolvedSignalDirection = "long_high_score",
    target_aware_policy: TargetAwarePortfolioPolicy = "none",
    signal_expiry_days: int = 370,
) -> MonthlyPortfolioBuildResult:
    if price_panel is None or len(rows) < 2:
        return MonthlyPortfolioBuildResult([], [], [], [])

    price_dates = sorted(set(price_panel.frame["date"]))
    if len(price_dates) < 2:
        return MonthlyPortfolioBuildResult([], [], [], [])

    start_date = min(row.prediction.event_date for row in rows)
    end_date = max(row.label.label_end_date for row in rows)
    rebalance_dates = _month_end_rebalance_dates(price_dates, start_date, end_date)
    if len(rebalance_dates) < 2:
        return MonthlyPortfolioBuildResult([], [], [], [])

    all_factor_panel: list[FactorPanelRecord] = []
    all_weights: list[PortfolioWeightRecord] = []
    all_returns: list[PortfolioReturnRecord] = []
    all_metrics: list[PortfolioMetricRecord] = []
    now = datetime.now(UTC)

    for variant in _available_monthly_variants(
        rows,
        signal_direction,
        target_aware_policy,
    ):
        variant_weights: list[PortfolioWeightRecord] = []
        variant_returns: list[PortfolioReturnRecord] = []
        previous_weights: dict[str, float] = {}

        for rebalance_date, next_rebalance_date in zip(
            rebalance_dates[:-1],
            rebalance_dates[1:],
            strict=True,
        ):
            panel_rows = _active_factor_panel_rows(
                run_id=run_id,
                rows=rows,
                rebalance_date=rebalance_date,
                signal_expiry_days=signal_expiry_days,
                created_at_utc=now,
            )
            if variant.name == "monthly_equal_weight":
                all_factor_panel.extend(panel_rows)
            current_weights = _weights_from_factor_panel(
                panel_rows=panel_rows,
                run_id=run_id,
                variant=variant,
                holding_start_date=_next_price_date(price_dates, rebalance_date),
                holding_end_date=next_rebalance_date,
                previous_weights=previous_weights,
                created_at_utc=now,
            )
            if not current_weights:
                continue
            target_weights = {
                record.ticker: record.normalized_weight for record in current_weights
            }
            all_tickers = set(previous_weights) | set(target_weights)
            turnover = 0.5 * sum(
                abs(target_weights.get(ticker, 0.0) - previous_weights.get(ticker, 0.0))
                for ticker in all_tickers
            )
            current_weights = [
                record.model_copy(
                    update={
                        "previous_weight": previous_weights.get(record.ticker, 0.0),
                        "trade_weight": (
                            record.normalized_weight
                            - previous_weights.get(record.ticker, 0.0)
                        ),
                    }
                )
                for record in current_weights
            ]
            variant_weights.extend(current_weights)
            variant_returns.extend(
                _daily_returns_for_monthly_weights(
                    run_id=run_id,
                    model_id=current_weights[0].model_id,
                    split_id=current_weights[0].split_id,
                    target_name=current_weights[0].target_name,
                    variant=variant,
                    rebalance_date=rebalance_date,
                    next_rebalance_date=next_rebalance_date,
                    weights=target_weights,
                    turnover=turnover,
                    transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                    price_panel=price_panel,
                    portfolio_return_type=portfolio_return_type,
                    created_at_utc=now,
                )
            )
            previous_weights = target_weights

        if variant_returns:
            all_metrics.append(
                _portfolio_metric(
                    run_id=run_id,
                    model_id=variant_returns[0].model_id,
                    split_id=variant_returns[0].split_id,
                    target_name=variant_returns[0].target_name,
                    returns=variant_returns,
                    variant=variant,
                    created_at_utc=now,
                )
            )
        all_weights.extend(variant_weights)
        all_returns.extend(variant_returns)

    return MonthlyPortfolioBuildResult(
        factor_panel=all_factor_panel,
        portfolio_weights=all_weights,
        portfolio_returns=all_returns,
        portfolio_metrics=all_metrics,
    )


def aggregate_monthly_portfolio_metrics(
    records: list[PortfolioReturnRecord],
    *,
    run_id: str,
    created_at_utc: datetime | None = None,
) -> list[PortfolioMetricRecord]:
    grouped: dict[tuple[str, str, str, str, str, str, bool], list[PortfolioReturnRecord]]
    grouped = defaultdict(list)
    for record in records:
        if record.split_id == "ALL_SPLITS":
            continue
        if record.return_source != "monthly_common_rebalance_price_panel":
            continue
        key = (
            _aggregate_model_id(record.model_id, record.target_name),
            record.target_name,
            record.portfolio_variant,
            record.weighting,
            record.signal_direction,
            record.target_aware_policy,
            record.sector_neutral,
        )
        grouped[key].append(record)

    now = created_at_utc or datetime.now(UTC)
    metrics: list[PortfolioMetricRecord] = []
    for (
        model_id,
        target_name,
        portfolio_variant,
        weighting,
        signal_direction,
        target_aware_policy,
        sector_neutral,
    ), rows in sorted(grouped.items()):
        ordered_rows = sorted(rows, key=lambda item: (item.date, item.split_id, item.model_id))
        variant = MonthlyVariant(
            portfolio_variant,
            weighting,
            sector_neutral,
            signal_direction,
            target_aware_policy,
        )
        metric = _portfolio_metric(
            run_id=run_id,
            model_id=model_id,
            split_id="ALL_SPLITS",
            target_name=target_name,
            returns=ordered_rows,
            variant=variant,
            created_at_utc=now,
        )
        metrics.append(metric)
    return metrics


def _month_end_rebalance_dates(
    price_dates: list[date],
    start_date: date,
    end_date: date,
) -> list[date]:
    candidates = [day for day in price_dates if start_date <= day <= end_date]
    by_month: dict[tuple[int, int], date] = {}
    for day in candidates:
        by_month[(day.year, day.month)] = day
    return [by_month[key] for key in sorted(by_month)]


def _aggregate_model_id(model_id: str, target_name: str) -> str:
    parts = model_id.split("::")
    if len(parts) >= 2 and parts[1] == target_name:
        return f"{parts[0]}::{target_name}::ALL_SPLITS"
    if parts:
        return f"{parts[0]}::{target_name}::ALL_SPLITS"
    return f"{model_id}::{target_name}::ALL_SPLITS"


def _next_price_date(price_dates: list[date], rebalance_date: date) -> date:
    for day in price_dates:
        if day > rebalance_date:
            return day
    return rebalance_date


def _available_monthly_variants(
    rows: list[Any],
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
) -> list[MonthlyVariant]:
    variants = [
        MonthlyVariant(
            "monthly_equal_weight",
            "equal_weight",
            False,
            signal_direction,
            target_aware_policy,
        )
    ]
    if all(row.prediction.market_cap is not None for row in rows):
        variants.append(
            MonthlyVariant(
                "monthly_value_weight",
                "value_weight",
                False,
                signal_direction,
                target_aware_policy,
            )
        )
    if all(row.prediction.sector for row in rows):
        variants.append(
            MonthlyVariant(
                "monthly_sector_neutral_equal_weight",
                "equal_weight",
                True,
                signal_direction,
                target_aware_policy,
            )
        )
    if all(row.prediction.sector and row.prediction.market_cap is not None for row in rows):
        variants.append(
            MonthlyVariant(
                "monthly_sector_neutral_value_weight",
                "value_weight",
                True,
                signal_direction,
                target_aware_policy,
            )
        )
    return variants


def _active_factor_panel_rows(
    *,
    run_id: str,
    rows: list[Any],
    rebalance_date: date,
    signal_expiry_days: int,
    created_at_utc: datetime,
) -> list[FactorPanelRecord]:
    latest_by_ticker: dict[str, tuple[Any, int]] = {}
    for row in sorted(rows, key=lambda item: item.prediction.event_date):
        age_days = (rebalance_date - row.prediction.event_date).days
        if age_days < 0 or age_days > signal_expiry_days:
            continue
        latest_by_ticker[row.prediction.ticker] = (row, age_days)
    active_rows = sorted(
        latest_by_ticker.values(),
        key=lambda item: (item[0].prediction.factor_score, item[0].prediction.ticker),
    )
    count = len(active_rows)
    records: list[FactorPanelRecord] = []
    for rank_index, (row, age_days) in enumerate(active_rows, start=1):
        quantile = min(5, max(1, int(np.ceil(rank_index * 5.0 / max(count, 1)))))
        records.append(
            FactorPanelRecord(
                run_id=run_id,
                model_id=row.prediction.model_id,
                split_id=row.prediction.split_id,
                target_name=row.prediction.target_name,
                rebalance_date=rebalance_date,
                ticker=row.prediction.ticker,
                entity_id=row.label.entity_id,
                sector=row.prediction.sector,
                industry=row.prediction.industry,
                market_cap=row.prediction.market_cap,
                signal_event_date=row.prediction.event_date,
                signal_age_days=age_days,
                factor_score=row.prediction.factor_score,
                rank=rank_index,
                quantile=quantile,
                is_active=True,
                created_at_utc=created_at_utc,
            )
        )
    return records


def _weights_from_factor_panel(
    *,
    panel_rows: list[FactorPanelRecord],
    run_id: str,
    variant: MonthlyVariant,
    holding_start_date: date,
    holding_end_date: date,
    previous_weights: dict[str, float],
    created_at_utc: datetime,
) -> list[PortfolioWeightRecord]:
    del previous_weights
    if len(panel_rows) < 2:
        return []
    if variant.sector_neutral:
        selected = _sector_neutral_panel_weights(panel_rows, variant)
    else:
        selected = _panel_leg_weights(
            panel_rows,
            variant.weighting,
            gross_allocation=2.0,
            signal_direction=variant.signal_direction,
            target_aware_policy=variant.target_aware_policy,
            target_name=panel_rows[0].target_name if panel_rows else "",
        )
    if not selected:
        return []
    records: list[PortfolioWeightRecord] = []
    for row in panel_rows:
        weight = selected.get(row.ticker)
        if weight is None:
            continue
        side = "long" if weight > 0 else "short"
        records.append(
            PortfolioWeightRecord(
                run_id=run_id,
                model_id=row.model_id,
                split_id=row.split_id,
                target_name=row.target_name,
                portfolio_variant=variant.name,
                weighting=variant.weighting,
                signal_direction=variant.signal_direction,
                target_aware_policy=variant.target_aware_policy,
                sector_neutral=variant.sector_neutral,
                rebalance_date=row.rebalance_date,
                holding_start_date=holding_start_date,
                holding_end_date=holding_end_date,
                ticker=row.ticker,
                entity_id=row.entity_id,
                sector=row.sector,
                industry=row.industry,
                market_cap=row.market_cap,
                factor_score=row.factor_score,
                rank=row.rank,
                quantile=row.quantile,
                side=side,
                raw_weight=weight,
                normalized_weight=weight,
                previous_weight=0.0,
                trade_weight=weight,
                created_at_utc=created_at_utc,
            )
        )
    return records


def _sector_neutral_panel_weights(
    panel_rows: list[FactorPanelRecord],
    variant: MonthlyVariant,
) -> dict[str, float]:
    by_sector: dict[str, list[FactorPanelRecord]] = defaultdict(list)
    for row in panel_rows:
        if row.sector:
            by_sector[row.sector].append(row)
    eligible = {sector: rows for sector, rows in by_sector.items() if len(rows) >= 2}
    if not eligible:
        return {}
    gross_allocation = 2.0 / len(eligible)
    selected: dict[str, float] = {}
    for sector_rows in eligible.values():
        selected.update(
            _panel_leg_weights(
                sorted(sector_rows, key=lambda item: item.factor_score),
                variant.weighting,
                gross_allocation=gross_allocation,
                signal_direction=variant.signal_direction,
                target_aware_policy=variant.target_aware_policy,
                target_name=sector_rows[0].target_name if sector_rows else "",
            )
        )
    return selected


def _panel_leg_weights(
    rows: list[FactorPanelRecord],
    weighting: str,
    *,
    gross_allocation: float,
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
    target_name: str,
) -> dict[str, float]:
    if len(rows) < 2:
        return {}
    sorted_rows = sorted(rows, key=lambda item: item.factor_score)
    leg_size = max(1, int(len(sorted_rows) * 0.2))
    short_rows = sorted_rows[:leg_size]
    long_rows = sorted_rows[-leg_size:]
    if signal_direction == "long_low_score":
        long_rows, short_rows = short_rows, long_rows
    use_risk_scaled = (
        target_aware_policy == "risk_scaled" and _is_volatility_target(target_name)
    )
    weights: dict[str, float] = {}
    for row, weight in _side_weights(
        long_rows,
        weighting,
        gross_allocation / 2.0,
        risk_scaled=use_risk_scaled,
    ):
        weights[row.ticker] = weight
    for row, weight in _side_weights(
        short_rows,
        weighting,
        gross_allocation / 2.0,
        risk_scaled=use_risk_scaled,
    ):
        weights[row.ticker] = -weight
    return weights


def _side_weights(
    rows: list[FactorPanelRecord],
    weighting: str,
    allocation: float,
    *,
    risk_scaled: bool = False,
) -> list[tuple[FactorPanelRecord, float]]:
    if risk_scaled:
        inverse_vol_weights = [
            1.0 / max(abs(float(row.factor_score)), 1e-6)
            for row in rows
        ]
        denominator = sum(inverse_vol_weights)
        if denominator > 0:
            return [
                (row, allocation * inverse_vol_weight / denominator)
                for row, inverse_vol_weight in zip(rows, inverse_vol_weights, strict=True)
            ]
    if weighting == "value_weight" and all(row.market_cap for row in rows):
        denominator = sum(float(row.market_cap or 0.0) for row in rows)
        if denominator > 0:
            return [
                (row, allocation * float(row.market_cap or 0.0) / denominator)
                for row in rows
            ]
    return [(row, allocation / len(rows)) for row in rows]


def _is_volatility_target(target_name: str) -> bool:
    return "volatility" in target_name.lower() or target_name.lower().startswith(
        "realized_vol"
    )


def _daily_returns_for_monthly_weights(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    variant: MonthlyVariant,
    rebalance_date: date,
    next_rebalance_date: date,
    weights: dict[str, float],
    turnover: float,
    transaction_cost_bps_one_way: float,
    price_panel: PricePanel,
    portfolio_return_type: ReturnType,
    created_at_utc: datetime,
) -> list[PortfolioReturnRecord]:
    return_column = f"{portfolio_return_type}_return"
    frame = price_panel.frame
    subset = frame[
        frame["ticker"].isin(weights)
        & (frame["date"] > rebalance_date)
        & (frame["date"] <= next_rebalance_date)
    ]
    if subset.empty:
        return []
    records: list[PortfolioReturnRecord] = []
    current_weights = dict(weights)
    first_return = True
    for holding_date, day_rows in subset.groupby("date", sort=True):
        ticker_returns = {
            str(row.ticker): float(getattr(row, return_column))
            for row in day_rows.itertuples(index=False)
            if not np.isnan(float(getattr(row, return_column)))
        }
        usable_weights = {
            ticker: weight for ticker, weight in current_weights.items() if ticker in ticker_returns
        }
        if not usable_weights:
            continue
        long_return = sum(
            weight * ticker_returns[ticker]
            for ticker, weight in usable_weights.items()
            if weight > 0
        )
        short_return = sum(
            weight * ticker_returns[ticker]
            for ticker, weight in usable_weights.items()
            if weight < 0
        )
        gross_return = float(long_return + short_return)
        row_turnover = turnover if first_return else 0.0
        transaction_cost = row_turnover * transaction_cost_bps_one_way / 10_000.0
        long_exposure, short_exposure, gross_exposure, net_exposure = _weight_exposures(
            usable_weights
        )
        next_weights = _drift_position_weights(
            weights=usable_weights,
            ticker_returns=ticker_returns,
            portfolio_return=gross_return,
        )
        (
            ending_long_exposure,
            ending_short_exposure,
            ending_gross_exposure,
            ending_net_exposure,
        ) = _weight_exposures(next_weights)
        records.append(
            PortfolioReturnRecord(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                portfolio_variant=variant.name,
                weighting=variant.weighting,
                signal_direction=variant.signal_direction,
                target_aware_policy=variant.target_aware_policy,
                sector_neutral=variant.sector_neutral,
                return_source="monthly_common_rebalance_price_panel",
                position_accounting="monthly_rebalance_drifted_daily_positions",
                date=holding_date,
                rebalance_date=rebalance_date,
                gross_long_return=float(long_return),
                gross_short_return=float(short_return),
                gross_long_short_return=gross_return,
                transaction_cost=float(transaction_cost),
                net_long_short_return=float(gross_return - transaction_cost),
                long_exposure=long_exposure,
                short_exposure=short_exposure,
                gross_exposure=gross_exposure,
                net_exposure=net_exposure,
                ending_long_exposure=ending_long_exposure,
                ending_short_exposure=ending_short_exposure,
                ending_gross_exposure=ending_gross_exposure,
                ending_net_exposure=ending_net_exposure,
                turnover=float(row_turnover),
                active_position_count=len(usable_weights),
                created_at_utc=created_at_utc,
            )
        )
        current_weights = next_weights
        first_return = False
    return records


def _weight_exposures(weights: dict[str, float]) -> tuple[float, float, float, float]:
    long_exposure = float(sum(weight for weight in weights.values() if weight > 0))
    short_exposure = float(sum(weight for weight in weights.values() if weight < 0))
    gross_exposure = float(sum(abs(weight) for weight in weights.values()))
    net_exposure = float(sum(weights.values()))
    return long_exposure, short_exposure, gross_exposure, net_exposure


def _drift_position_weights(
    *,
    weights: dict[str, float],
    ticker_returns: dict[str, float],
    portfolio_return: float,
) -> dict[str, float]:
    denominator = 1.0 + portfolio_return
    if denominator <= 0.0:
        return dict(weights)
    return {
        ticker: weight * (1.0 + ticker_returns[ticker]) / denominator
        for ticker, weight in weights.items()
        if ticker in ticker_returns
    }


def _portfolio_metric(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    returns: list[PortfolioReturnRecord],
    variant: MonthlyVariant,
    created_at_utc: datetime,
) -> PortfolioMetricRecord:
    values = np.array([record.net_long_short_return for record in returns], dtype=float)
    cumulative = float(np.prod(1.0 + values) - 1.0)
    periods_per_year = 252.0
    annualized_return = float((1.0 + cumulative) ** (periods_per_year / len(values)) - 1.0)
    annualized_volatility = (
        float(np.std(values, ddof=1) * sqrt(periods_per_year)) if len(values) > 1 else 0.0
    )
    sharpe_ratio = (
        float(np.mean(values) / np.std(values, ddof=1) * sqrt(periods_per_year))
        if len(values) > 1 and np.std(values, ddof=1)
        else 0.0
    )
    newey_west_lag = min(21, max(len(values) - 1, 0))
    equity_curve = np.cumprod(1.0 + values)
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = equity_curve / running_max - 1.0
    return PortfolioMetricRecord(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        portfolio_variant=variant.name,
        portfolio_method="monthly_common_rebalance_top_bottom_quintile",
        weighting=variant.weighting,
        signal_direction=variant.signal_direction,
        target_aware_policy=variant.target_aware_policy,
        sector_neutral=variant.sector_neutral,
        observation_count=len(returns),
        cumulative_return=cumulative,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=sharpe_ratio,
        mean_period_return=float(np.mean(values)),
        period_return_t_stat=_mean_t_stat(values),
        newey_west_lag=newey_west_lag,
        newey_west_t_stat=_newey_west_t_stat(values, newey_west_lag),
        max_drawdown=float(np.min(drawdowns)),
        hit_rate=float(np.mean(values > 0)),
        average_turnover=float(np.mean([record.turnover for record in returns])),
        average_gross_exposure=float(np.mean([record.gross_exposure for record in returns])),
        average_net_exposure=float(np.mean([record.net_exposure for record in returns])),
        created_at_utc=created_at_utc,
    )


def _mean_t_stat(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    standard_error = float(np.std(values, ddof=1) / sqrt(len(values)))
    if standard_error == 0.0:
        return 0.0
    return float(values.mean() / standard_error)


def _newey_west_t_stat(values: np.ndarray, lag: int) -> float:
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n < 2:
        return 0.0
    centered = values - values.mean()
    gamma0 = float(np.dot(centered, centered) / n)
    variance = gamma0
    max_lag = min(lag, n - 1)
    for lag_index in range(1, max_lag + 1):
        covariance = float(np.dot(centered[lag_index:], centered[:-lag_index]) / n)
        weight = 1.0 - lag_index / (max_lag + 1)
        variance += 2.0 * weight * covariance
    variance = max(variance / n, 0.0)
    if variance == 0.0:
        return 0.0
    return float(values.mean() / sqrt(variance))


def write_factor_panel_jsonl(records: list[FactorPanelRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")
