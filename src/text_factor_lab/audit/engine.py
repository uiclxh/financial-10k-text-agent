from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import ValidationError

from text_factor_lab.audit.coverage import (
    OUTSIDE_CONFIGURED_SPLIT_STAGE,
    CoverageDiagnostics,
    build_coverage_diagnostics,
    write_coverage_diagnostics,
)
from text_factor_lab.schemas import (
    AuditCheckRecord,
    AuditReportRecord,
    DataLicenseManifestRecord,
    DocumentManifestRecord,
    EvaluationMetricRecord,
    FeatureManifestRecord,
    FeatureRecord,
    LabelRecord,
    ModelManifestRecord,
    ModelPredictionFailureRecord,
    MultipleTestingReportRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    PredictionRecord,
    RunStatusRecord,
    SplitAssignmentRecord,
    SplitLeakageRecord,
    TestedSpecificationRecord,
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
    split_assignments: Path
    split_leakage: Path
    features: Path
    feature_manifest: Path
    vocabulary: Path
    predictions: Path
    model_prediction_failures: Path
    model_manifest: Path
    tuning_log: Path
    evaluation_metrics: Path
    backtest_results: Path
    portfolio_metrics: Path
    monthly_portfolio_metrics: Path
    delisting_application_report: Path
    tested_specifications: Path
    multiple_testing_report: Path
    specification_registry: Path
    coverage_waterfall: Path
    coverage_failures: Path
    coverage_by_target: Path
    coverage_by_split: Path
    coverage_by_ticker: Path
    coverage_by_model: Path
    audit_report: Path

    @classmethod
    def from_run_dir(cls, run_dir: str | Path) -> AuditArtifactPaths:
        base = Path(run_dir)
        return cls(
            run_dir=base,
            document_manifest=base / "document_manifest.jsonl",
            labels=base / "labels.jsonl",
            split_assignments=base / "split_assignments.jsonl",
            split_leakage=base / "split_leakage.jsonl",
            features=base / "features.jsonl",
            feature_manifest=base / "feature_manifest.json",
            vocabulary=base / "vocabulary.json",
            predictions=base / "predictions.jsonl",
            model_prediction_failures=base / "model_prediction_failures.jsonl",
            model_manifest=base / "model_manifest.json",
            tuning_log=base / "tuning_log.json",
            evaluation_metrics=base / "evaluation_metrics.json",
            backtest_results=base / "backtest_results.json",
            portfolio_metrics=base / "portfolio_metrics.json",
            monthly_portfolio_metrics=base / "monthly_portfolio_metrics.json",
            delisting_application_report=base / "delisting_application_report.json",
            tested_specifications=base / "tested_specifications.jsonl",
            multiple_testing_report=base / "multiple_testing_report.json",
            specification_registry=base / "specification_registry.json",
            coverage_waterfall=base / "coverage_waterfall.json",
            coverage_failures=base / "coverage_failures.jsonl",
            coverage_by_target=base / "coverage_by_target.csv",
            coverage_by_split=base / "coverage_by_split.csv",
            coverage_by_ticker=base / "coverage_by_ticker.csv",
            coverage_by_model=base / "coverage_by_model.csv",
            audit_report=base / "audit_report.json",
        )


@dataclass(frozen=True)
class LoadedAuditArtifacts:
    document_manifest: list[DocumentManifestRecord]
    labels: list[LabelRecord]
    split_assignments: list[SplitAssignmentRecord]
    split_leakage: list[SplitLeakageRecord]
    features: list[FeatureRecord]
    feature_manifest: list[FeatureManifestRecord]
    vocabulary: dict[str, dict[str, dict[str, int]]] | None
    predictions: list[PredictionRecord]
    model_prediction_failures: list[ModelPredictionFailureRecord]
    model_manifest: list[ModelManifestRecord]
    tuning_log: list[TuningLogRecord]
    evaluation_metrics: list[EvaluationMetricRecord]
    backtest_results: list[PortfolioBacktestRecord]
    portfolio_metrics: list[PortfolioMetricRecord]
    monthly_portfolio_metrics: list[PortfolioMetricRecord]
    delisting_application_report: dict[str, object] | None
    tested_specifications: list[TestedSpecificationRecord]
    multiple_testing_report: MultipleTestingReportRecord | None
    specification_registry: dict[str, object] | None


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
    coverage_diagnostics = build_coverage_diagnostics(
        labels=artifacts.labels,
        split_assignments=artifacts.split_assignments,
        features=artifacts.features,
        model_manifest=artifacts.model_manifest,
        predictions=artifacts.predictions,
        tested_specifications=artifacts.tested_specifications,
    )
    write_coverage_diagnostics(
        coverage_diagnostics,
        waterfall_path=paths.coverage_waterfall,
        failures_path=paths.coverage_failures,
        by_target_path=paths.coverage_by_target,
        by_split_path=paths.coverage_by_split,
        by_ticker_path=paths.coverage_by_ticker,
        by_model_path=paths.coverage_by_model,
    )

    checks.extend(
        [
            _coverage_check(
                run_id,
                coverage_diagnostics,
                threshold,
                formal=config.run.run_type == "formal_run",
            ),
            _baseline_prediction_coverage_check(
                run_id,
                coverage_diagnostics,
                enabled_models=config.models.enabled,
            ),
            _primary_spec_coverage_check(
                run_id,
                coverage_diagnostics,
                formal=config.run.run_type == "formal_run",
            ),
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
            _model_manifest_version_check(run_id, artifacts.model_manifest),
            _model_selection_leakage_check(run_id, artifacts.tuning_log),
            _evaluation_check(run_id, artifacts.evaluation_metrics, artifacts.backtest_results),
            _rank_ic_tie_policy_check(run_id, artifacts.evaluation_metrics),
            _constant_baseline_rank_ic_check(
                run_id,
                artifacts.evaluation_metrics,
                artifacts.predictions,
                enabled_models=config.models.enabled,
            ),
            _constant_baseline_portfolio_check(
                run_id,
                artifacts.backtest_results,
                artifacts.portfolio_metrics,
                artifacts.monthly_portfolio_metrics,
            ),
            _evaluation_method_metadata_check(run_id, artifacts.evaluation_metrics),
            _delisting_application_check(
                run_id,
                artifacts.delisting_application_report,
                formal=config.run.run_type == "formal_run",
            ),
            _licensed_data_manifest_check(
                run_id=run_id,
                config=config,
                formal=config.run.run_type == "formal_run",
            ),
            _mixed_market_data_source_check(run_id=run_id, config=config),
            _tested_specifications_check(
                run_id,
                artifacts.tested_specifications,
                artifacts.evaluation_metrics,
                artifacts.backtest_results,
                artifacts.multiple_testing_report,
                artifacts.specification_registry,
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

    coverage = float(coverage_diagnostics.waterfall["raw_label_coverage"])
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
    split_assignments = _load_jsonl_artifact(
        run_id,
        paths.split_assignments,
        SplitAssignmentRecord,
        checks,
        required=True,
    )
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
    model_prediction_failures = _load_jsonl_artifact(
        run_id,
        paths.model_prediction_failures,
        ModelPredictionFailureRecord,
        checks,
        required=False,
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
    portfolio_metrics = _load_json_array_artifact(
        run_id,
        paths.portfolio_metrics,
        PortfolioMetricRecord,
        checks,
        required=False,
    )
    monthly_portfolio_metrics = _load_json_array_artifact(
        run_id,
        paths.monthly_portfolio_metrics,
        PortfolioMetricRecord,
        checks,
        required=False,
    )
    delisting_application_report = _load_optional_json_object(
        run_id,
        paths.delisting_application_report,
        checks,
        required=False,
    )
    tested_specifications = _load_jsonl_artifact(
        run_id,
        paths.tested_specifications,
        TestedSpecificationRecord,
        checks,
        required=False,
    )
    multiple_testing_report = _load_json_object_artifact(
        run_id,
        paths.multiple_testing_report,
        MultipleTestingReportRecord,
        checks,
        required=False,
    )
    specification_registry = _load_optional_json_object(
        run_id,
        paths.specification_registry,
        checks,
        required=False,
    )
    return LoadedAuditArtifacts(
        document_manifest=document_manifest,
        labels=labels,
        split_assignments=split_assignments,
        split_leakage=split_leakage,
        features=features,
        feature_manifest=feature_manifest,
        vocabulary=vocabulary,
        predictions=predictions,
        model_prediction_failures=model_prediction_failures,
        model_manifest=model_manifest,
        tuning_log=tuning_log,
        evaluation_metrics=evaluation_metrics,
        backtest_results=backtest_results,
        portfolio_metrics=portfolio_metrics,
        monthly_portfolio_metrics=monthly_portfolio_metrics,
        delisting_application_report=delisting_application_report,
        tested_specifications=tested_specifications,
        multiple_testing_report=multiple_testing_report,
        specification_registry=specification_registry,
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


def _load_json_object_artifact(
    run_id: str,
    path: Path,
    model: type[T],
    checks: list[AuditCheckRecord],
    *,
    required: bool,
) -> T | None:
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
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact must contain a JSON object")
        record = model.model_validate(payload)
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
        return None
    checks.append(
        _check(
            run_id,
            f"schema_valid::{path.name}",
            "schema",
            "pass",
            f"{path.name} parsed successfully",
            [str(path)],
            observed_value=1,
        )
    )
    return record


def _load_optional_json_object(
    run_id: str,
    path: Path,
    checks: list[AuditCheckRecord],
    *,
    required: bool,
) -> dict[str, object] | None:
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
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact must contain a JSON object")
    except (json.JSONDecodeError, ValueError, OSError) as exc:
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
        return None
    checks.append(
        _check(
            run_id,
            f"schema_valid::{path.name}",
            "schema",
            "pass",
            f"{path.name} parsed successfully",
            [str(path)],
            observed_value=1,
        )
    )
    return payload


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
    diagnostics: CoverageDiagnostics,
    threshold: float,
    *,
    formal: bool,
) -> AuditCheckRecord:
    raw = float(diagnostics.waterfall["raw_label_coverage"])
    eligible = float(diagnostics.waterfall["eligible_oos_coverage"])
    primary = float(diagnostics.waterfall["primary_spec_coverage"])
    primary_prediction = float(diagnostics.waterfall["primary_prediction_coverage"])
    primary_portfolio = float(diagnostics.waterfall["primary_portfolio_coverage"])
    counts = diagnostics.waterfall["counts"]
    missing_split = int(diagnostics.waterfall["failure_counts"].get("missing_split_assignment", 0))
    outside_split = int(
        diagnostics.waterfall["failure_counts"].get(OUTSIDE_CONFIGURED_SPLIT_STAGE, 0)
    )
    if formal:
        eligible_threshold = max(0.90, threshold)
        primary_threshold = 0.95
        status = (
            "fail"
            if eligible < eligible_threshold
            or primary < primary_threshold
            or missing_split > 0
            else "pass"
        )
        threshold_message = (
            f"formal eligible_oos>={eligible_threshold:.3f}, "
            f"primary_spec>={primary_threshold:.3f}"
        )
    else:
        eligible_threshold = max(0.80, min(threshold, 0.90))
        primary_threshold = 0.95
        status = "pass" if eligible >= eligible_threshold and missing_split == 0 else "warn"
        threshold_message = (
            f"exploratory eligible_oos>={eligible_threshold:.3f}; raw coverage is "
            f"reported; outside_split_window_labels={outside_split}"
        )
    return _check(
        run_id,
        "coverage_waterfall_threshold",
        "audit",
        status,
        (
            f"Raw={raw:.3f}; eligible_oos={eligible:.3f}; "
            f"primary_spec={primary:.3f}; "
            f"primary_prediction={primary_prediction:.3f}; "
            f"primary_portfolio={primary_portfolio:.3f}; "
            f"eligible_oos_labels={counts['eligible_oos_labels']}; "
            f"primary_specs={counts['primary_covered_specifications']}/"
            f"{counts['primary_expected_specifications']}; "
            f"{threshold_message}"
        ),
        [
            "coverage_waterfall.json",
            "coverage_failures.jsonl",
            "coverage_by_target.csv",
            "coverage_by_split.csv",
            "coverage_by_ticker.csv",
            "coverage_by_model.csv",
        ],
        observed_value=(
            f"raw={raw:.3f}, eligible_oos={eligible:.3f}, primary={primary:.3f}, "
            f"primary_prediction={primary_prediction:.3f}, "
            f"primary_portfolio={primary_portfolio:.3f}"
        ),
        threshold=f"eligible_oos={eligible_threshold:.3f}, primary={primary_threshold:.3f}",
    )


def _baseline_prediction_coverage_check(
    run_id: str,
    diagnostics: CoverageDiagnostics,
    *,
    enabled_models: list[str],
) -> AuditCheckRecord:
    if "historical_mean" not in enabled_models:
        return _check(
            run_id,
            "historical_mean_oos_coverage",
            "model",
            "warn",
            "historical_mean is not enabled; baseline OOS coverage cannot be guaranteed",
            ["model_manifest.json", "predictions.jsonl"],
        )
    historical_rows = [
        row for row in diagnostics.by_model if row.get("model_name") == "historical_mean"
    ]
    if not historical_rows:
        return _check(
            run_id,
            "historical_mean_oos_coverage",
            "model",
            "fail",
            "historical_mean is enabled but no model coverage row was produced",
            ["model_manifest.json", "predictions.jsonl"],
            observed_value=0,
            threshold=1,
        )
    missing = [
        row
        for row in historical_rows
        if float(row.get("model_expected_prediction_coverage", 0.0)) < 1.0
    ]
    return _check(
        run_id,
        "historical_mean_oos_coverage",
        "model",
        "fail" if missing else "pass",
        (
            "historical_mean must cover every eligible validation/test label; "
            f"{len(missing)} split-target rows are incomplete"
        ),
        ["coverage_by_model.csv", "predictions.jsonl"],
        observed_value=len(missing),
        threshold=0,
    )


def _primary_spec_coverage_check(
    run_id: str,
    diagnostics: CoverageDiagnostics,
    *,
    formal: bool,
) -> AuditCheckRecord:
    primary = float(diagnostics.waterfall["primary_spec_coverage"])
    expected = int(diagnostics.waterfall["counts"]["primary_expected_specifications"])
    covered = int(diagnostics.waterfall["counts"]["primary_covered_specifications"])
    if expected == 0:
        return _check(
            run_id,
            "primary_model_expected_coverage",
            "audit",
            "warn",
            "No primary model-label pairs were registered for coverage audit",
            ["tested_specifications.jsonl", "coverage_waterfall.json"],
            observed_value=0,
        )
    status = "pass" if primary >= 0.95 else "fail" if formal else "warn"
    return _check(
        run_id,
        "primary_model_expected_coverage",
        "audit",
        status,
        (
            f"Primary spec coverage is {primary:.3f} ({covered}/{expected}); "
            "threshold is 0.950"
        ),
        ["coverage_waterfall.json", "tested_specifications.jsonl", "predictions.jsonl"],
        observed_value=primary,
        threshold=0.95,
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
    purged_count = sum(record.severity == "purged" for record in split_leakage)
    warn_count = sum(record.severity == "warn" for record in split_leakage)
    status = "fail" if fail_count else "warn" if purged_count or warn_count else "pass"
    return _check(
        run_id,
        "split_purge_and_leakage",
        "split",
        status,
        (
            f"{fail_count} split records have severity=fail; "
            f"{purged_count} records were purged by embargo; "
            f"{warn_count} records have severity=warn"
        ),
        ["split_leakage.jsonl"],
        observed_value=f"fail={fail_count}, purged={purged_count}, warn={warn_count}",
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


def _model_manifest_version_check(
    run_id: str,
    model_manifest: list[ModelManifestRecord],
) -> AuditCheckRecord:
    from text_factor_lab.models import MODEL_TRAINING_VERSION

    invalid = [
        record.model_id
        for record in model_manifest
        if record.model_version != MODEL_TRAINING_VERSION
    ]
    return _check(
        run_id,
        "model_manifest_version",
        "model",
        "fail" if invalid or not model_manifest else "pass",
        (
            f"All model manifests use {MODEL_TRAINING_VERSION}."
            if model_manifest and not invalid
            else "Model manifests are missing or stale for: "
            + (", ".join(sorted(set(invalid))) if invalid else "all models")
        ),
        ["model_manifest.json"],
        observed_value=len(invalid) if model_manifest else "missing_manifests",
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
    tested_specifications: list[TestedSpecificationRecord],
    metrics: list[EvaluationMetricRecord],
    backtests: list[PortfolioBacktestRecord],
    multiple_testing_report: MultipleTestingReportRecord | None,
    specification_registry: dict[str, object] | None,
) -> AuditCheckRecord:
    target_count = len({record.target_name for record in metrics})
    expected_minimum = len([record for record in metrics if record.role == "test"]) + len(backtests)
    spec_count = len(tested_specifications)
    if spec_count == 0 and expected_minimum > 0:
        status = "fail"
        message = "No tested specifications were recorded for available evaluation artifacts"
    elif multiple_testing_report is None:
        status = "fail" if spec_count > 1 else "warn"
        message = "Tested specifications exist but multiple_testing_report.json is missing"
    elif multiple_testing_report.specification_count != spec_count:
        status = "fail"
        message = "multiple_testing_report specification_count does not match registry rows"
    elif specification_registry is None:
        status = "warn"
        message = "Specification registry artifact is missing"
    elif int(specification_registry.get("specification_count", -1)) != spec_count:
        status = "fail"
        message = "specification_registry specification_count does not match registry rows"
    elif int(specification_registry.get("role_counts", {}).get("primary", 0)) <= 0:
        status = "warn"
        message = "Specification registry has no primary specifications"
    else:
        status = "pass"
        message = (
            "Tested specifications, multiple-testing report, and specification "
            "registry are present"
        )
    return _check(
        run_id,
        "tested_specifications_disclosure",
        "audit",
        status,
        message,
        [
            "tested_specifications.jsonl",
            "multiple_testing_report.json",
            "specification_registry.json",
        ],
        observed_value=f"targets={target_count}, specs={spec_count}",
    )


def _evaluation_check(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
    backtests: list[PortfolioBacktestRecord],
) -> AuditCheckRecord:
    if not metrics:
        return _check(
            run_id,
            "evaluation_outputs_present",
            "evaluation",
            "fail",
            "Evaluation metrics must be present.",
            ["evaluation_metrics.json", "backtest_results.json"],
            observed_value=f"metrics={len(metrics)}, backtests={len(backtests)}",
        )
    return _check(
        run_id,
        "evaluation_outputs_present",
        "evaluation",
        "pass",
        (
            "Evaluation metrics are present; "
            + (
                "eligible portfolio backtests are present."
                if backtests
                else "no portfolio passed the tie-aware eligibility policy."
            )
        ),
        ["evaluation_metrics.json", "backtest_results.json"],
        observed_value=f"metrics={len(metrics)}, backtests={len(backtests)}",
    )


def _rank_ic_tie_policy_check(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
) -> AuditCheckRecord:
    invalid = [
        metric.model_id
        for metric in metrics
        if metric.rank_method != "average"
        or metric.constant_prediction_policy != "return_zero"
    ]
    return _check(
        run_id,
        "rank_ic_tie_policy",
        "evaluation",
        "fail" if invalid else "pass",
        (
            "Rank IC uses average ranks for ties and returns zero for constant predictions."
            if not invalid
            else "Rank IC tie or constant-prediction policy is invalid for: "
            + ", ".join(sorted(set(invalid)))
        ),
        ["evaluation_metrics.json"],
        observed_value=len(invalid),
        threshold=0,
    )


def _constant_baseline_rank_ic_check(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
    predictions: list[PredictionRecord],
    *,
    enabled_models: list[str],
    tolerance: float = 1e-12,
) -> AuditCheckRecord:
    if "historical_mean" not in enabled_models:
        return _check(
            run_id,
            "constant_baseline_rank_ic",
            "evaluation",
            "pass",
            "Historical-mean baseline is not enabled; constant-baseline IC check "
            "is not applicable.",
            ["config_snapshot.yaml"],
            observed_value="not_applicable",
        )

    baseline_metrics = [
        metric
        for metric in metrics
        if metric.model_id.split("::", maxsplit=1)[0] == "historical_mean"
    ]
    violations = [
        metric.model_id
        for metric in baseline_metrics
        if any(
            abs(value) > tolerance
            for value in (
                metric.rank_ic,
                metric.rank_ic_t_stat,
                metric.rank_ic_newey_west_t_stat,
            )
        )
    ]

    prediction_groups: dict[tuple[str, str, str | None], set[float]] = {}
    for prediction in predictions:
        if prediction.model_id.split("::", maxsplit=1)[0] != "historical_mean":
            continue
        key = (prediction.model_id, prediction.split_id, prediction.role)
        prediction_groups.setdefault(key, set()).add(prediction.prediction_value)
    non_constant_groups = [
        f"{model_id}:{split_id}:{role}"
        for (model_id, split_id, role), values in prediction_groups.items()
        if len(values) > 1
    ]

    if not baseline_metrics:
        violations.append("missing_historical_mean_metrics")
    violations.extend(non_constant_groups)
    return _check(
        run_id,
        "constant_baseline_rank_ic",
        "evaluation",
        "fail" if violations else "pass",
        (
            "Historical-mean predictions are constant and all split/ALL_SPLITS Rank IC "
            "statistics are zero."
            if not violations
            else "Historical-mean baseline produced invalid ranking diagnostics: "
            + ", ".join(sorted(set(violations)))
        ),
        ["predictions.jsonl", "evaluation_metrics.json"],
        observed_value=len(violations),
        threshold=0,
    )


def _constant_baseline_portfolio_check(
    run_id: str,
    backtests: list[PortfolioBacktestRecord],
    portfolio_metrics: list[PortfolioMetricRecord],
    monthly_portfolio_metrics: list[PortfolioMetricRecord],
) -> AuditCheckRecord:
    invalid = [
        record.model_id
        for record in [*backtests, *portfolio_metrics, *monthly_portfolio_metrics]
        if record.model_id.split("::", maxsplit=1)[0] == "historical_mean"
    ]
    return _check(
        run_id,
        "constant_baseline_portfolio",
        "evaluation",
        "fail" if invalid else "pass",
        (
            "No portfolio was constructed from the constant historical-mean signal."
            if not invalid
            else "Constant historical-mean scores produced invalid portfolio artifacts: "
            + ", ".join(sorted(set(invalid)))
        ),
        [
            "backtest_results.json",
            "portfolio_metrics.json",
            "monthly_portfolio_metrics.json",
        ],
        observed_value=len(invalid),
        threshold=0,
    )


def _evaluation_method_metadata_check(
    run_id: str,
    metrics: list[EvaluationMetricRecord],
) -> AuditCheckRecord:
    from text_factor_lab.backtest.evaluation import BACKTEST_VERSION

    invalid: list[str] = []
    for metric in metrics:
        if metric.evaluation_version != BACKTEST_VERSION:
            valid = False
        elif metric.split_id == "ALL_SPLITS":
            valid = (
                metric.aggregation_method == "split_mean_ic_weighted_error_metrics"
                and metric.ic_grouping == "split"
                and metric.split_count >= 1
            )
        else:
            valid = (
                metric.aggregation_method
                == "pooled_window_metrics_with_date_ic_diagnostics"
                and metric.ic_grouping in {"event_date_cross_section", "pooled_fallback"}
                and metric.split_count == 1
            )
        if not valid:
            invalid.append(metric.model_id)

    return _check(
        run_id,
        "evaluation_method_metadata",
        "evaluation",
        "fail" if invalid or not metrics else "pass",
        (
            "Evaluation aggregation and IC-grouping metadata match the registered method."
            if metrics and not invalid
            else "Evaluation method metadata is missing or inconsistent for: "
            + (", ".join(sorted(set(invalid))) if invalid else "all metrics")
        ),
        ["evaluation_metrics.json"],
        observed_value=len(invalid) if metrics else "missing_metrics",
        threshold=0,
    )


def _delisting_application_check(
    run_id: str,
    report: dict[str, object] | None,
    *,
    formal: bool,
) -> AuditCheckRecord:
    if report is None:
        return _check(
            run_id,
            "delisting_application_report",
            "evaluation",
            "warn",
            "delisting_application_report.json is missing",
            ["delisting_application_report.json"],
        )
    missing = int(report.get("missing_delisting_returns", 0) or 0)
    status = "pass"
    if missing:
        status = "fail" if formal else "warn"
    return _check(
        run_id,
        "delisting_application_report",
        "evaluation",
        status,
        (
            "Delisting return handling checked; "
            f"applied={report.get('delisting_returns_applied', 0)}, "
            f"missing={missing}"
        ),
        ["delisting_application_report.json"],
        observed_value=missing,
        threshold=0,
    )


def _licensed_data_manifest_check(
    *,
    run_id: str,
    config,
    formal: bool,
) -> AuditCheckRecord:
    if not formal:
        return _check(
            run_id,
            "licensed_data_manifest",
            "data",
            "pass",
            "Exploratory run does not require a licensed data manifest.",
            ["data_provider.data_license_manifest_file"],
        )

    manifest_path = config.data_provider.data_license_manifest_file
    if manifest_path is None:
        return _check(
            run_id,
            "licensed_data_manifest",
            "data",
            "fail",
            "Formal CRSP/WRDS runs require data_provider.data_license_manifest_file.",
            ["config_snapshot.yaml"],
        )

    path = Path(manifest_path)
    if not path.exists():
        return _check(
            run_id,
            "licensed_data_manifest",
            "data",
            "fail",
            f"Licensed data manifest is missing: {path}",
            [str(path)],
        )

    try:
        manifest = DataLicenseManifestRecord.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except (json.JSONDecodeError, OSError, ValidationError) as exc:
        return _check(
            run_id,
            "licensed_data_manifest",
            "data",
            "fail",
            f"Licensed data manifest failed validation: {exc}",
            [str(path)],
        )

    mismatches: list[str] = []
    expected_pairs = {
        "market_data_provider": config.data_provider.market_data_provider,
        "filing_provider": config.data_provider.filing_provider,
        "price_source": config.data_provider.price_source,
        "return_source": config.data_provider.return_source,
        "delisting_return_source": config.data_provider.delisting_return_source,
        "link_source": config.data_provider.link_source,
    }
    for field_name, expected in expected_pairs.items():
        observed = getattr(manifest, field_name)
        if expected is not None and observed != expected:
            mismatches.append(f"{field_name}: expected={expected}, observed={observed}")
    if manifest.raw_data_committed:
        mismatches.append("raw_data_committed must be false")
    if manifest.allow_public_yahoo_fallback:
        mismatches.append("allow_public_yahoo_fallback must be false")
    if not manifest.delisting_return_source:
        mismatches.append("delisting_return_source is required")
    if not manifest.link_source:
        mismatches.append("link_source is required")

    return _check(
        run_id,
        "licensed_data_manifest",
        "data",
        "fail" if mismatches else "pass",
        (
            "Licensed CRSP/WRDS data manifest checked. "
            + ("; ".join(mismatches) if mismatches else "No blockers found.")
        ),
        [str(path)],
        observed_value=len(mismatches),
        threshold=0,
    )


def _mixed_market_data_source_check(*, run_id: str, config) -> AuditCheckRecord:
    price_source = str(config.data_provider.price_source).lower()
    return_source = str(config.data_provider.return_source).lower()
    provider = str(config.data_provider.market_data_provider).lower()
    allow_yahoo = bool(config.data_provider.allow_public_yahoo_fallback)
    uses_declared_mixed_source = (
        "mixed" in price_source
        or "mixed" in return_source
        or "yahoo_fallback" in price_source
        or (provider == "fmp_alpha" and allow_yahoo)
    )
    if not uses_declared_mixed_source:
        return _check(
            run_id,
            "mixed_market_data_source_boundary",
            "data",
            "pass",
            "Market data source boundary is single-provider or no public fallback is enabled.",
            ["config_snapshot.yaml"],
        )
    return _check(
        run_id,
        "mixed_market_data_source_boundary",
        "data",
        "warn",
        (
            "Mixed market data source detected. Treat the run as an applied-grade "
            "pilot; do not present market-data-dependent portfolio evidence as a "
            "CRSP/WRDS-equivalent formal result."
        ),
        ["config_snapshot.yaml", "license_manifest.json"],
        observed_value=(
            f"provider={config.data_provider.market_data_provider}, "
            f"price_source={config.data_provider.price_source}, "
            f"return_source={config.data_provider.return_source}, "
            f"allow_public_yahoo_fallback={allow_yahoo}"
        ),
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
