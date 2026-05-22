from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from math import sqrt
from pathlib import Path

import numpy as np

from text_factor_lab.models import rank_ic
from text_factor_lab.schemas import (
    EvaluationMetricRecord,
    LabelRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    PortfolioReturnRecord,
    PortfolioWeightRecord,
    PredictionRecord,
)

BACKTEST_VERSION = "backtest-evaluation-v0"


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
    transaction_cost_bps_one_way: float = 10.0,
    newey_west_lag: int = 19,
) -> EvaluationBuildResult:
    labels_by_id = {label.label_id: label for label in labels}
    scored = [
        ScoredPrediction(prediction=prediction, label=labels_by_id[prediction.label_id])
        for prediction in predictions
        if prediction.label_id is not None and prediction.label_id in labels_by_id
    ]
    grouped = _group_scored_predictions(scored)
    metrics: list[EvaluationMetricRecord] = []
    backtests: list[PortfolioBacktestRecord] = []
    portfolio_weights: list[PortfolioWeightRecord] = []
    portfolio_returns: list[PortfolioReturnRecord] = []
    portfolio_metrics: list[PortfolioMetricRecord] = []

    for (model_id, split_id, target_name, role), rows in sorted(grouped.items()):
        metrics.append(
            _evaluation_metric(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                role=role,
                rows=rows,
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
            )
            if backtest is not None:
                backtests.append(backtest)
            portfolio_result = _portfolio_time_series(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                rows=rows,
                transaction_cost_bps_one_way=transaction_cost_bps_one_way,
            )
            portfolio_weights.extend(portfolio_result[0])
            portfolio_returns.extend(portfolio_result[1])
            if portfolio_result[2] is not None:
                portfolio_metrics.append(portfolio_result[2])

    metrics.extend(_aggregate_metrics(run_id=run_id, scored=scored))
    return EvaluationBuildResult(
        metrics=metrics,
        backtests=backtests,
        portfolio_weights=portfolio_weights,
        portfolio_returns=portfolio_returns,
        portfolio_metrics=portfolio_metrics,
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


def _evaluation_metric(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    role: str,
    rows: list[ScoredPrediction],
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
    return EvaluationMetricRecord(
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
        created_at_utc=datetime.now(UTC),
    )


def _aggregate_metrics(
    *,
    run_id: str,
    scored: list[ScoredPrediction],
) -> list[EvaluationMetricRecord]:
    grouped: dict[tuple[str, str, str], list[ScoredPrediction]] = defaultdict(list)
    for row in scored:
        role = row.prediction.role or "test"
        grouped[(row.prediction.model_id, row.prediction.target_name, role)].append(row)
    return [
        _evaluation_metric(
            run_id=run_id,
            model_id=model_id,
            split_id="ALL_SPLITS",
            target_name=target_name,
            role=role,
            rows=rows,
        )
        for (model_id, target_name, role), rows in sorted(grouped.items())
    ]


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
) -> PortfolioBacktestRecord | None:
    if len(rows) < 2:
        return None
    sorted_rows = sorted(rows, key=lambda row: row.prediction.factor_score)
    leg_size = max(1, int(len(sorted_rows) * 0.2))
    short_rows = sorted_rows[:leg_size]
    long_rows = sorted_rows[-leg_size:]
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
    transaction_cost_bps_one_way: float,
) -> tuple[list[PortfolioWeightRecord], list[PortfolioReturnRecord], PortfolioMetricRecord | None]:
    if len(rows) < 2:
        return [], [], None

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
        returns.append(
            _portfolio_return_for_rebalance(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                rebalance_date=rebalance_date,
                rows=rebalance_rows,
                weights=current_weights,
                turnover=turnover,
                transaction_cost_bps_one_way=transaction_cost_bps_one_way,
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
    created_at_utc: datetime,
) -> list[PortfolioWeightRecord]:
    del previous_weights
    sorted_rows = sorted(rows, key=lambda row: row.prediction.factor_score)
    leg_size = max(1, int(len(sorted_rows) * 0.2))
    short_rows = sorted_rows[:leg_size]
    long_rows = sorted_rows[-leg_size:]
    selected_ids = {id(row): "short" for row in short_rows}
    selected_ids.update({id(row): "long" for row in long_rows})
    records: list[PortfolioWeightRecord] = []
    for rank_index, row in enumerate(sorted_rows, start=1):
        side = selected_ids.get(id(row), "neutral")
        if side == "neutral":
            continue
        raw_weight = (1.0 / leg_size) if side == "long" else (-1.0 / leg_size)
        quantile = 5 if side == "long" else 1
        records.append(
            PortfolioWeightRecord(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                target_name=target_name,
                rebalance_date=row.prediction.event_date,
                holding_start_date=row.label.label_start_date,
                holding_end_date=row.label.label_end_date,
                ticker=row.prediction.ticker,
                entity_id=row.label.entity_id,
                factor_score=row.prediction.factor_score,
                rank=rank_index,
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


def _portfolio_return_for_rebalance(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rebalance_date,
    rows: list[ScoredPrediction],
    weights: dict[str, float],
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
    return PortfolioReturnRecord(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        date=max(label.label_end_date for label in label_by_ticker.values()),
        rebalance_date=rebalance_date,
        gross_long_return=float(long_return),
        gross_short_return=float(short_return),
        gross_long_short_return=float(gross_return),
        transaction_cost=float(transaction_cost),
        net_long_short_return=float(gross_return - transaction_cost),
        long_exposure=float(sum(weight for weight in weights.values() if weight > 0)),
        short_exposure=float(sum(weight for weight in weights.values() if weight < 0)),
        gross_exposure=float(sum(abs(weight) for weight in weights.values())),
        net_exposure=float(sum(weights.values())),
        turnover=float(turnover),
        active_position_count=len(weights),
        created_at_utc=created_at_utc,
    )


def _portfolio_metric(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    returns: list[PortfolioReturnRecord],
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
    equity_curve = np.cumprod(1.0 + values)
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = equity_curve / running_max - 1.0
    return PortfolioMetricRecord(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        portfolio_method="top_bottom_quintile_min_one_time_series",
        weighting="equal_weight_dollar_neutral",
        observation_count=len(returns),
        cumulative_return=cumulative,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=sharpe_ratio,
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
