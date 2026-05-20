from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import ValidationError

from text_factor_lab.schemas import (
    AuditCheckRecord,
    AuditReportRecord,
    DocumentManifestRecord,
    EvaluationMetricRecord,
    FeatureManifestRecord,
    FeatureRecord,
    LabelRecord,
    ModelManifestRecord,
    PortfolioBacktestRecord,
    PredictionRecord,
    RunStatusRecord,
    SplitLeakageRecord,
    TuningLogRecord,
    load_experiment_config,
)
from text_factor_lab.schemas.base import StrictBaseModel
from text_factor_lab.schemas.run_status import AuditStatus

T = TypeVar("T", bound=StrictBaseModel)


@dataclass(frozen=True)
class AuditArtifactPaths:
    run_dir: Path
    document_manifest: Path
    labels: Path
    split_leakage: Path
    features: Path
    feature_manifest: Path
    vocabulary: Path
    predictions: Path
    model_manifest: Path
    tuning_log: Path
    evaluation_metrics: Path
    backtest_results: Path
    audit_report: Path

    @classmethod
    def from_run_dir(cls, run_dir: str | Path) -> AuditArtifactPaths:
        base = Path(run_dir)
        return cls(
            run_dir=base,
            document_manifest=base / "document_manifest.jsonl",
            labels=base / "labels.jsonl",
            split_leakage=base / "split_leakage.jsonl",
            features=base / "features.jsonl",
            feature_manifest=base / "feature_manifest.json",
            vocabulary=base / "vocabulary.json",
            predictions=base / "predictions.jsonl",
            model_manifest=base / "model_manifest.json",
            tuning_log=base / "tuning_log.json",
            evaluation_metrics=base / "evaluation_metrics.json",
            backtest_results=base / "backtest_results.json",
            audit_report=base / "audit_report.json",
        )


@dataclass(frozen=True)
class LoadedAuditArtifacts:
    document_manifest: list[DocumentManifestRecord]
    labels: list[LabelRecord]
    split_leakage: list[SplitLeakageRecord]
    features: list[FeatureRecord]
    feature_manifest: list[FeatureManifestRecord]
    vocabulary: dict[str, dict[str, dict[str, int]]] | None
    predictions: list[PredictionRecord]
    model_manifest: list[ModelManifestRecord]
    tuning_log: list[TuningLogRecord]
    evaluation_metrics: list[EvaluationMetricRecord]
    backtest_results: list[PortfolioBacktestRecord]


def audit_run(
    *,
    run_id: str,
    run_dir: str | Path | None = None,
    config_path: str | Path | None = None,
    coverage_threshold: float | None = None,
) -> AuditReportRecord:
    resolved_run_dir = (
        Path(run_dir) if run_dir is not None else Path("runs/text_factor_lab") / run_id
    )
    paths = AuditArtifactPaths.from_run_dir(resolved_run_dir)
    config = _load_config(paths.run_dir, config_path)
    threshold = (
        float(coverage_threshold)
        if coverage_threshold is not None
        else float(config.audit.coverage_threshold)
    )
    checks: list[AuditCheckRecord] = []
    artifacts = _load_artifacts(
        run_id=run_id,
        paths=paths,
        checks=checks,
        formal=config.run.run_type,
    )

    checks.extend(
        [
            _coverage_check(run_id, artifacts.labels, artifacts.predictions, threshold),
            _prediction_alignment_check(run_id, artifacts.labels, artifacts.predictions),
            _split_leakage_check(run_id, artifacts.split_leakage),
            _feature_lookahead_check(run_id, artifacts.features),
            _feature_manifest_fit_scope_check(run_id, artifacts.feature_manifest),
            _feature_manifest_vocabulary_check(
                run_id,
                artifacts.feature_manifest,
                artifacts.vocabulary,
            ),
            _model_manifest_check(run_id, artifacts.model_manifest),
            _model_selection_leakage_check(run_id, artifacts.tuning_log),
            _evaluation_check(run_id, artifacts.evaluation_metrics, artifacts.backtest_results),
            _tested_specifications_check(
                run_id,
                artifacts.model_manifest,
                artifacts.evaluation_metrics,
            ),
            _formal_metadata_check(
                run_id=run_id,
                documents=artifacts.document_manifest,
                feature_manifest=artifacts.feature_manifest,
                formal=config.run.run_type == "formal_run",
                require_license=config.audit.require_license_note,
                require_available_time=config.audit.require_available_time,
            ),
        ]
    )

    coverage = _coverage(artifacts.labels, artifacts.predictions)
    audit_status = _audit_status(checks)
    report = AuditReportRecord(
        run_id=run_id,
        run_type=config.run.run_type,
        audit_status=audit_status,
        formal_result_allowed=config.run.run_type == "formal_run" and audit_status == "pass",
        coverage=coverage,
        check_count=len(checks),
        fail_count=sum(check.status == "fail" for check in checks),
        warn_count=sum(check.status == "warn" for check in checks),
        checks=checks,
        created_at_utc=datetime.now(UTC),
    )
    write_audit_report_json(report, paths.audit_report)
    _update_run_status(paths.run_dir, report)
    return report


