from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from math import sqrt
from pathlib import Path
from typing import Literal

import numpy as np

from text_factor_lab.backtest.monthly import (
    aggregate_monthly_portfolio_metrics,
    build_monthly_portfolio_artifacts,
)
from text_factor_lab.data.prices import PricePanel, ReturnType
from text_factor_lab.models import rank_ic
from text_factor_lab.ranking import average_ranks, tie_aware_extreme_indices
from text_factor_lab.schemas import (
    EvaluationMetricRecord,
    FactorPanelRecord,
    LabelRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    PortfolioReturnRecord,
    PortfolioWeightRecord,
    PredictionRecord,
)

BACKTEST_VERSION = "backtest-evaluation-v2-tie-aware-portfolio"
PortfolioSignalDirection = Literal[
    "long_high_score",
    "long_low_score",
    "validation_selected",
]
ResolvedSignalDirection = Literal["long_high_score", "long_low_score"]
TargetAwarePortfolioPolicy = Literal["none", "long_low_vol", "risk_scaled"]


@dataclass(frozen=True)
class ScoredPrediction:
    prediction: PredictionRecord
    label: LabelRecord


@dataclass(frozen=True)
class EvaluationBuildResult:
    metrics: list[EvaluationMetricRecord]
    backtests: list[PortfolioBacktestRecord]
    portfolio_weights: list[PortfolioWeightRecord]
    portfolio_returns: list[PortfolioReturnRecord]
    portfolio_metrics: list[PortfolioMetricRecord]
    factor_panel: list[FactorPanelRecord]
    monthly_portfolio_weights: list[PortfolioWeightRecord]
    monthly_portfolio_returns: list[PortfolioReturnRecord]
    monthly_portfolio_metrics: list[PortfolioMetricRecord]
    delisting_application_report: dict[str, int | float | str]


@dataclass(frozen=True)
class PortfolioVariant:
    name: str
    weighting: str
    sector_neutral: bool
    signal_direction: ResolvedSignalDirection
    target_aware_policy: TargetAwarePortfolioPolicy


