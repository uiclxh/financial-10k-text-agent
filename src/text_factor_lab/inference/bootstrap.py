from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from text_factor_lab.models import rank_ic
from text_factor_lab.schemas import LabelRecord, PredictionRecord

BOOTSTRAP_REPORT_VERSION = "primary-rank-ic-bootstrap-v0"


@dataclass(frozen=True)
class BootstrapRow:
    prediction: PredictionRecord
    label: LabelRecord


def build_primary_rank_ic_bootstrap_report(
    *,
    run_id: str,
    predictions: list[PredictionRecord],
    labels: list[LabelRecord],
    primary_model_name: str = "ridge",
    primary_target_name: str = "realized_volatility_1_20",
    iterations: int = 2000,
    random_seed: int = 42,
) -> dict[str, object]:
    labels_by_id = {label.label_id: label for label in labels}
    rows = [
        BootstrapRow(prediction=prediction, label=labels_by_id[prediction.label_id])
        for prediction in predictions
        if prediction.label_id in labels_by_id
        and prediction.role == "test"
        and prediction.target_name == primary_target_name
        and prediction.model_id.split("::", 1)[0] == primary_model_name
    ]
    if not rows:
        return {
            "report_version": BOOTSTRAP_REPORT_VERSION,
            "run_id": run_id,
            "status": "unavailable",
            "reason": "No OOS rows matched the preregistered primary model and target.",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "rows": [],
        }

    estimands: list[tuple[str, Callable[[list[BootstrapRow]], float]]] = [
        ("all_splits_rank_ic", lambda sample: _all_splits_rank_ic(sample, False)),
        (
            "industry_neutral_all_splits_rank_ic",
            lambda sample: _all_splits_rank_ic(sample, True),
        ),
    ]
    report_rows: list[dict[str, object]] = []
    for estimand_index, (estimand, statistic) in enumerate(estimands):
        point_estimate = statistic(rows)
        methods: list[tuple[str, Callable[[BootstrapRow], str]]] = [
            ("split_bootstrap", lambda row: row.prediction.split_id),
            ("event_date_bootstrap", lambda row: row.prediction.event_date.isoformat()),
            ("ticker_cluster_bootstrap", lambda row: row.prediction.ticker),
        ]
        for method_index, (method, cluster_key) in enumerate(methods):
            rng = np.random.default_rng(
                random_seed + estimand_index * 1009 + method_index * 101
            )
            draws, cluster_count = _cluster_bootstrap(
                rows,
                cluster_key=cluster_key,
                statistic=statistic,
                iterations=iterations,
                rng=rng,
            )
            report_rows.append(
                _bootstrap_summary(
                    estimand=estimand,
                    method=method,
                    point_estimate=point_estimate,
                    draws=draws,
                    cluster_count=cluster_count,
                    iterations=iterations,
                )
            )

    return {
        "report_version": BOOTSTRAP_REPORT_VERSION,
        "run_id": run_id,
        "status": "completed",
        "primary_model_name": primary_model_name,
        "primary_target_name": primary_target_name,
        "aggregation_method": (
            "Mean of split-level tie-aware Rank IC values; bootstrap resampling "
            "preserves each selected cluster as a block."
        ),
        "industry_neutral_method": (
            "Within each sampled OOS split, target and prediction are separately "
            "demeaned by industry before tie-aware Rank IC is computed."
        ),
        "confidence_level": 0.95,
        "iterations": iterations,
        "random_seed": random_seed,
        "oos_observation_count": len(rows),
        "split_count": len({row.prediction.split_id for row in rows}),
        "event_date_count": len({row.prediction.event_date for row in rows}),
        "ticker_count": len({row.prediction.ticker for row in rows}),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "rows": report_rows,
    }


def write_primary_rank_ic_bootstrap_report_json(
    report: dict[str, object],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _all_splits_rank_ic(rows: list[BootstrapRow], industry_neutral: bool) -> float:
    grouped: dict[str, list[BootstrapRow]] = defaultdict(list)
    for row in rows:
        grouped[row.prediction.split_id].append(row)
    split_values = [
        _sample_rank_ic(split_rows, industry_neutral)
        for _, split_rows in sorted(grouped.items())
        if len(split_rows) >= 2
    ]
    return float(np.mean(split_values)) if split_values else 0.0


def _sample_rank_ic(rows: list[BootstrapRow], industry_neutral: bool) -> float:
    y_true = np.asarray([row.label.target_value for row in rows], dtype=float)
    y_pred = np.asarray([row.prediction.prediction_value for row in rows], dtype=float)
    if industry_neutral:
        grouped_indices: dict[str, list[int]] = defaultdict(list)
        for index, row in enumerate(rows):
            industry = (
                row.prediction.industry
                or row.prediction.sector
                or "__MISSING_INDUSTRY__"
            )
            grouped_indices[industry].append(index)
        for indices in grouped_indices.values():
            group_index = np.asarray(indices, dtype=int)
            y_true[group_index] -= float(np.mean(y_true[group_index]))
            y_pred[group_index] -= float(np.mean(y_pred[group_index]))
        y_true = _zero_numerical_residuals(y_true)
        y_pred = _zero_numerical_residuals(y_pred)
    return rank_ic(y_true, y_pred)


def _zero_numerical_residuals(values: np.ndarray) -> np.ndarray:
    scale = max(float(np.max(np.abs(values), initial=0.0)), 1.0)
    tolerance = np.finfo(float).eps * scale * 32.0
    cleaned = values.copy()
    cleaned[np.abs(cleaned) <= tolerance] = 0.0
    return cleaned


def _cluster_bootstrap(
    rows: list[BootstrapRow],
    *,
    cluster_key: Callable[[BootstrapRow], str],
    statistic: Callable[[list[BootstrapRow]], float],
    iterations: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    grouped: dict[str, list[BootstrapRow]] = defaultdict(list)
    for row in rows:
        grouped[str(cluster_key(row))].append(row)
    cluster_names = sorted(grouped)
    draws = np.zeros(iterations, dtype=float)
    for index in range(iterations):
        sampled_names = rng.choice(cluster_names, size=len(cluster_names), replace=True)
        sample = [
            row
            for cluster_name in sampled_names
            for row in grouped[str(cluster_name)]
        ]
        draws[index] = statistic(sample)
    return draws, len(cluster_names)


def _bootstrap_summary(
    *,
    estimand: str,
    method: str,
    point_estimate: float,
    draws: np.ndarray,
    cluster_count: int,
    iterations: int,
) -> dict[str, object]:
    lower, upper = np.quantile(draws, [0.025, 0.975])
    nonpositive_probability = float(np.mean(draws <= 0.0))
    nonnegative_probability = float(np.mean(draws >= 0.0))
    return {
        "estimand": estimand,
        "bootstrap_method": method,
        "point_estimate": point_estimate,
        "ci_lower_95": float(lower),
        "ci_upper_95": float(upper),
        "bootstrap_standard_error": (
            float(np.std(draws, ddof=1)) if len(draws) > 1 else 0.0
        ),
        "two_sided_zero_p_value": min(
            1.0,
            2.0 * min(nonpositive_probability, nonnegative_probability),
        ),
        "cluster_count": cluster_count,
        "iterations": iterations,
    }
