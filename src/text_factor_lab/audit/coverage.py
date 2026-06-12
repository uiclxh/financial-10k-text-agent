from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from text_factor_lab.schemas import (
    CoverageFailureRecord,
    FeatureRecord,
    LabelRecord,
    ModelManifestRecord,
    PredictionRecord,
    SplitAssignmentRecord,
    TestedSpecificationRecord,
)

BASELINE_MODEL_NAMES = {"historical_mean", "industry_mean"}
OOS_ROLES = {"validation", "test"}
OUTSIDE_CONFIGURED_SPLIT_STAGE = "outside_configured_split_window"
OUTSIDE_CONFIGURED_SPLIT_REASON = (
    "Label event date is outside the configured validation/test split window."
)


@dataclass(frozen=True)
class CoverageDiagnostics:
    waterfall: dict[str, Any]
    failures: list[CoverageFailureRecord]
    by_target: list[dict[str, Any]]
    by_split: list[dict[str, Any]]
    by_ticker: list[dict[str, Any]]
    by_model: list[dict[str, Any]]


def build_coverage_diagnostics(
    *,
    labels: list[LabelRecord],
    split_assignments: list[SplitAssignmentRecord],
    features: list[FeatureRecord],
    model_manifest: list[ModelManifestRecord],
    predictions: list[PredictionRecord],
    tested_specifications: list[TestedSpecificationRecord],
) -> CoverageDiagnostics:
    labels_by_id = {label.label_id: label for label in labels}
    assignments_by_label: dict[str, list[SplitAssignmentRecord]] = defaultdict(list)
    for assignment in split_assignments:
        assignments_by_label[assignment.label_id].append(assignment)

    prediction_label_ids = {
        prediction.label_id
        for prediction in predictions
        if prediction.label_id is not None and prediction.label_id in labels_by_id
    }
    predictions_by_model_label = {
        (prediction.model_id, prediction.label_id)
        for prediction in predictions
        if prediction.label_id is not None and prediction.label_id in labels_by_id
    }
    feature_document_ids = {feature.source_document_id for feature in features}
    manifest_by_split_target = {}
    for record in model_manifest:
        target_name = _target_from_model_id(record.model_id)
        split_id = _split_from_model_id(record.model_id)
        if target_name and split_id:
            manifest_by_split_target[(split_id, target_name, record.model_id)] = record

    primary_specifications = [
        spec for spec in tested_specifications if spec.specification_role == "primary"
    ]
    primary_prediction_specs = [
        spec for spec in primary_specifications if spec.portfolio_method == "prediction_metric"
    ]
    primary_portfolio_specs = [
        spec for spec in primary_specifications if spec.portfolio_method != "prediction_metric"
    ]
    primary_covered_specs = [
        spec for spec in primary_specifications if _specification_metric_is_available(spec)
    ]
    primary_covered_prediction_specs = [
        spec for spec in primary_prediction_specs if _specification_metric_is_available(spec)
    ]
    primary_covered_portfolio_specs = [
        spec for spec in primary_portfolio_specs if _specification_metric_is_available(spec)
    ]

    failures: list[CoverageFailureRecord] = []
    eligible_oos_label_ids: set[str] = set()
    expected_model_label_pairs: set[tuple[str, str]] = set()
    model_predicted_pairs: set[tuple[str, str]] = set()
    portfolio_eligible_label_ids: set[str] = set()
    label_stage_by_id: dict[str, str] = {}

    for label in labels:
        assignments = assignments_by_label.get(label.label_id, [])
        oos_assignments = [item for item in assignments if item.role in OOS_ROLES]
        if not assignments:
            label_stage_by_id[label.label_id] = OUTSIDE_CONFIGURED_SPLIT_STAGE
            failures.append(
                _failure(
                    label,
                    failure_stage=OUTSIDE_CONFIGURED_SPLIT_STAGE,
                    failure_reason=OUTSIDE_CONFIGURED_SPLIT_REASON,
                    recommended_fix=(
                        "No model prediction is expected unless the experiment config is "
                        "expanded to include this event date in a validation/test window."
                    ),
                )
            )
            continue
        if not oos_assignments:
            label_stage_by_id[label.label_id] = "not_oos_expected"
            continue

        eligible_oos_label_ids.add(label.label_id)
        if any(assignment.role == "test" for assignment in oos_assignments):
            portfolio_eligible_label_ids.add(label.label_id)
        if label.label_id in prediction_label_ids:
            label_stage_by_id[label.label_id] = "ok_predicted"
        else:
            label_stage_by_id[label.label_id] = "missing_model_prediction"

        for assignment in oos_assignments:
            matching_manifests = [
                manifest
                for (split_id, target_name, _), manifest in manifest_by_split_target.items()
                if split_id == assignment.split_id and target_name == label.target_name
            ]
            if not matching_manifests:
                failures.append(
                    _failure(
                        label,
                        split_id=assignment.split_id,
                        expected_role=assignment.role,
                        failure_stage="model_not_expected_for_target",
                        failure_reason=(
                            "No model manifest exists for this split and target."
                        ),
                        observed_artifacts=["model_manifest.json"],
                        recommended_fix=(
                            "Run build-models for the split/target or remove the target from "
                            "formal comparison."
                        ),
                    )
                )
                continue

            for manifest in matching_manifests:
                pair = (manifest.model_id, label.label_id)
                expected_model_label_pairs.add(pair)
                if pair in predictions_by_model_label:
                    model_predicted_pairs.add(pair)
                    continue
                document_id = _document_id_from_label_id(label.label_id)
                if (
                    manifest.model_name not in BASELINE_MODEL_NAMES
                    and document_id not in feature_document_ids
                ):
                    stage = "missing_feature"
                    reason = "The source document has no feature records for this model."
                    fix = "Rebuild features for the document before model prediction."
                    artifacts = ["features.jsonl", "predictions.jsonl"]
                else:
                    stage = "missing_model_prediction"
                    reason = "The model was expected to score this eligible OOS label."
                    fix = "Regenerate predictions and preserve model-specific missing reasons."
                    artifacts = ["model_manifest.json", "predictions.jsonl"]
                failures.append(
                    _failure(
                        label,
                        split_id=assignment.split_id,
                        expected_role=assignment.role,
                        failure_stage=stage,
                        failure_reason=reason,
                        expected_model_id=manifest.model_id,
                        observed_artifacts=artifacts,
                        recommended_fix=fix,
                    )
                )

    raw_label_coverage = _ratio(len(prediction_label_ids), len(labels_by_id))
    eligible_oos_coverage = _ratio(
        len(prediction_label_ids & eligible_oos_label_ids),
        len(eligible_oos_label_ids),
    )
    model_expected_prediction_coverage = _ratio(
        len(model_predicted_pairs),
        len(expected_model_label_pairs),
    )
    primary_prediction_coverage = _ratio(
        len(primary_covered_prediction_specs),
        len(primary_prediction_specs),
    )
    primary_portfolio_coverage = _ratio(
        len(primary_covered_portfolio_specs),
        len(primary_portfolio_specs),
    )
    primary_spec_coverage = _ratio(
        len(primary_covered_specs),
        len(primary_specifications),
    )
    portfolio_eligible_coverage = _ratio(
        len(prediction_label_ids & portfolio_eligible_label_ids),
        len(portfolio_eligible_label_ids),
    )

    failure_counts = Counter(failure.failure_stage for failure in failures)
    waterfall = {
        "raw_label_coverage": raw_label_coverage,
        "eligible_oos_coverage": eligible_oos_coverage,
        "model_expected_prediction_coverage": model_expected_prediction_coverage,
        "portfolio_eligible_coverage": portfolio_eligible_coverage,
        "primary_prediction_coverage": primary_prediction_coverage,
        "primary_portfolio_coverage": primary_portfolio_coverage,
        "primary_spec_coverage": primary_spec_coverage,
        "counts": {
            "labels_total": len(labels_by_id),
            "predicted_unique_labels": len(prediction_label_ids),
            "eligible_oos_labels": len(eligible_oos_label_ids),
            "predicted_eligible_oos_labels": len(prediction_label_ids & eligible_oos_label_ids),
            "model_expected_label_pairs": len(expected_model_label_pairs),
            "model_predicted_label_pairs": len(model_predicted_pairs),
            "primary_expected_label_pairs": len(primary_specifications),
            "primary_predicted_label_pairs": len(primary_covered_specs),
            "primary_expected_specifications": len(primary_specifications),
            "primary_covered_specifications": len(primary_covered_specs),
            "primary_prediction_expected_specifications": len(primary_prediction_specs),
            "primary_prediction_covered_specifications": len(
                primary_covered_prediction_specs
            ),
            "primary_portfolio_expected_specifications": len(primary_portfolio_specs),
            "primary_portfolio_covered_specifications": len(
                primary_covered_portfolio_specs
            ),
            "portfolio_eligible_labels": len(portfolio_eligible_label_ids),
            "predicted_portfolio_eligible_labels": len(
                prediction_label_ids & portfolio_eligible_label_ids
            ),
        },
        "failure_counts": dict(sorted(failure_counts.items())),
        "top_failure_reasons": _top_failure_reasons(failures),
    }

    return CoverageDiagnostics(
        waterfall=waterfall,
        failures=failures,
        by_target=_coverage_by_dimension(
            labels=labels,
            label_stage_by_id=label_stage_by_id,
            prediction_label_ids=prediction_label_ids,
            eligible_oos_label_ids=eligible_oos_label_ids,
            dimension="target_name",
        ),
        by_split=_coverage_by_split(
            labels_by_id=labels_by_id,
            split_assignments=split_assignments,
            prediction_label_ids=prediction_label_ids,
        ),
        by_ticker=_coverage_by_dimension(
            labels=labels,
            label_stage_by_id=label_stage_by_id,
            prediction_label_ids=prediction_label_ids,
            eligible_oos_label_ids=eligible_oos_label_ids,
            dimension="ticker",
        ),
        by_model=_coverage_by_model(
            model_manifest=model_manifest,
            expected_pairs=expected_model_label_pairs,
            predicted_pairs=model_predicted_pairs,
            failures=failures,
        ),
    )