def write_audit_report_json(report: AuditReportRecord, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, indent=2)
        file.write("\n")


def _load_config(run_dir: Path, config_path: str | Path | None):
    if config_path is not None:
        return load_experiment_config(config_path)
    snapshot = run_dir / "config_snapshot.yaml"
    if snapshot.exists():
        return load_experiment_config(snapshot)
    return load_experiment_config("configs/text_factor_lab/mvp_v0.yaml")


def _load_artifacts(
    *,
    run_id: str,
    paths: AuditArtifactPaths,
    checks: list[AuditCheckRecord],
    formal: str,
) -> LoadedAuditArtifacts:
    document_manifest = _load_jsonl_artifact(
        run_id,
        paths.document_manifest,
        DocumentManifestRecord,
        checks,
        required=formal == "formal_run",
    )
    labels = _load_jsonl_artifact(run_id, paths.labels, LabelRecord, checks, required=True)
    split_leakage = _load_jsonl_artifact(
        run_id, paths.split_leakage, SplitLeakageRecord, checks, required=False
    )
    features = _load_jsonl_artifact(
        run_id, paths.features, FeatureRecord, checks, required=formal == "formal_run"
    )
    feature_manifest = _load_json_array_artifact(
        run_id,
        paths.feature_manifest,
        FeatureManifestRecord,
        checks,
        required=formal == "formal_run",
    )
    vocabulary = _load_vocabulary_json(paths.vocabulary)
    predictions = _load_jsonl_artifact(
        run_id, paths.predictions, PredictionRecord, checks, required=True
    )
    model_manifest = _load_json_array_artifact(
        run_id, paths.model_manifest, ModelManifestRecord, checks, required=True
    )
    evaluation_metrics = _load_json_array_artifact(
        run_id, paths.evaluation_metrics, EvaluationMetricRecord, checks, required=True
    )
    tuning_log = _load_json_array_artifact(
        run_id, paths.tuning_log, TuningLogRecord, checks, required=True
    )
    backtest_results = _load_json_array_artifact(
        run_id, paths.backtest_results, PortfolioBacktestRecord, checks, required=True
    )
    return LoadedAuditArtifacts(
        document_manifest=document_manifest,
        labels=labels,
        split_leakage=split_leakage,
        features=features,
        feature_manifest=feature_manifest,
        vocabulary=vocabulary,
        predictions=predictions,
        model_manifest=model_manifest,
        tuning_log=tuning_log,
        evaluation_metrics=evaluation_metrics,
        backtest_results=backtest_results,
    )


