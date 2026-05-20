from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from math import sqrt
from pathlib import Path

import numpy as np

from text_factor_lab.models import rank_ic
from text_factor_lab.schemas import (
    EvaluationMetricRecord,
    LabelRecord,
    PortfolioBacktestRecord,
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

    return EvaluationBuildResult(metrics=metrics, backtests=backtests)


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
        pearson_ic=pearson,
        rank_ic=rank,
        created_at_utc=datetime.now(UTC),
    )


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
        newey_west_lag=newey_west_lag,
        newey_west_t_stat=newey_west_t_stat(event_returns, newey_west_lag),
        created_at_utc=datetime.now(UTC),
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