def write_coverage_diagnostics(
    diagnostics: CoverageDiagnostics,
    *,
    waterfall_path: str | Path,
    failures_path: str | Path,
    by_target_path: str | Path,
    by_split_path: str | Path,
    by_ticker_path: str | Path,
    by_model_path: str | Path,
) -> None:
    Path(waterfall_path).write_text(
        json.dumps(diagnostics.waterfall, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with Path(failures_path).open("w", encoding="utf-8") as file:
        for failure in diagnostics.failures:
            file.write(failure.model_dump_json() + "\n")
    _write_csv(by_target_path, diagnostics.by_target)
    _write_csv(by_split_path, diagnostics.by_split)
    _write_csv(by_ticker_path, diagnostics.by_ticker)
    _write_csv(by_model_path, diagnostics.by_model)


def _coverage_by_dimension(
    *,
    labels: list[LabelRecord],
    label_stage_by_id: dict[str, str],
    prediction_label_ids: set[str],
    eligible_oos_label_ids: set[str],
    dimension: str,
) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for label in labels:
        key = getattr(label, dimension)
        row = rows.setdefault(
            key,
            {
                dimension: key,
                "labels_total": 0,
                "eligible_oos_labels": 0,
                "predicted_unique_labels": 0,
                "predicted_eligible_oos_labels": 0,
                "raw_label_coverage": 0.0,
                "eligible_oos_coverage": 0.0,
                "top_failure_stage": "none",
            },
        )
        row["labels_total"] += 1
        if label.label_id in eligible_oos_label_ids:
            row["eligible_oos_labels"] += 1
        if label.label_id in prediction_label_ids:
            row["predicted_unique_labels"] += 1
        if label.label_id in prediction_label_ids and label.label_id in eligible_oos_label_ids:
            row["predicted_eligible_oos_labels"] += 1
    failure_stage_by_key: dict[str, Counter[str]] = defaultdict(Counter)
    for label in labels:
        key = getattr(label, dimension)
        stage = label_stage_by_id.get(label.label_id, "unknown")
        if stage != "ok_predicted":
            failure_stage_by_key[key][stage] += 1
    for key, row in rows.items():
        row["raw_label_coverage"] = _ratio(
            row["predicted_unique_labels"],
            row["labels_total"],
        )
        row["eligible_oos_coverage"] = _ratio(
            row["predicted_eligible_oos_labels"],
            row["eligible_oos_labels"],
        )
        if failure_stage_by_key[key]:
            row["top_failure_stage"] = failure_stage_by_key[key].most_common(1)[0][0]
    return sorted(rows.values(), key=lambda item: str(item[dimension]))


def _coverage_by_split(
    *,
    labels_by_id: dict[str, LabelRecord],
    split_assignments: list[SplitAssignmentRecord],
    prediction_label_ids: set[str],
) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for assignment in split_assignments:
        if assignment.label_id not in labels_by_id:
            continue
        row = rows.setdefault(
            assignment.split_id,
            {
                "split_id": assignment.split_id,
                "assigned_labels": 0,
                "eligible_oos_labels": 0,
                "predicted_eligible_oos_labels": 0,
                "eligible_oos_coverage": 0.0,
                "validation_labels": 0,
                "test_labels": 0,
                "train_labels": 0,
            },
        )
        row["assigned_labels"] += 1
        row[f"{assignment.role}_labels"] += 1
        if assignment.role in OOS_ROLES:
            row["eligible_oos_labels"] += 1
            if assignment.label_id in prediction_label_ids:
                row["predicted_eligible_oos_labels"] += 1
    for row in rows.values():
        row["eligible_oos_coverage"] = _ratio(
            row["predicted_eligible_oos_labels"],
            row["eligible_oos_labels"],
        )
    return sorted(rows.values(), key=lambda item: str(item["split_id"]))


def _coverage_by_model(
    *,
    model_manifest: list[ModelManifestRecord],
    expected_pairs: set[tuple[str, str]],
    predicted_pairs: set[tuple[str, str]],
    failures: list[CoverageFailureRecord],
) -> list[dict[str, Any]]:
    model_names = {record.model_id: record.model_name for record in model_manifest}
    rows: dict[str, dict[str, Any]] = {}
    for model_id, _ in expected_pairs:
        row = rows.setdefault(
            model_id,
            {
                "model_id": model_id,
                "model_name": model_names.get(model_id, "unknown"),
                "expected_label_pairs": 0,
                "predicted_label_pairs": 0,
                "model_expected_prediction_coverage": 0.0,
                "top_failure_stage": "none",
            },
        )
        row["expected_label_pairs"] += 1
    for model_id, _ in predicted_pairs:
        if model_id in rows:
            rows[model_id]["predicted_label_pairs"] += 1
    failure_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for failure in failures:
        if failure.expected_model_id:
            failure_counts[failure.expected_model_id][failure.failure_stage] += 1
    for model_id, row in rows.items():
        row["model_expected_prediction_coverage"] = _ratio(
            row["predicted_label_pairs"],
            row["expected_label_pairs"],
        )
        if failure_counts[model_id]:
            row["top_failure_stage"] = failure_counts[model_id].most_common(1)[0][0]
    return sorted(rows.values(), key=lambda item: str(item["model_id"]))


def _failure(
    label: LabelRecord,
    *,
    failure_stage: str,
    failure_reason: str,
    recommended_fix: str,
    split_id: str | None = None,
    expected_role: str | None = None,
    expected_model_id: str | None = None,
    observed_artifacts: list[str] | None = None,
) -> CoverageFailureRecord:
    return CoverageFailureRecord(
        label_id=label.label_id,
        ticker=label.ticker,
        target_name=label.target_name,
        event_date=label.event_time_utc.date(),
        split_id=split_id,
        expected_role=expected_role,
        failure_stage=failure_stage,
        failure_reason=failure_reason,
        expected_model_id=expected_model_id,
        observed_artifacts=observed_artifacts or ["labels.jsonl", "split_assignments.jsonl"],
        recommended_fix=recommended_fix,
    )


def _top_failure_reasons(failures: list[CoverageFailureRecord]) -> list[dict[str, Any]]:
    counter = Counter(
        (failure.failure_stage, failure.failure_reason) for failure in failures
    )
    return [
        {
            "failure_stage": stage,
            "failure_reason": reason,
            "count": count,
        }
        for (stage, reason), count in counter.most_common(10)
    ]


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _document_id_from_label_id(label_id: str) -> str:
    parts = label_id.rsplit(":", 2)
    if len(parts) != 3:
        return label_id
    return parts[0]


def _target_from_model_id(model_id: str) -> str:
    parts = model_id.split("::")
    if len(parts) < 3:
        return ""
    return parts[1]


def _split_from_model_id(model_id: str) -> str:
    parts = model_id.split("::")
    if len(parts) < 3:
        return ""
    return parts[2]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _specification_metric_is_available(specification: TestedSpecificationRecord) -> bool:
    if not isfinite(specification.raw_metric):
        return False
    if specification.raw_p_value is not None and not isfinite(specification.raw_p_value):
        return False
    return True