def _load_jsonl_artifact(
    run_id: str,
    path: Path,
    model: type[T],
    checks: list[AuditCheckRecord],
    *,
    required: bool,
) -> list[T]:
    if not path.exists():
        checks.append(
            _check(
                run_id,
                f"artifact_exists::{path.name}",
                "artifact",
                "fail" if required else "warn",
                f"Missing {'required' if required else 'optional'} artifact: {path.name}",
                [str(path)],
            )
        )
        return []
    records: list[T] = []
    current_line = 0
    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                current_line = line_number
                if line.strip():
                    records.append(model.model_validate(json.loads(line)))
    except (json.JSONDecodeError, ValidationError, OSError) as exc:
        checks.append(
            _check(
                run_id,
                f"schema_valid::{path.name}",
                "schema",
                "fail",
                f"{path.name} failed schema validation: {exc}",
                [f"{path}:{current_line or '?'}"],
            )
        )
        return []
    checks.append(
        _check(
            run_id,
            f"schema_valid::{path.name}",
            "schema",
            "pass",
            f"{path.name} parsed successfully",
            [str(path)],
            observed_value=len(records),
        )
    )
    return records


def _load_json_array_artifact(
    run_id: str,
    path: Path,
    model: type[T],
    checks: list[AuditCheckRecord],
    *,
    required: bool,
) -> list[T]:
    if not path.exists():
        checks.append(
            _check(
                run_id,
                f"artifact_exists::{path.name}",
                "artifact",
                "fail" if required else "warn",
                f"Missing {'required' if required else 'optional'} artifact: {path.name}",
                [str(path)],
            )
        )
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("artifact must contain a JSON array")
        records = [model.model_validate(row) for row in payload]
    except (json.JSONDecodeError, ValidationError, ValueError, OSError) as exc:
        checks.append(
            _check(
                run_id,
                f"schema_valid::{path.name}",
                "schema",
                "fail",
                f"{path.name} failed schema validation: {exc}",
                [str(path)],
            )
        )
        return []
    checks.append(
        _check(
            run_id,
            f"schema_valid::{path.name}",
            "schema",
            "pass",
            f"{path.name} parsed successfully",
            [str(path)],
            observed_value=len(records),
        )
    )
    return records


