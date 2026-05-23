from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from math import atanh, erfc, sqrt
from pathlib import Path

from text_factor_lab.schemas import (
    EvaluationMetricRecord,
    MultipleTestingFamilyRecord,
    MultipleTestingReportRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    TestedSpecificationRecord,
)

INFERENCE_VERSION = "multiple-testing-v0"
ADJUSTMENT_METHODS = ["bonferroni", "holm", "benjamini_hochberg_fdr"]


@dataclass(frozen=True)
class InferenceBuildResult:
    tested_specifications: list[TestedSpecificationRecord]
    multiple_testing_report: MultipleTestingReportRecord


def build_inference_artifacts(
    *,
    run_id: str,
    metrics: list[EvaluationMetricRecord],
    backtests: list[PortfolioBacktestRecord],
    portfolio_metrics: list[PortfolioMetricRecord],
) -> InferenceBuildResult:
    now = datetime.now(UTC)
    specifications: list[TestedSpecificationRecord] = []
    specifications.extend(_specifications_from_metrics(run_id, metrics, now))
    specifications.extend(_specifications_from_backtests(run_id, backtests, now))
    specifications.extend(_specifications_from_portfolio_metrics(run_id, portfolio_metrics, now))
    report = _multiple_testing_report(run_id, specifications, now)
    return InferenceBuildResult(
        tested_specifications=specifications,
        multiple_testing_report=report,
    )


def _specifications_from_metrics(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
    created_at_utc: datetime,
) -> list[TestedSpecificationRecord]:
    records: list[TestedSpecificationRecord] = []
    for metric in metrics:
        if metric.role != "test":
            continue
        records.append(
            _specification(
                run_id=run_id,
                target_name=metric.target_name,
                split_id=metric.split_id,
                model_id=metric.model_id,
                portfolio_method="prediction_metric",
                weighting="not_applicable",
                sector_neutral=False,
                transaction_cost_bps_one_way=None,
                metric_name="rank_ic",
                raw_metric=metric.rank_ic,
                raw_p_value=_correlation_p_value(metric.rank_ic, metric.observation_count),
                created_at_utc=created_at_utc,
            )
        )
    return records


def _specifications_from_backtests(
    run_id: str,
    backtests: list[PortfolioBacktestRecord],
    created_at_utc: datetime,
) -> list[TestedSpecificationRecord]:
    return [
        _specification(
            run_id=run_id,
            target_name=record.target_name,
            split_id=record.split_id,
            model_id=record.model_id,
            portfolio_method=record.portfolio_method,
            weighting=record.weighting,
            sector_neutral=False,
            transaction_cost_bps_one_way=record.transaction_cost_bps_one_way,
            metric_name="newey_west_t_stat",
            raw_metric=record.newey_west_t_stat,
            raw_p_value=_normal_two_sided_p_value(record.newey_west_t_stat),
            created_at_utc=created_at_utc,
        )
        for record in backtests
    ]


def _specifications_from_portfolio_metrics(
    run_id: str,
    portfolio_metrics: list[PortfolioMetricRecord],
    created_at_utc: datetime,
) -> list[TestedSpecificationRecord]:
    return [
        _specification(
            run_id=run_id,
            target_name=record.target_name,
            split_id=record.split_id,
            model_id=record.model_id,
            portfolio_method=record.portfolio_method,
            weighting=record.weighting,
            sector_neutral=record.sector_neutral,
            transaction_cost_bps_one_way=None,
            metric_name="portfolio_sharpe",
            raw_metric=record.sharpe_ratio,
            raw_p_value=_portfolio_sharpe_p_value(
                record.sharpe_ratio,
                record.observation_count,
            ),
            created_at_utc=created_at_utc,
        )
        for record in portfolio_metrics
    ]


def _specification(
    *,
    run_id: str,
    target_name: str,
    split_id: str,
    model_id: str,
    portfolio_method: str,
    weighting: str,
    sector_neutral: bool,
    transaction_cost_bps_one_way: float | None,
    metric_name: str,
    raw_metric: float,
    raw_p_value: float,
    created_at_utc: datetime,
) -> TestedSpecificationRecord:
    payload = {
        "target_name": target_name,
        "split_id": split_id,
        "model_id": model_id,
        "portfolio_method": portfolio_method,
        "weighting": weighting,
        "sector_neutral": sector_neutral,
        "metric_name": metric_name,
    }
    spec_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return TestedSpecificationRecord(
        run_id=run_id,
        spec_id=spec_id,
        family_id=f"{target_name}::{metric_name}",
        target_name=target_name,
        label_window=_label_window(target_name),
        text_source="10-K",
        section="all_available_sections",
        feature_method="configured_feature_set",
        model_name=_model_name(model_id),
        model_id=model_id,
        hyperparameter_grid_id=f"{_model_name(model_id)}_grid",
        split_id=split_id,
        split_method="rolling_year",
        portfolio_method=portfolio_method,
        weighting=weighting,
        sector_neutral=sector_neutral,
        transaction_cost_bps_one_way=transaction_cost_bps_one_way,
        metric_name=metric_name,
        raw_metric=raw_metric,
        raw_p_value=raw_p_value,
        created_at_utc=created_at_utc,
    )