def read_predictions_jsonl(path: str | Path) -> list[PredictionRecord]:
    records: list[PredictionRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(PredictionRecord.model_validate(json.loads(line)))
    return records


def read_labels_jsonl(path: str | Path) -> list[LabelRecord]:
    records: list[LabelRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(LabelRecord.model_validate(json.loads(line)))
    return records


def build_evaluation_artifacts(
    *,
    run_id: str,
    predictions: list[PredictionRecord],
    labels: list[LabelRecord],
    price_panel: PricePanel | None = None,
    portfolio_return_type: ReturnType = "simple",
    transaction_cost_bps_one_way: float = 10.0,
    newey_west_lag: int = 19,
    portfolio_signal_direction: PortfolioSignalDirection = "long_high_score",
    target_aware_portfolio_policy: TargetAwarePortfolioPolicy = "none",
) -> EvaluationBuildResult:
    labels_by_id = {label.label_id: label for label in labels}
    scored = [
        ScoredPrediction(prediction=prediction, label=labels_by_id[prediction.label_id])
        for prediction in predictions
        if prediction.label_id is not None and prediction.label_id in labels_by_id
    ]
    grouped = _group_scored_predictions(scored)
    signal_directions = _resolved_signal_directions(
        grouped,
        portfolio_signal_direction,
        target_aware_portfolio_policy,
    )
    metrics: list[EvaluationMetricRecord] = []
    backtests: list[PortfolioBacktestRecord] = []
    portfolio_weights: list[PortfolioWeightRecord] = []
    portfolio_returns: list[PortfolioReturnRecord] = []
    portfolio_metrics: list[PortfolioMetricRecord] = []
    factor_panel: list[FactorPanelRecord] = []
    monthly_portfolio_weights: list[PortfolioWeightRecord] = []
    monthly_portfolio_returns: list[PortfolioReturnRecord] = []
    monthly_portfolio_metrics: list[PortfolioMetricRecord] = []

    for (model_id, split_id, target_name, role), rows in sorted(grouped.items()):
        metrics.append(
            _evaluation_metric(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                role=role,
                rows=rows,
                ic_newey_west_lag=newey_west_lag,
            )
        )
        if role == "test":
            backtest = _portfolio_backtest(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                rows=rows,
                transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                newey_west_lag=newey_west_lag,
                signal_direction=signal_directions[(model_id, split_id, target_name)],
                target_aware_policy=target_aware_portfolio_policy,
            )
            if backtest is not None:
                backtests.append(backtest)
            portfolio_result = _portfolio_time_series(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                rows=rows,
                price_panel=price_panel,
                portfolio_return_type=portfolio_return_type,
                transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                signal_direction=signal_directions[(model_id, split_id, target_name)],
                target_aware_policy=target_aware_portfolio_policy,
            )
            portfolio_weights.extend(portfolio_result[0])
            portfolio_returns.extend(portfolio_result[1])
            portfolio_metrics.extend(portfolio_result[2])
            monthly_result = build_monthly_portfolio_artifacts(
                run_id=run_id,
                rows=rows,
                price_panel=price_panel,
                portfolio_return_type=portfolio_return_type,
                transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                signal_direction=signal_directions[(model_id, split_id, target_name)],
                target_aware_policy=target_aware_portfolio_policy,
            )
            factor_panel.extend(monthly_result.factor_panel)
            monthly_portfolio_weights.extend(monthly_result.portfolio_weights)
            monthly_portfolio_returns.extend(monthly_result.portfolio_returns)
            monthly_portfolio_metrics.extend(monthly_result.portfolio_metrics)

    metrics.extend(
        _aggregate_metrics(
            run_id=run_id,
            split_metrics=metrics,
            ic_newey_west_lag=newey_west_lag,
        )
    )
    monthly_portfolio_metrics.extend(
        aggregate_monthly_portfolio_metrics(
            monthly_portfolio_returns,
            run_id=run_id,
        )
    )
    return EvaluationBuildResult(
        metrics=metrics,
        backtests=backtests,
        portfolio_weights=portfolio_weights,
        portfolio_returns=portfolio_returns,
        portfolio_metrics=portfolio_metrics,
        factor_panel=factor_panel,
        monthly_portfolio_weights=monthly_portfolio_weights,
        monthly_portfolio_returns=monthly_portfolio_returns,
        monthly_portfolio_metrics=monthly_portfolio_metrics,
        delisting_application_report=_delisting_application_report(
            labels=labels,
            portfolio_returns=portfolio_returns + monthly_portfolio_returns,
        ),
    )


def _group_scored_predictions(
    rows: list[ScoredPrediction],
) -> dict[tuple[str, str, str, str], list[ScoredPrediction]]:
    grouped: dict[tuple[str, str, str, str], list[ScoredPrediction]] = defaultdict(list)
    for row in rows:
        role = row.prediction.role or "test"
        grouped[
            (
                row.prediction.model_id,
                row.prediction.split_id,
                row.prediction.target_name,
                role,
            )
        ].append(row)
    return grouped


def _resolved_signal_directions(
    grouped: dict[tuple[str, str, str, str], list[ScoredPrediction]],
    requested_direction: PortfolioSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
) -> dict[tuple[str, str, str], ResolvedSignalDirection]:
    keys = {
        (model_id, split_id, target_name)
        for model_id, split_id, target_name, _ in grouped
    }
    target_aware = {
        key: "long_low_score"
        for key in keys
        if _is_volatility_target(key[2])
        and target_aware_policy in {"long_low_vol", "risk_scaled"}
    }
    if requested_direction != "validation_selected":
        return {
            key: target_aware.get(key, requested_direction)
            for key in keys
        }

    resolved: dict[tuple[str, str, str], ResolvedSignalDirection] = {}
    for model_id, split_id, target_name in keys:
        validation_rows = grouped.get((model_id, split_id, target_name, "validation"), [])
        key = (model_id, split_id, target_name)
        resolved[key] = target_aware.get(
            key,
            _direction_from_validation_rows(validation_rows),
        )
    return resolved


def _direction_from_validation_rows(
    rows: list[ScoredPrediction],
) -> ResolvedSignalDirection:
    low_rows, high_rows = _tie_aware_extreme_rows(rows)
    if not low_rows or not high_rows:
        return "long_high_score"
    high_minus_low = float(
        np.mean([row.label.target_value for row in high_rows])
        - np.mean([row.label.target_value for row in low_rows])
    )
    return "long_high_score" if high_minus_low >= 0.0 else "long_low_score"


def _is_volatility_target(target_name: str) -> bool:
    return "volatility" in target_name.lower() or target_name.lower().startswith(
        "realized_vol"
    )


def _tie_aware_extreme_rows(
    rows: list[ScoredPrediction],
) -> tuple[list[ScoredPrediction], list[ScoredPrediction]]:
    scores = np.array([row.prediction.factor_score for row in rows], dtype=float)
    low_indices, high_indices = tie_aware_extreme_indices(scores)
    return (
        [rows[int(index)] for index in low_indices],
        [rows[int(index)] for index in high_indices],
    )


def _evaluation_metric(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    role: str,
    rows: list[ScoredPrediction],
    ic_newey_west_lag: int,
) -> EvaluationMetricRecord:
    y_true = np.array([row.label.target_value for row in rows], dtype=float)
    y_pred = np.array([row.prediction.prediction_value for row in rows], dtype=float)
    errors = y_pred - y_true
    rmse = float(np.sqrt(np.mean(errors**2))) if len(rows) else 0.0
    mae = float(np.mean(np.abs(errors))) if len(rows) else 0.0
    r_squared = _r_squared(y_true, y_pred)
    directional_accuracy = _directional_accuracy(y_true, y_pred)
    pearson = pearson_ic(y_true, y_pred)
    rank = rank_ic(y_true, y_pred)
    pearson_series, rank_series, ic_grouping = _ic_diagnostic_series(
        rows,
        pooled_pearson=pearson,
        pooled_rank=rank,
    )
    return EvaluationMetricRecord(
        evaluation_version=BACKTEST_VERSION,
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        role=role,
        observation_count=len(rows),
        rmse=rmse,
        mae=mae,
        r_squared=r_squared,
        directional_accuracy=directional_accuracy,
        pearson_ic=pearson,
        rank_ic=rank,
        aggregation_method="pooled_window_metrics_with_date_ic_diagnostics",
        split_count=1,
        ic_grouping=ic_grouping,
        ic_observation_count=max(len(pearson_series), len(rank_series)),
        pearson_ic_t_stat=_mean_t_stat(pearson_series),
        rank_ic_t_stat=_mean_t_stat(rank_series),
        pearson_ic_newey_west_t_stat=newey_west_t_stat(
            pearson_series,
            ic_newey_west_lag,
        ),
        rank_ic_newey_west_t_stat=newey_west_t_stat(rank_series, ic_newey_west_lag),
        created_at_utc=datetime.now(UTC),
    )


def _aggregate_metrics(
    *,
    run_id: str,
    split_metrics: list[EvaluationMetricRecord],
    ic_newey_west_lag: int,
) -> list[EvaluationMetricRecord]:
    grouped: dict[tuple[str, str, str], list[EvaluationMetricRecord]] = defaultdict(list)
    for metric in split_metrics:
        if metric.split_id == "ALL_SPLITS":
            continue
        grouped[
            (
                _aggregate_model_id(metric.model_id, metric.target_name),
                metric.target_name,
                metric.role,
            )
        ].append(metric)
    return [
        _aggregate_metric_from_split_metrics(
            run_id=run_id,
            model_id=model_id,
            split_id="ALL_SPLITS",
            target_name=target_name,
            role=role,
            rows=rows,
            ic_newey_west_lag=ic_newey_west_lag,
        )
        for (model_id, target_name, role), rows in sorted(grouped.items())
    ]


def _aggregate_metric_from_split_metrics(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    role: str,
    rows: list[EvaluationMetricRecord],
    ic_newey_west_lag: int,
) -> EvaluationMetricRecord:
    total_observations = sum(record.observation_count for record in rows)
    weights = np.array([record.observation_count for record in rows], dtype=float)
    if weights.sum() == 0:
        weights = np.ones(len(rows), dtype=float)
    rmse = float(
        sqrt(
            float(
                np.average(
                    [record.rmse**2 for record in rows],
                    weights=weights,
                )
            )
        )
    )
    pearson_values = np.array([record.pearson_ic for record in rows], dtype=float)
    rank_values = np.array([record.rank_ic for record in rows], dtype=float)
    return EvaluationMetricRecord(
        evaluation_version=BACKTEST_VERSION,
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        role=role,
        observation_count=total_observations,
        rmse=rmse,
        mae=float(np.average([record.mae for record in rows], weights=weights)),
        r_squared=float(np.average([record.r_squared for record in rows], weights=weights)),
        directional_accuracy=float(
            np.average([record.directional_accuracy for record in rows], weights=weights)
        ),
        pearson_ic=float(np.mean(pearson_values)) if len(pearson_values) else 0.0,
        rank_ic=float(np.mean(rank_values)) if len(rank_values) else 0.0,
        aggregation_method="split_mean_ic_weighted_error_metrics",
        split_count=len(rows),
        ic_grouping="split",
        ic_observation_count=len(rows),
        pearson_ic_t_stat=_mean_t_stat(pearson_values),
        rank_ic_t_stat=_mean_t_stat(rank_values),
        pearson_ic_newey_west_t_stat=newey_west_t_stat(
            pearson_values,
            ic_newey_west_lag,
        ),
        rank_ic_newey_west_t_stat=newey_west_t_stat(rank_values, ic_newey_west_lag),
        created_at_utc=datetime.now(UTC),
    )


def _aggregate_model_id(model_id: str, target_name: str) -> str:
    parts = model_id.split("::")
    if len(parts) >= 2 and parts[1] == target_name:
        return f"{parts[0]}::{target_name}::ALL_SPLITS"
    if len(parts) >= 1:
        return f"{parts[0]}::{target_name}::ALL_SPLITS"
    return f"{model_id}::{target_name}::ALL_SPLITS"


def _delisting_application_report(
    *,
    labels: list[LabelRecord],
    portfolio_returns: list[PortfolioReturnRecord],
) -> dict[str, int | float | str]:
    labels_with_delisting = sum(label.delisting_return_applied for label in labels)
    labels_missing_delisting_return = sum(
        label.return_quality_flag == "missing_delisting_return" for label in labels
    )
    positions_affected = sum(
        record.positions_affected_by_delisting for record in portfolio_returns
    )
    delisting_returns_applied = sum(
        record.delisting_returns_applied for record in portfolio_returns
    )
    missing_delisting_returns = sum(
        record.missing_delisting_returns for record in portfolio_returns
    ) + labels_missing_delisting_return
    status = (
        "fail"
        if missing_delisting_returns
        else "pass"
        if labels_with_delisting or delisting_returns_applied
        else "not_applicable"
    )
    return {
        "report_version": "delisting-application-report-v0",
        "status": status,
        "labels_total": len(labels),
        "labels_with_delisting_return_applied": labels_with_delisting,
        "labels_missing_delisting_return": labels_missing_delisting_return,
        "portfolio_return_rows": len(portfolio_returns),
        "positions_affected_by_delisting": positions_affected,
        "delisting_returns_applied": delisting_returns_applied,
        "missing_delisting_returns": missing_delisting_returns,
    }


def _ic_diagnostic_series(
    rows: list[ScoredPrediction],
    *,
    pooled_pearson: float,
    pooled_rank: float,
    min_cross_section: int = 2,
) -> tuple[np.ndarray, np.ndarray, str]:
    rows_by_date: dict[date, list[ScoredPrediction]] = defaultdict(list)
    for row in rows:
        rows_by_date[row.prediction.event_date].append(row)
    pearson_values: list[float] = []
    rank_values: list[float] = []
    for event_date in sorted(rows_by_date):
        date_rows = rows_by_date[event_date]
        if len(date_rows) < min_cross_section:
            continue
        y_true = np.array([row.label.target_value for row in date_rows], dtype=float)
        y_pred = np.array([row.prediction.prediction_value for row in date_rows], dtype=float)
        pearson_values.append(pearson_ic(y_true, y_pred))
        rank_values.append(rank_ic(y_true, y_pred))
    if pearson_values or rank_values:
        return np.array(pearson_values), np.array(rank_values), "event_date_cross_section"
    return np.array([pooled_pearson]), np.array([pooled_rank]), "pooled_fallback"


def _r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2:
        return 0.0
    total_sum_squares = float(np.sum((y_true - y_true.mean()) ** 2))
    if total_sum_squares == 0.0:
        return 0.0
    residual_sum_squares = float(np.sum((y_true - y_pred) ** 2))
    return 1.0 - residual_sum_squares / total_sum_squares


def _directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(np.sign(y_true) == np.sign(y_pred)))


def _mean_t_stat(values: np.ndarray | list[float]) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return 0.0
    standard_error = float(np.std(values, ddof=1) / sqrt(len(values)))
    if standard_error == 0.0:
        return 0.0
    return float(values.mean() / standard_error)


def pearson_ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0
    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        return 0.0
    return float(np.corrcoef(y_true, y_pred)[0, 1])


def _portfolio_backtest(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rows: list[ScoredPrediction],
    transaction_cost_bps_one_way: float,
    newey_west_lag: int,
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
) -> PortfolioBacktestRecord | None:
    short_rows, long_rows = _tie_aware_extreme_rows(rows)
    if not short_rows or not long_rows:
        return None
    if signal_direction == "long_low_score":
        long_rows, short_rows = short_rows, long_rows
    long_return = float(np.mean([row.label.target_value for row in long_rows]))
    short_return = float(np.mean([row.label.target_value for row in short_rows]))
    gross_return = long_return - short_return
    turnover = 2.0
    cost = turnover * transaction_cost_bps_one_way / 10_000.0
    net_return = gross_return - cost
    event_returns = np.array(
        [row.label.target_value for row in long_rows]
        + [-row.label.target_value for row in short_rows],
        dtype=float,
    )
    event_std = float(np.std(event_returns, ddof=1)) if len(event_returns) > 1 else 0.0
    sharpe_ratio = float(event_returns.mean() / event_std * sqrt(252)) if event_std else 0.0
    return PortfolioBacktestRecord(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        role="test",
        portfolio_method="top_bottom_quintile_min_one",
        weighting="equal_weight",
        signal_direction=signal_direction,
        target_aware_policy=target_aware_policy,
        rebalance_frequency="event_based",
        long_count=len(long_rows),
        short_count=len(short_rows),
        gross_long_short_return=gross_return,
        turnover=turnover,
        transaction_cost_bps_one_way=transaction_cost_bps_one_way,
        net_long_short_return=net_return,
        sharpe_ratio=sharpe_ratio,
        newey_west_lag=newey_west_lag,
        newey_west_t_stat=newey_west_t_stat(event_returns, newey_west_lag),
        created_at_utc=datetime.now(UTC),
    )


def _portfolio_time_series(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rows: list[ScoredPrediction],
    price_panel: PricePanel | None,
    portfolio_return_type: ReturnType,
    transaction_cost_bps_one_way: float,
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
) -> tuple[list[PortfolioWeightRecord], list[PortfolioReturnRecord], list[PortfolioMetricRecord]]:
    if len(rows) < 2:
        return [], [], []

    all_weights: list[PortfolioWeightRecord] = []
    all_returns: list[PortfolioReturnRecord] = []
    metric_rows: list[PortfolioMetricRecord] = []
    for variant in _available_portfolio_variants(
        rows,
        signal_direction,
        target_aware_policy,
    ):
        weights, returns, metric = _portfolio_time_series_for_variant(
            run_id=run_id,
            model_id=model_id,
            split_id=split_id,
            target_name=target_name,
            rows=rows,
            price_panel=price_panel,
            portfolio_return_type=portfolio_return_type,
            transaction_cost_bps_one_way=transaction_cost_bps_one_way,
            variant=variant,
        )
        all_weights.extend(weights)
        all_returns.extend(returns)
        if metric is not None:
            metric_rows.append(metric)
    return all_weights, all_returns, metric_rows


def _available_portfolio_variants(
    rows: list[ScoredPrediction],
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
) -> list[PortfolioVariant]:
    variants = [
        PortfolioVariant(
            "equal_weight",
            "equal_weight",
            False,
            signal_direction,
            target_aware_policy,
        )
    ]
    if all(row.prediction.market_cap is not None for row in rows):
        variants.append(
            PortfolioVariant(
                "value_weight",
                "value_weight",
                False,
                signal_direction,
                target_aware_policy,
            )
        )
    if all(row.prediction.sector for row in rows):
        variants.append(
            PortfolioVariant(
                "sector_neutral_equal_weight",
                "equal_weight",
                True,
                signal_direction,
                target_aware_policy,
            )
        )
    if all(row.prediction.sector and row.prediction.market_cap is not None for row in rows):
        variants.append(
            PortfolioVariant(
                "sector_neutral_value_weight",
                "value_weight",
                True,
                signal_direction,
                target_aware_policy,
            )
        )
    return variants


def _portfolio_time_series_for_variant(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rows: list[ScoredPrediction],
    price_panel: PricePanel | None,
    portfolio_return_type: ReturnType,
    transaction_cost_bps_one_way: float,
    variant: PortfolioVariant,
) -> tuple[list[PortfolioWeightRecord], list[PortfolioReturnRecord], PortfolioMetricRecord | None]:
    rows_by_rebalance: dict[date, list[ScoredPrediction]] = defaultdict(list)
    for row in rows:
        rows_by_rebalance[row.prediction.event_date].append(row)

    weights: list[PortfolioWeightRecord] = []
    returns: list[PortfolioReturnRecord] = []
    previous_weights: dict[str, float] = {}
    now = datetime.now(UTC)

    for rebalance_date, rebalance_rows in sorted(rows_by_rebalance.items()):
        selected = _portfolio_weights_for_rebalance(
            rows=rebalance_rows,
            previous_weights=previous_weights,
            run_id=run_id,
            model_id=model_id,
            split_id=split_id,
            target_name=target_name,
            variant=variant,
            created_at_utc=now,
        )
        if not selected:
            continue
        current_weights = {record.ticker: record.normalized_weight for record in selected}
        all_tickers = set(previous_weights) | set(current_weights)
        turnover = 0.5 * sum(
            abs(current_weights.get(ticker, 0.0) - previous_weights.get(ticker, 0.0))
            for ticker in all_tickers
        )
        weights.extend(
            record.model_copy(
                update={
                    "previous_weight": previous_weights.get(record.ticker, 0.0),
                    "trade_weight": (
                        record.normalized_weight - previous_weights.get(record.ticker, 0.0)
                    ),
                }
            )
            for record in selected
        )
        if price_panel is None:
            returns.append(
                _portfolio_return_for_rebalance(
                    run_id=run_id,
                    model_id=model_id,
                    split_id=split_id,
                    target_name=target_name,
                    rebalance_date=rebalance_date,
                    rows=rebalance_rows,
                    weights=current_weights,
                    variant=variant,
                    turnover=turnover,
                    transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                    created_at_utc=now,
                )
            )
        else:
            returns.extend(
                _daily_portfolio_returns_for_rebalance(
                    run_id=run_id,
                    model_id=model_id,
                    split_id=split_id,
                    target_name=target_name,
                    rebalance_date=rebalance_date,
                    rows=rebalance_rows,
                    weights=current_weights,
                    variant=variant,
                    turnover=turnover,
                    transaction_cost_bps_one_way=transaction_cost_bps_one_way,
                    price_panel=price_panel,
                    portfolio_return_type=portfolio_return_type,
                    created_at_utc=now,
                )
            )
        previous_weights = current_weights

    if not returns:
        return weights, returns, None
    return weights, returns, _portfolio_metric(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        returns=returns,
        variant=variant,
        created_at_utc=now,
    )


def _portfolio_weights_for_rebalance(
    *,
    rows: list[ScoredPrediction],
    previous_weights: dict[str, float],
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    variant: PortfolioVariant,
    created_at_utc: datetime,
) -> list[PortfolioWeightRecord]:
    del previous_weights
    if variant.sector_neutral:
        return _sector_neutral_weights_for_rebalance(
            rows=rows,
            run_id=run_id,
            model_id=model_id,
            split_id=split_id,
            target_name=target_name,
            variant=variant,
            created_at_utc=created_at_utc,
        )
    short_rows, long_rows = _tie_aware_extreme_rows(rows)
    if not short_rows or not long_rows:
        return []
    selected_weights = _leg_weights(
        long_rows=long_rows,
        short_rows=short_rows,
        weighting=variant.weighting,
        gross_allocation=2.0,
        signal_direction=variant.signal_direction,
        target_aware_policy=variant.target_aware_policy,
        target_name=target_name,
    )
    rank_values = average_ranks(
        np.array([row.prediction.factor_score for row in rows], dtype=float),
        one_based=True,
    )
    ranks_by_id = {
        id(row): float(rank_value)
        for row, rank_value in zip(rows, rank_values, strict=True)
    }
    records: list[PortfolioWeightRecord] = []
    for row in rows:
        if id(row) not in selected_weights:
            continue
        raw_weight = selected_weights[id(row)]
        side = "long" if raw_weight > 0 else "short"
        quantile = 5 if side == "long" else 1
        records.append(
            PortfolioWeightRecord(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                portfolio_variant=variant.name,
                weighting=variant.weighting,
                signal_direction=variant.signal_direction,
                target_aware_policy=variant.target_aware_policy,
                sector_neutral=variant.sector_neutral,
                rebalance_date=row.prediction.event_date,
                holding_start_date=row.label.label_start_date,
                holding_end_date=row.label.label_end_date,
                ticker=row.prediction.ticker,
                entity_id=row.label.entity_id,
                sector=row.prediction.sector,
                industry=row.prediction.industry,
                market_cap=row.prediction.market_cap,
                factor_score=row.prediction.factor_score,
                rank=ranks_by_id[id(row)],
                quantile=quantile,
                side=side,
                raw_weight=raw_weight,
                normalized_weight=raw_weight,
                previous_weight=0.0,
                trade_weight=raw_weight,
                created_at_utc=created_at_utc,
            )
        )
    return records


def _sector_neutral_weights_for_rebalance(
    *,
    rows: list[ScoredPrediction],
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    variant: PortfolioVariant,
    created_at_utc: datetime,
) -> list[PortfolioWeightRecord]:
    rows_by_sector: dict[str, list[ScoredPrediction]] = defaultdict(list)
    for row in rows:
        if row.prediction.sector:
            rows_by_sector[row.prediction.sector].append(row)
    eligible_sectors = {
        sector: sector_rows
        for sector, sector_rows in rows_by_sector.items()
        if len(sector_rows) >= 2
    }
    sector_extremes = {
        sector: _tie_aware_extreme_rows(sector_rows)
        for sector, sector_rows in eligible_sectors.items()
    }
    sector_extremes = {
        sector: extremes
        for sector, extremes in sector_extremes.items()
        if extremes[0] and extremes[1]
    }
    if not sector_extremes:
        return []
    gross_allocation = 2.0 / len(sector_extremes)
    selected_weights: dict[int, float] = {}
    rank_values = average_ranks(
        np.array([row.prediction.factor_score for row in rows], dtype=float),
        one_based=True,
    )
    ranks_by_id = {
        id(row): float(rank_value)
        for row, rank_value in zip(rows, rank_values, strict=True)
    }
    for short_rows, long_rows in sector_extremes.values():
        sector_weights = _leg_weights(
            long_rows=long_rows,
            short_rows=short_rows,
            weighting=variant.weighting,
            gross_allocation=gross_allocation,
            signal_direction=variant.signal_direction,
            target_aware_policy=variant.target_aware_policy,
            target_name=target_name,
        )
        selected_weights.update(sector_weights)

    records: list[PortfolioWeightRecord] = []
    for row in rows:
        weight = selected_weights.get(id(row))
        if weight is None:
            continue
        side = "long" if weight > 0 else "short"
        records.append(
            PortfolioWeightRecord(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                portfolio_variant=variant.name,
                weighting=variant.weighting,
                signal_direction=variant.signal_direction,
                target_aware_policy=variant.target_aware_policy,
                sector_neutral=variant.sector_neutral,
                rebalance_date=row.prediction.event_date,
                holding_start_date=row.label.label_start_date,
                holding_end_date=row.label.label_end_date,
                ticker=row.prediction.ticker,
                entity_id=row.label.entity_id,
                sector=row.prediction.sector,
                industry=row.prediction.industry,
                market_cap=row.prediction.market_cap,
                factor_score=row.prediction.factor_score,
                rank=ranks_by_id[id(row)],
                quantile=5 if side == "long" else 1,
                side=side,
                raw_weight=weight,
                normalized_weight=weight,
                previous_weight=0.0,
                trade_weight=weight,
                created_at_utc=created_at_utc,
            )
        )
    return records


def _leg_weights(
    *,
    long_rows: list[ScoredPrediction],
    short_rows: list[ScoredPrediction],
    weighting: str,
    gross_allocation: float,
    signal_direction: ResolvedSignalDirection,
    target_aware_policy: TargetAwarePortfolioPolicy,
    target_name: str,
) -> dict[int, float]:
    if signal_direction == "long_low_score":
        long_rows, short_rows = short_rows, long_rows
    long_allocation = gross_allocation / 2.0
    short_allocation = gross_allocation / 2.0
    weights: dict[int, float] = {}
    use_risk_scaled = (
        target_aware_policy == "risk_scaled" and _is_volatility_target(target_name)
    )
    for row, weight in _side_weights(
        long_rows,
        weighting=weighting,
        allocation=long_allocation,
        risk_scaled=use_risk_scaled,
    ):
        weights[id(row)] = weight
    for row, weight in _side_weights(
        short_rows,
        weighting=weighting,
        allocation=short_allocation,
        risk_scaled=use_risk_scaled,
    ):
        weights[id(row)] = -weight
    return weights


def _side_weights(
    rows: list[ScoredPrediction],
    *,
    weighting: str,
    allocation: float,
    risk_scaled: bool = False,
) -> list[tuple[ScoredPrediction, float]]:
    if not rows:
        return []
    if risk_scaled:
        inverse_vol_weights = [
            1.0 / max(abs(float(row.prediction.factor_score)), 1e-6)
            for row in rows
        ]
        denominator = sum(inverse_vol_weights)
        if denominator > 0:
            return [
                (row, allocation * inverse_vol_weight / denominator)
                for row, inverse_vol_weight in zip(rows, inverse_vol_weights, strict=True)
            ]
    if weighting == "value_weight" and all(row.prediction.market_cap for row in rows):
        denominator = sum(float(row.prediction.market_cap or 0.0) for row in rows)
        if denominator > 0:
            return [
                (row, allocation * float(row.prediction.market_cap or 0.0) / denominator)
                for row in rows
            ]
    return [(row, allocation / len(rows)) for row in rows]


def _portfolio_return_for_rebalance(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rebalance_date,
    rows: list[ScoredPrediction],
    weights: dict[str, float],
    variant: PortfolioVariant,
    turnover: float,
    transaction_cost_bps_one_way: float,
    created_at_utc: datetime,
) -> PortfolioReturnRecord:
    label_by_ticker = {row.prediction.ticker: row.label for row in rows}
    long_return = sum(
        weight * label_by_ticker[ticker].target_value
        for ticker, weight in weights.items()
        if weight > 0
    )
    short_return = sum(
        weight * label_by_ticker[ticker].target_value
        for ticker, weight in weights.items()
        if weight < 0
    )
    gross_return = long_return + short_return
    transaction_cost = turnover * transaction_cost_bps_one_way / 10_000.0
    long_exposure, short_exposure, gross_exposure, net_exposure = _weight_exposures(weights)
    affected_by_delisting = sum(
        1 for ticker in weights if label_by_ticker[ticker].delisting_return_applied
    )
    return PortfolioReturnRecord(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        portfolio_variant=variant.name,
        weighting=variant.weighting,
        signal_direction=variant.signal_direction,
        target_aware_policy=variant.target_aware_policy,
        sector_neutral=variant.sector_neutral,
        return_source="label_window",
        position_accounting="label_window",
        date=max(label.label_end_date for label in label_by_ticker.values()),
        rebalance_date=rebalance_date,
        gross_long_return=float(long_return),
        gross_short_return=float(short_return),
        gross_long_short_return=float(gross_return),
        transaction_cost=float(transaction_cost),
        net_long_short_return=float(gross_return - transaction_cost),
        long_exposure=long_exposure,
        short_exposure=short_exposure,
        gross_exposure=gross_exposure,
        net_exposure=net_exposure,
        ending_long_exposure=long_exposure,
        ending_short_exposure=short_exposure,
        ending_gross_exposure=gross_exposure,
        ending_net_exposure=net_exposure,
        turnover=float(turnover),
        active_position_count=len(weights),
        positions_affected_by_delisting=affected_by_delisting,
        delisting_returns_applied=affected_by_delisting,
        created_at_utc=created_at_utc,
    )


def _daily_portfolio_returns_for_rebalance(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rebalance_date,
    rows: list[ScoredPrediction],
    weights: dict[str, float],
    variant: PortfolioVariant,
    turnover: float,
    transaction_cost_bps_one_way: float,
    price_panel: PricePanel,
    portfolio_return_type: ReturnType,
    created_at_utc: datetime,
) -> list[PortfolioReturnRecord]:
    label_by_ticker = {row.prediction.ticker: row.label for row in rows}
    if not weights:
        return []
    start_date = min(label_by_ticker[ticker].label_start_date for ticker in weights)
    end_date = max(label_by_ticker[ticker].label_end_date for ticker in weights)
    return_column = f"{portfolio_return_type}_return"
    frame = price_panel.frame
    subset = frame[
        frame["ticker"].isin(weights)
        & (frame["date"] >= start_date)
        & (frame["date"] <= end_date)
    ]
    if subset.empty:
        return []
    returns: list[PortfolioReturnRecord] = []
    first_return = True
    current_weights = dict(weights)
    for holding_date, day_rows in subset.groupby("date", sort=True):
        ticker_returns = {
            str(row.ticker): float(getattr(row, return_column))
            for row in day_rows.itertuples(index=False)
            if not np.isnan(float(getattr(row, return_column)))
        }
        delisted_tickers = {
            str(row.ticker)
            for row in day_rows.itertuples(index=False)
            if bool(getattr(row, "delisting_return_applied", False))
        }
        missing_delisting_tickers = {
            str(row.ticker)
            for row in day_rows.itertuples(index=False)
            if bool(getattr(row, "missing_delisting_return", False))
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
        gross_return = long_return + short_return
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
        next_weights = {
            ticker: weight
            for ticker, weight in next_weights.items()
            if ticker not in delisted_tickers
        }
        (
            ending_long_exposure,
            ending_short_exposure,
            ending_gross_exposure,
            ending_net_exposure,
        ) = _weight_exposures(next_weights)
        returns.append(
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
                return_source="daily_price_panel",
                position_accounting="drifted_daily_positions",
                date=holding_date,
                rebalance_date=rebalance_date,
                gross_long_return=float(long_return),
                gross_short_return=float(short_return),
                gross_long_short_return=float(gross_return),
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
                positions_affected_by_delisting=len(delisted_tickers & set(usable_weights)),
                delisting_returns_applied=len(delisted_tickers & set(usable_weights)),
                missing_delisting_returns=len(missing_delisting_tickers & set(usable_weights)),
                created_at_utc=created_at_utc,
            )
        )
        current_weights = next_weights
        first_return = False
    return returns


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
    variant: PortfolioVariant,
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
        portfolio_method="top_bottom_quintile_min_one_time_series",
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
        newey_west_t_stat=newey_west_t_stat(values, newey_west_lag),
        max_drawdown=float(np.min(drawdowns)),
        hit_rate=float(np.mean(values > 0)),
        average_turnover=float(np.mean([record.turnover for record in returns])),
        average_gross_exposure=float(np.mean([record.gross_exposure for record in returns])),
        average_net_exposure=float(np.mean([record.net_exposure for record in returns])),
        created_at_utc=created_at_utc,
    )


def newey_west_t_stat(values: np.ndarray, lag: int) -> float:
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


def write_evaluation_metrics_json(
    records: list[EvaluationMetricRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([record.model_dump(mode="json") for record in records], file, indent=2)
        file.write("\n")


def write_backtest_results_json(
    records: list[PortfolioBacktestRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([record.model_dump(mode="json") for record in records], file, indent=2)
        file.write("\n")


def write_portfolio_weights_jsonl(
    records: list[PortfolioWeightRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def write_portfolio_returns_jsonl(
    records: list[PortfolioReturnRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def write_portfolio_metrics_json(
    records: list[PortfolioMetricRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([record.model_dump(mode="json") for record in records], file, indent=2)
        file.write("\n")


def write_factor_panel_jsonl(records: list[FactorPanelRecord], path: str | Path) -> None:
    from text_factor_lab.backtest.monthly import write_factor_panel_jsonl as _write

    _write(records, path)


def write_delisting_application_report_json(
    report: dict[str, int | float | str],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