def _load_vocabulary_json(path: Path) -> dict[str, dict[str, dict[str, int]]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _coverage_check(
    run_id: str,
    labels: list[LabelRecord],
    predictions: list[PredictionRecord],
    threshold: float,
) -> AuditCheckRecord:
    observed = _coverage(labels, predictions)
    status = "pass" if observed >= threshold else "fail"
    return _check(
        run_id,
        "coverage_threshold",
        "audit",
        status,
        f"Prediction-label coverage is {observed:.3f}; threshold is {threshold:.3f}",
        ["labels.jsonl", "predictions.jsonl"],
        observed_value=observed,
        threshold=threshold,
    )


def _prediction_alignment_check(
    run_id: str,
    labels: list[LabelRecord],
    predictions: list[PredictionRecord],
) -> AuditCheckRecord:
    label_ids = {label.label_id for label in labels}
    missing = [
        prediction.label_id
        for prediction in predictions
        if prediction.label_id is None or prediction.label_id not in label_ids
    ]
    return _check(
        run_id,
        "prediction_label_alignment",
        "model",
        "fail" if missing else "pass",
        f"{len(missing)} predictions do not map to a valid label_id",
        ["labels.jsonl", "predictions.jsonl"],
        observed_value=len(missing),
        threshold=0,
    )


def _split_leakage_check(
    run_id: str,
    split_leakage: list[SplitLeakageRecord],
) -> AuditCheckRecord:
    fail_count = sum(record.severity == "fail" for record in split_leakage)
    return _check(
        run_id,
        "split_leakage_failures",
        "split",
        "fail" if fail_count else "pass",
        f"{fail_count} split leakage records have severity=fail",
        ["split_leakage.jsonl"],
        observed_value=fail_count,
        threshold=0,
    )


def _feature_lookahead_check(run_id: str, features: list[FeatureRecord]) -> AuditCheckRecord:
    leaked = sum(feature.feature_time_utc > feature.prediction_time_utc for feature in features)
    return _check(
        run_id,
        "feature_lookahead",
        "feature",
        "fail" if leaked else "pass",
        f"{leaked} feature records have feature_time_utc after prediction_time_utc",
        ["features.jsonl"],
        observed_value=leaked,
        threshold=0,
    )


def _model_manifest_check(
    run_id: str,
    model_manifest: list[ModelManifestRecord],
) -> AuditCheckRecord:
    invalid = sum((record.train_observation_count or 0) <= 0 for record in model_manifest)
    return _check(
        run_id,
        "model_manifest_training_rows",
        "model",
        "fail" if invalid else "pass",
        f"{invalid} model manifests have no training observations",
        ["model_manifest.json"],
        observed_value=invalid,
        threshold=0,
    )


def _feature_manifest_fit_scope_check(
    run_id: str,
    feature_manifest: list[FeatureManifestRecord],
) -> AuditCheckRecord:
    invalid = [
        record.feature_version
        for record in feature_manifest
        if record.feature_method == "tfidf" and record.fit_scope != "train_window_only"
    ]
    return _check(
        run_id,
        "tfidf_train_window_fit_scope",
        "feature",
        "fail" if invalid else "pass",
        f"{len(invalid)} TF-IDF feature manifests are not train-window-only",
        ["feature_manifest.json"],
        observed_value=len(invalid),
        threshold=0,
    )


def _feature_manifest_vocabulary_check(
    run_id: str,
    feature_manifest: list[FeatureManifestRecord],
    vocabulary: dict[str, dict[str, dict[str, int]]] | None,
) -> AuditCheckRecord:
    tfidf_manifests = [record for record in feature_manifest if record.feature_method == "tfidf"]
    if not tfidf_manifests:
        return _check(
            run_id,
            "feature_manifest_vocabulary_alignment",
            "feature",
            "pass",
            "No TF-IDF feature manifests require vocabulary alignment",
            ["feature_manifest.json", "vocabulary.json"],
            observed_value=0,
        )
    if vocabulary is None:
        return _check(
            run_id,
            "feature_manifest_vocabulary_alignment",
            "feature",
            "fail",
            "TF-IDF feature manifests exist but vocabulary.json is missing or invalid",
            ["feature_manifest.json", "vocabulary.json"],
            observed_value=len(tfidf_manifests),
        )
    mismatches = 0
    for record in tfidf_manifests:
        terms = vocabulary.get(record.split_id, {}).get(record.text_scope, {})
        if len(terms) != record.vocabulary_size:
            mismatches += 1
    return _check(
        run_id,
        "feature_manifest_vocabulary_alignment",
        "feature",
        "fail" if mismatches else "pass",
        f"{mismatches} TF-IDF feature manifests disagree with vocabulary.json",
        ["feature_manifest.json", "vocabulary.json"],
        observed_value=mismatches,
        threshold=0,
    )


def _model_selection_leakage_check(
    run_id: str,
    tuning_logs: list[TuningLogRecord],
) -> AuditCheckRecord:
    leaked = [
        record.model_id
        for record in tuning_logs
        if record.validation_metric not in {"not_applicable", "validation_rank_ic"}
        or "test" in record.validation_metric.lower()
    ]
    return _check(
        run_id,
        "model_selection_validation_only",
        "model",
        "fail" if leaked else "pass",
        f"{len(leaked)} tuning logs use a non-validation model-selection metric",
        ["tuning_log.json"],
        observed_value=len(leaked),
        threshold=0,
    )


def _tested_specifications_check(
    run_id: str,
    model_manifest: list[ModelManifestRecord],
    metrics: list[EvaluationMetricRecord],
) -> AuditCheckRecord:
    model_count = len({record.model_id for record in model_manifest})
    target_count = len({record.target_name for record in metrics})
    spec_count = len(
        {
            (record.model_id, record.target_name, record.split_id, record.role)
            for record in metrics
        }
    )
    status = "pass" if spec_count else "fail"
    return _check(
        run_id,
        "tested_specifications_disclosure",
        "audit",
        status,
        (
            "Tested specifications are disclosed through model_manifest and "
            "evaluation_metrics artifacts"
        ),
        ["model_manifest.json", "evaluation_metrics.json"],
        observed_value=f"models={model_count}, targets={target_count}, specs={spec_count}",
    )


def _evaluation_check(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
    backtests: list[PortfolioBacktestRecord],
) -> AuditCheckRecord:
    if not metrics or not backtests:
        return _check(
            run_id,
            "evaluation_outputs_present",
            "evaluation",
            "fail",
            "Evaluation metrics and backtest results must both be present",
            ["evaluation_metrics.json", "backtest_results.json"],
            observed_value=f"metrics={len(metrics)}, backtests={len(backtests)}",
        )
    return _check(
        run_id,
        "evaluation_outputs_present",
        "evaluation",
        "pass",
        "Evaluation metrics and backtest results are present",
        ["evaluation_metrics.json", "backtest_results.json"],
        observed_value=f"metrics={len(metrics)}, backtests={len(backtests)}",
    )


def _formal_metadata_check(
    *,
    run_id: str,
    documents: list[DocumentManifestRecord],
    feature_manifest: list[FeatureManifestRecord],
    formal: bool,
    require_license: bool,
    require_available_time: bool,
) -> AuditCheckRecord:
    if not formal:
        return _check(
            run_id,
            "formal_metadata_gate",
            "audit",
            "pass",
            "Exploratory run does not require formal metadata gate",
            ["document_manifest.jsonl", "feature_manifest.json"],
        )
    missing_license = (
        sum(not document.license_note for document in documents) if require_license else 0
    )
    missing_time = (
        sum(document.available_time_utc is None for document in documents)
        if require_available_time
        else 0
    )
    missing_feature_manifest = 0 if feature_manifest else 1
    failures = missing_license + missing_time + missing_feature_manifest
    return _check(
        run_id,
        "formal_metadata_gate",
        "audit",
        "fail" if failures else "pass",
        (
            "Formal metadata gate checked license_note, available_time_utc, "
            "and feature_manifest presence"
        ),
        ["document_manifest.jsonl", "feature_manifest.json"],
        observed_value=failures,
        threshold=0,
    )


def _coverage(labels: list[LabelRecord], predictions: list[PredictionRecord]) -> float:
    if not labels:
        return 0.0
    label_ids = {label.label_id for label in labels}
    predicted_label_ids = {
        prediction.label_id
        for prediction in predictions
        if prediction.label_id is not None and prediction.label_id in label_ids
    }
    return len(predicted_label_ids) / len(label_ids)


def _audit_status(checks: list[AuditCheckRecord]) -> AuditStatus:
    if any(check.status == "fail" for check in checks):
        return "fail"
    if any(check.status == "warn" for check in checks):
        return "warn"
    return "pass"


def _check(
    run_id: str,
    check_id: str,
    stage: str,
    status: str,
    message: str,
    affected_artifacts: list[str],
    *,
    observed_value: float | int | str | None = None,
    threshold: float | int | str | None = None,
) -> AuditCheckRecord:
    severity = "fail" if status == "fail" else "warn" if status == "warn" else "info"
    return AuditCheckRecord(
        run_id=run_id,
        check_id=check_id,
        stage=stage,
        severity=severity,
        status=status,
        message=message,
        affected_artifacts=affected_artifacts,
        observed_value=observed_value,
        threshold=threshold,
        created_at_utc=datetime.now(UTC),
    )


def _update_run_status(run_dir: Path, report: AuditReportRecord) -> None:
    status_path = run_dir / "run_status.json"
    if not status_path.exists():
        return
    status = RunStatusRecord.model_validate(json.loads(status_path.read_text(encoding="utf-8")))
    next_status = "audited" if report.audit_status in {"pass", "warn"} else "rejected"
    updated = status.model_copy(
        update={
            "status": next_status,
            "audit_status": report.audit_status,
            "coverage": report.coverage,
            "failure_reason": None
            if report.audit_status in {"pass", "warn"}
            else "Audit failed; see audit_report.json",
            "updated_at_utc": datetime.now(UTC),
        }
    )
    with status_path.open("w", encoding="utf-8") as file:
        json.dump(updated.model_dump(mode="json"), file, indent=2)
        file.write("\n")