def _multiple_testing_report(
    run_id: str,
    specifications: list[TestedSpecificationRecord],
    created_at_utc: datetime,
) -> MultipleTestingReportRecord:
    grouped: dict[str, list[TestedSpecificationRecord]] = defaultdict(list)
    for specification in specifications:
        if specification.raw_p_value is not None:
            grouped[specification.family_id].append(specification)
    families = [
        _family_report(run_id, family_id, rows, created_at_utc)
        for family_id, rows in sorted(grouped.items())
    ]
    return MultipleTestingReportRecord(
        run_id=run_id,
        report_version=INFERENCE_VERSION,
        specification_count=len(specifications),
        p_value_count=sum(len(rows) for rows in grouped.values()),
        family_count=len(families),
        methods_applied=ADJUSTMENT_METHODS,
        families=families,
        created_at_utc=created_at_utc,
    )


def _family_report(
    run_id: str,
    family_id: str,
    rows: list[TestedSpecificationRecord],
    created_at_utc: datetime,
) -> MultipleTestingFamilyRecord:
    p_values = [float(row.raw_p_value or 1.0) for row in rows]
    bonferroni = _bonferroni(p_values)
    holm = _holm(p_values)
    bh = _benjamini_hochberg(p_values)
    best_raw_index = min(range(len(p_values)), key=lambda index: p_values[index])
    best_adjusted_index = min(range(len(bh)), key=lambda index: bh[index])
    return MultipleTestingFamilyRecord(
        run_id=run_id,
        family_id=family_id,
        number_of_tests=len(rows),
        methods_applied=ADJUSTMENT_METHODS,
        raw_p_values=p_values,
        bonferroni_adjusted_p_values=bonferroni,
        holm_adjusted_p_values=holm,
        bh_fdr_adjusted_p_values=bh,
        best_raw_spec_id=rows[best_raw_index].spec_id,
        best_raw_p_value=p_values[best_raw_index],
        best_adjusted_spec_id=rows[best_adjusted_index].spec_id,
        best_adjusted_p_value=bh[best_adjusted_index],
        discoveries_at_5pct=sum(value <= 0.05 for value in bh),
        discoveries_at_10pct=sum(value <= 0.10 for value in bh),
        created_at_utc=created_at_utc,
    )


def _bonferroni(p_values: list[float]) -> list[float]:
    count = len(p_values)
    return [min(value * count, 1.0) for value in p_values]


def _holm(p_values: list[float]) -> list[float]:
    count = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * count
    running = 0.0
    for rank, (index, value) in enumerate(indexed):
        corrected = min((count - rank) * value, 1.0)
        running = max(running, corrected)
        adjusted[index] = running
    return adjusted


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    count = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda item: item[1], reverse=True)
    adjusted = [0.0] * count
    running = 1.0
    for reverse_rank, (index, value) in enumerate(indexed, start=1):
        rank = count - reverse_rank + 1
        corrected = min(value * count / rank, 1.0)
        running = min(running, corrected)
        adjusted[index] = running
    return adjusted


def _correlation_p_value(correlation: float, observations: int) -> float:
    if observations < 4 or abs(correlation) >= 1:
        return 1.0 if abs(correlation) < 1 else 0.0
    z_score = atanh(max(min(correlation, 0.999999), -0.999999)) * sqrt(observations - 3)
    return _normal_two_sided_p_value(z_score)


def _portfolio_sharpe_p_value(sharpe_ratio: float, observations: int) -> float:
    if observations < 2:
        return 1.0
    daily_equivalent_z = sharpe_ratio * sqrt(observations / 252.0)
    return _normal_two_sided_p_value(daily_equivalent_z)


def _normal_two_sided_p_value(z_score: float) -> float:
    return max(min(erfc(abs(z_score) / sqrt(2.0)), 1.0), 0.0)


def _label_window(target_name: str) -> str:
    match = re.search(r"_(\d+)_(\d+)$", target_name)
    if not match:
        return "unspecified"
    return f"{match.group(1)}_{match.group(2)}"


def _model_name(model_id: str) -> str:
    return model_id.split("::", 1)[0]


def write_tested_specifications_jsonl(
    records: list[TestedSpecificationRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def write_multiple_testing_report_json(
    record: MultipleTestingReportRecord,
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(record.model_dump(mode="json"), file, indent=2)
        file.write("\n")
