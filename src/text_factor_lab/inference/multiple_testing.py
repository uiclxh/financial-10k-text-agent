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
PRIMARY_TARGET_PREFERENCE = ["realized_volatility_1_20", "CAR_1_20", "CAR_1_5"]
PRIMARY_MODEL_PREFERENCE = ["ridge", "xgboost"]
SPECIFICATION_REGISTRY_VERSION = "specification-registry-v1"


@dataclass(frozen=True)
class InferenceBuildResult:
    tested_specifications: list[TestedSpecificationRecord]
    multiple_testing_report: MultipleTestingReportRecord
    specification_registry: dict[str, object]


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
        specification_registry=_specification_registry(run_id, specifications, now),
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
                signal_direction="not_applicable",
                target_aware_policy="none",
                sector_neutral=False,
                transaction_cost_bps_one_way=None,
                metric_name="rank_ic",
                raw_metric=metric.rank_ic,
                raw_p_value=_correlation_p_value(metric.rank_ic, metric.observation_count),
                p_value_method="fisher_z_rank_ic",
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
            signal_direction=record.signal_direction,
            target_aware_policy=record.target_aware_policy,
            sector_neutral=False,
            transaction_cost_bps_one_way=record.transaction_cost_bps_one_way,
            metric_name="newey_west_t_stat",
            raw_metric=record.newey_west_t_stat,
            raw_p_value=_normal_two_sided_p_value(record.newey_west_t_stat),
            p_value_method="event_level_newey_west_t_stat",
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
            signal_direction=record.signal_direction,
            target_aware_policy=record.target_aware_policy,
            sector_neutral=record.sector_neutral,
            transaction_cost_bps_one_way=None,
            metric_name="portfolio_sharpe",
            raw_metric=record.sharpe_ratio,
            raw_p_value=_portfolio_metric_p_value(record),
            p_value_method=_portfolio_metric_p_value_method(record),
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
    signal_direction: str,
    target_aware_policy: str,
    sector_neutral: bool,
    transaction_cost_bps_one_way: float | None,
    metric_name: str,
    raw_metric: float,
    raw_p_value: float,
    p_value_method: str,
    created_at_utc: datetime,
) -> TestedSpecificationRecord:
    model_name = _model_name(model_id)
    specification_role, specification_rationale = _specification_role(
        target_name=target_name,
        split_id=split_id,
        model_name=model_name,
        portfolio_method=portfolio_method,
        weighting=weighting,
        signal_direction=signal_direction,
        target_aware_policy=target_aware_policy,
        sector_neutral=sector_neutral,
        metric_name=metric_name,
    )
    payload = {
        "target_name": target_name,
        "split_id": split_id,
        "model_id": model_id,
        "portfolio_method": portfolio_method,
        "weighting": weighting,
        "signal_direction": signal_direction,
        "target_aware_policy": target_aware_policy,
        "sector_neutral": sector_neutral,
        "metric_name": metric_name,
        "p_value_method": p_value_method,
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
        model_name=model_name,
        model_id=model_id,
        hyperparameter_grid_id=f"{model_name}_grid",
        split_id=split_id,
        split_method="rolling_year",
        portfolio_method=portfolio_method,
        weighting=weighting,
        signal_direction=signal_direction,
        target_aware_policy=target_aware_policy,
        sector_neutral=sector_neutral,
        transaction_cost_bps_one_way=transaction_cost_bps_one_way,
        metric_name=metric_name,
        raw_metric=raw_metric,
        raw_p_value=raw_p_value,
        p_value_method=p_value_method,
        specification_role=specification_role,
        preregistered=specification_role == "primary",
        specification_rationale=specification_rationale,
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
            grouped[_role_family_id(specification)].append(specification)
    families = [
        _family_report(run_id, family_id, rows, created_at_utc)
        for family_id, rows in sorted(grouped.items())
    ]
    role_family_counts = {
        role: sum(family.specification_role == role for family in families)
        for role in ("primary", "robustness", "exploratory")
    }
    return MultipleTestingReportRecord(
        run_id=run_id,
        report_version=INFERENCE_VERSION,
        specification_count=len(specifications),
        primary_specification_count=sum(
            row.specification_role == "primary" for row in specifications
        ),
        robustness_specification_count=sum(
            row.specification_role == "robustness" for row in specifications
        ),
        exploratory_specification_count=sum(
            row.specification_role == "exploratory" for row in specifications
        ),
        p_value_count=sum(len(rows) for rows in grouped.values()),
        family_count=len(families),
        role_family_counts=role_family_counts,
        primary_discoveries_at_5pct=sum(
            family.discoveries_at_5pct
            for family in families
            if family.specification_role == "primary"
        ),
        primary_discoveries_at_10pct=sum(
            family.discoveries_at_10pct
            for family in families
            if family.specification_role == "primary"
        ),
        robustness_discoveries_at_10pct=sum(
            family.discoveries_at_10pct
            for family in families
            if family.specification_role == "robustness"
        ),
        exploratory_discoveries_at_10pct=sum(
            family.discoveries_at_10pct
            for family in families
            if family.specification_role == "exploratory"
        ),
        methods_applied=ADJUSTMENT_METHODS,
        families=families,
        created_at_utc=created_at_utc,
    )


def _role_family_id(specification: TestedSpecificationRecord) -> str:
    return f"{specification.specification_role}::{specification.family_id}"


def _family_report(
    run_id: str,
    family_id: str,
    rows: list[TestedSpecificationRecord],
    created_at_utc: datetime,
) -> MultipleTestingFamilyRecord:
    role, base_family_id = _split_role_family_id(family_id)
    p_values = [float(row.raw_p_value or 1.0) for row in rows]
    bonferroni = _bonferroni(p_values)
    holm = _holm(p_values)
    bh = _benjamini_hochberg(p_values)
    best_raw_index = min(range(len(p_values)), key=lambda index: p_values[index])
    best_adjusted_index = min(range(len(bh)), key=lambda index: bh[index])
    return MultipleTestingFamilyRecord(
        run_id=run_id,
        family_id=family_id,
        base_family_id=base_family_id,
        specification_role=role,
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


def _split_role_family_id(family_id: str) -> tuple[str, str]:
    role, separator, base_family_id = family_id.partition("::")
    if separator and role in {"primary", "robustness", "exploratory"}:
        return role, base_family_id
    return "exploratory", family_id


def _specification_registry(
    run_id: str,
    specifications: list[TestedSpecificationRecord],
    created_at_utc: datetime,
) -> dict[str, object]:
    role_counts = {
        role: sum(specification.specification_role == role for specification in specifications)
        for role in ("primary", "robustness", "exploratory")
    }
    primary_specs = [
        _registry_spec_summary(specification)
        for specification in specifications
        if specification.specification_role == "primary"
    ]
    robustness_examples = [
        _registry_spec_summary(specification)
        for specification in specifications
        if specification.specification_role == "robustness"
    ][:20]
    return {
        "run_id": run_id,
        "registry_version": SPECIFICATION_REGISTRY_VERSION,
        "registry_designation": "pre_registered_specification_registry",
        "preregistration": {
            "status": "pre_registered",
            "scope": (
                "Rules marked primary are fixed before interpreting model, "
                "portfolio, and multiple-testing results for this run."
            ),
            "primary_rules_are_preregistered": True,
            "robustness_rules_are_preregistered": False,
            "exploratory_rules_are_preregistered": False,
            "created_at_utc": created_at_utc.isoformat(),
        },
        "policy": {
            "primary_target_preference": PRIMARY_TARGET_PREFERENCE,
            "primary_model_preference": PRIMARY_MODEL_PREFERENCE,
            "primary_prediction_rule": (
                "ALL_SPLITS Rank IC for preferred target/model."
            ),
            "primary_portfolio_rule": (
                "Monthly common rebalance, sector-neutral equal-weight portfolio "
                "Sharpe for preferred target/model at ALL_SPLITS, with p-value "
                "from the ALL_SPLITS OOS return-series Newey-West t-stat."
            ),
            "split_level_rule": "Individual rolling split results are exploratory by default.",
        },
        "preregistered_primary_rules": [
            {
                "rule_id": "primary_prediction_all_splits_rank_ic",
                "metric_name": "rank_ic",
                "target_selection": "first available preferred target",
                "model_selection": "first available preferred model",
                "split_id": "ALL_SPLITS",
                "portfolio_method": "prediction_metric",
                "p_value_method": "fisher_z_rank_ic",
                "preregistered": True,
            },
            {
                "rule_id": "primary_portfolio_all_splits_monthly_nw",
                "metric_name": "portfolio_sharpe",
                "target_selection": "first available preferred target",
                "model_selection": "first available preferred model",
                "split_id": "ALL_SPLITS",
                "portfolio_method": "monthly_common_rebalance_top_bottom_quintile",
                "weighting": "equal_weight",
                "sector_neutral": True,
                "p_value_method": "all_splits_oos_return_series_newey_west_t_stat",
                "preregistered": True,
            },
        ],
        "specification_count": len(specifications),
        "role_counts": role_counts,
        "primary_specifications": primary_specs,
        "robustness_examples": robustness_examples,
        "created_at_utc": created_at_utc.isoformat(),
    }


def _registry_spec_summary(specification: TestedSpecificationRecord) -> dict[str, object]:
    return {
        "spec_id": specification.spec_id,
        "family_id": specification.family_id,
        "target_name": specification.target_name,
        "model_name": specification.model_name,
        "model_id": specification.model_id,
        "split_id": specification.split_id,
        "metric_name": specification.metric_name,
        "portfolio_method": specification.portfolio_method,
        "weighting": specification.weighting,
        "signal_direction": specification.signal_direction,
        "target_aware_policy": specification.target_aware_policy,
        "sector_neutral": specification.sector_neutral,
        "raw_metric": specification.raw_metric,
        "raw_p_value": specification.raw_p_value,
        "p_value_method": specification.p_value_method,
        "preregistered": specification.preregistered,
        "rule_status": (
            "pre_registered_primary"
            if specification.preregistered
            else "not_preregistered"
        ),
        "rationale": specification.specification_rationale,
    }


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


def _portfolio_metric_p_value(record: PortfolioMetricRecord) -> float:
    if _uses_all_splits_oos_return_series_p_value(record):
        return _normal_two_sided_p_value(record.newey_west_t_stat)
    return _portfolio_sharpe_p_value(record.sharpe_ratio, record.observation_count)


def _portfolio_metric_p_value_method(record: PortfolioMetricRecord) -> str:
    if _uses_all_splits_oos_return_series_p_value(record):
        return "all_splits_oos_return_series_newey_west_t_stat"
    return "portfolio_sharpe_normal_approximation"


def _uses_all_splits_oos_return_series_p_value(record: PortfolioMetricRecord) -> bool:
    return (
        record.split_id == "ALL_SPLITS"
        and record.portfolio_method.startswith("monthly_common_rebalance")
    )


def _normal_two_sided_p_value(z_score: float) -> float:
    return max(min(erfc(abs(z_score) / sqrt(2.0)), 1.0), 0.0)


def _label_window(target_name: str) -> str:
    match = re.search(r"_(\d+)_(\d+)$", target_name)
    if not match:
        return "unspecified"
    return f"{match.group(1)}_{match.group(2)}"


def _model_name(model_id: str) -> str:
    return model_id.split("::", 1)[0]


def _primary_target_rank(target_name: str) -> int:
    try:
        return PRIMARY_TARGET_PREFERENCE.index(target_name)
    except ValueError:
        return len(PRIMARY_TARGET_PREFERENCE)


def _primary_model_rank(model_name: str) -> int:
    try:
        return PRIMARY_MODEL_PREFERENCE.index(model_name)
    except ValueError:
        return len(PRIMARY_MODEL_PREFERENCE)


def _specification_role(
    *,
    target_name: str,
    split_id: str,
    model_name: str,
    portfolio_method: str,
    weighting: str,
    signal_direction: str,
    target_aware_policy: str,
    sector_neutral: bool,
    metric_name: str,
) -> tuple[str, str]:
    del target_aware_policy
    preferred_target = _primary_target_rank(target_name) == 0
    preferred_model = _primary_model_rank(model_name) == 0
    allowed_model = _primary_model_rank(model_name) < len(PRIMARY_MODEL_PREFERENCE)

    if metric_name == "rank_ic":
        if split_id == "ALL_SPLITS" and preferred_target and preferred_model:
            return (
                "primary",
                "Primary prediction specification: preferred target, preferred model, "
                "and all-split out-of-sample Rank IC.",
            )
        if split_id == "ALL_SPLITS" and allowed_model:
            return (
                "robustness",
                "Robustness prediction specification: all-split Rank IC for an "
                "allowed target/model variant.",
            )
        return (
            "exploratory",
            "Exploratory prediction specification: split-level or non-primary metric.",
        )

    if metric_name == "portfolio_sharpe":
        monthly_method = portfolio_method.startswith("monthly_common_rebalance")
        if (
            monthly_method
            and split_id == "ALL_SPLITS"
            and preferred_target
            and preferred_model
            and weighting == "equal_weight"
            and sector_neutral
        ):
            return (
                "primary",
                "Primary portfolio specification: monthly common rebalance, "
                "sector-neutral equal-weight construction, preferred target/model.",
            )
        if monthly_method and allowed_model:
            return (
                "robustness",
                "Robustness portfolio specification: monthly common rebalance "
                "variant for an allowed model.",
            )
        return (
            "exploratory",
            "Exploratory portfolio specification: event-level or non-primary variant.",
        )

    if metric_name == "newey_west_t_stat":
        return (
            "robustness" if allowed_model else "exploratory",
            "Event-level Newey-West result retained as a robustness diagnostic, "
            "not the primary portfolio claim.",
        )

    return "exploratory", "Exploratory specification outside the primary registry policy."


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


def write_specification_registry_json(
    registry: dict[str, object],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(registry, file, indent=2, sort_keys=True)
        file.write("\n")
