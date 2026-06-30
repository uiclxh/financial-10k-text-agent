from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from text_factor_lab.schemas import (
    AuditReportRecord,
    DataLicenseManifestRecord,
    EvaluationMetricRecord,
    FeatureManifestRecord,
    ModelManifestRecord,
    MultipleTestingReportRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    RunStatusRecord,
    TuningLogRecord,
    load_experiment_config,
)

REPORT_VERSION = "report-generator-v0"


@dataclass(frozen=True)
class ReportArtifactPaths:
    run_dir: Path
    config: Path
    run_status: Path
    audit_report: Path
    evaluation_metrics: Path
    backtest_results: Path
    delisting_application_report: Path
    model_manifest: Path
    tuning_log: Path
    feature_manifest: Path
    vocabulary_manifest: Path
    section_length_quality_report: Path
    parser_manual_review_appendix: Path
    prediction_distribution_report: Path
    feature_ablation_summary: Path
    primary_rank_ic_bootstrap_report: Path
    portfolio_metrics: Path
    monthly_portfolio_metrics: Path
    multiple_testing_report: Path
    specification_registry: Path
    universe_quality_report: Path
    coverage_waterfall: Path
    coverage_by_target: Path
    coverage_by_split: Path
    coverage_by_ticker: Path
    coverage_by_model: Path
    report_markdown: Path
    empirical_report: Path
    factor_card: Path
    appendix_tables: Path
    report_summary: Path

    @classmethod
    def from_run_dir(
        cls,
        run_dir: str | Path,
        *,
        config_path: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> ReportArtifactPaths:
        base = Path(run_dir)
        output = Path(output_dir) if output_dir else base
        return cls(
            run_dir=base,
            config=Path(config_path) if config_path else base / "config_snapshot.yaml",
            run_status=base / "run_status.json",
            audit_report=base / "audit_report.json",
            evaluation_metrics=base / "evaluation_metrics.json",
            backtest_results=base / "backtest_results.json",
            delisting_application_report=base / "delisting_application_report.json",
            model_manifest=base / "model_manifest.json",
            tuning_log=base / "tuning_log.json",
            feature_manifest=base / "feature_manifest.json",
            vocabulary_manifest=base / "vocabulary_manifest.json",
            section_length_quality_report=base / "section_length_quality_report.json",
            parser_manual_review_appendix=base / "parser_manual_review_appendix.md",
            prediction_distribution_report=base / "prediction_distribution_report.json",
            feature_ablation_summary=base / "feature_ablation_summary.json",
            primary_rank_ic_bootstrap_report=(
                base / "primary_rank_ic_bootstrap_report.json"
            ),
            portfolio_metrics=base / "portfolio_metrics.json",
            monthly_portfolio_metrics=base / "monthly_portfolio_metrics.json",
            multiple_testing_report=base / "multiple_testing_report.json",
            specification_registry=base / "specification_registry.json",
            universe_quality_report=base / "universe_quality_report.json",
            coverage_waterfall=base / "coverage_waterfall.json",
            coverage_by_target=base / "coverage_by_target.csv",
            coverage_by_split=base / "coverage_by_split.csv",
            coverage_by_ticker=base / "coverage_by_ticker.csv",
            coverage_by_model=base / "coverage_by_model.csv",
            report_markdown=output / "report.md",
            empirical_report=output / "empirical_report.md",
            factor_card=output / "factor_card.md",
            appendix_tables=output / "appendix_tables.md",
            report_summary=output / "report_summary.json",
        )


@dataclass(frozen=True)
class ReportBuildResult:
    run_id: str
    report_markdown_path: Path
    empirical_report_path: Path
    factor_card_path: Path
    appendix_tables_path: Path
    report_summary_path: Path
    conclusion_level: str
    formal_result_allowed: bool
    generated_at_utc: datetime


def generate_run_report(
    *,
    run_id: str,
    run_dir: str | Path | None = None,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    allow_failed_audit: bool = False,
) -> ReportBuildResult:
    resolved_run_dir = Path(run_dir) if run_dir else Path("runs/text_factor_lab") / run_id
    paths = ReportArtifactPaths.from_run_dir(
        resolved_run_dir,
        config_path=config_path,
        output_dir=output_dir,
    )
    artifacts = _load_report_artifacts(paths)
    audit = artifacts["audit_report"]
    if audit.run_id != run_id:
        raise ValueError(
            f"audit run_id '{audit.run_id}' does not match requested run_id '{run_id}'"
        )
    if audit.audit_status == "fail" and not allow_failed_audit:
        raise ValueError(
            "audit_status=fail; report generation is blocked unless "
            "allow_failed_audit=True is set for a diagnostic report"
        )

    generated_at = datetime.now(UTC)
    summary = _build_summary(
        run_id=run_id,
        generated_at_utc=generated_at,
        artifacts=artifacts,
        paths=paths,
        allow_failed_audit=allow_failed_audit,
    )
    markdown = _render_markdown(summary)
    empirical_report = _render_empirical_report(summary)
    factor_card = _render_factor_card(summary)
    appendix_tables = _render_appendix_tables(summary)

    paths.report_markdown.parent.mkdir(parents=True, exist_ok=True)
    paths.report_markdown.write_text(markdown, encoding="utf-8")
    paths.empirical_report.write_text(empirical_report, encoding="utf-8")
    paths.factor_card.write_text(factor_card, encoding="utf-8")
    paths.appendix_tables.write_text(appendix_tables, encoding="utf-8")
    paths.report_summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _mark_run_reported(paths.run_status, audit)
    return ReportBuildResult(
        run_id=run_id,
        report_markdown_path=paths.report_markdown,
        empirical_report_path=paths.empirical_report,
        factor_card_path=paths.factor_card,
        appendix_tables_path=paths.appendix_tables,
        report_summary_path=paths.report_summary,
        conclusion_level=summary["conclusion_level"],
        formal_result_allowed=summary["formal_result_allowed"],
        generated_at_utc=generated_at,
    )


def _load_report_artifacts(paths: ReportArtifactPaths) -> dict[str, Any]:
    missing = [
        str(path)
        for path in [
            paths.config,
            paths.run_status,
            paths.audit_report,
            paths.evaluation_metrics,
            paths.backtest_results,
            paths.model_manifest,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("missing required report artifacts: " + ", ".join(missing))

    return {
        "config": load_experiment_config(paths.config),
        "config_payload": yaml.safe_load(paths.config.read_text(encoding="utf-8")),
        "run_status": RunStatusRecord.model_validate(_read_json_object(paths.run_status)),
        "audit_report": AuditReportRecord.model_validate(_read_json_object(paths.audit_report)),
        "evaluation_metrics": [
            EvaluationMetricRecord.model_validate(item)
            for item in _read_json_array(paths.evaluation_metrics)
        ],
        "backtest_results": [
            PortfolioBacktestRecord.model_validate(item)
            for item in _read_json_array(paths.backtest_results)
        ],
        "delisting_application_report": _read_optional_json_object(
            paths.delisting_application_report
        ),
        "model_manifest": [
            ModelManifestRecord.model_validate(item)
            for item in _read_json_array(paths.model_manifest)
        ],
        "tuning_log": [
            TuningLogRecord.model_validate(item)
            for item in _read_optional_json_array(paths.tuning_log)
        ],
        "feature_manifest": [
            FeatureManifestRecord.model_validate(item)
            for item in _read_optional_json_array(paths.feature_manifest)
        ],
        "vocabulary_manifest": _read_optional_json_array(paths.vocabulary_manifest),
        "section_length_quality_report": _read_optional_json_object(
            paths.section_length_quality_report
        ),
        "prediction_distribution_report": _read_optional_json_object(
            paths.prediction_distribution_report
        ),
        "feature_ablation_summary": _read_optional_json_object(
            paths.feature_ablation_summary
        ),
        "primary_rank_ic_bootstrap_report": _read_optional_json_object(
            paths.primary_rank_ic_bootstrap_report
        ),
        "portfolio_metrics": [
            PortfolioMetricRecord.model_validate(item)
            for item in _read_optional_json_array(paths.portfolio_metrics)
        ]
        + [
            PortfolioMetricRecord.model_validate(item)
            for item in _read_optional_json_array(paths.monthly_portfolio_metrics)
        ],
        "portfolio_return_sources": sorted(
            {
                item.get("return_source", "label_window")
                for item in (
                    _read_optional_jsonl_objects(paths.run_dir / "portfolio_returns.jsonl")
                    + _read_optional_jsonl_objects(
                        paths.run_dir / "monthly_portfolio_returns.jsonl"
                    )
                )
            }
        ),
        "portfolio_position_accounting": sorted(
            {
                item.get("position_accounting", "label_window")
                for item in (
                    _read_optional_jsonl_objects(paths.run_dir / "portfolio_returns.jsonl")
                    + _read_optional_jsonl_objects(
                        paths.run_dir / "monthly_portfolio_returns.jsonl"
                    )
                )
            }
        ),
        "multiple_testing_report": _read_optional_multiple_testing_report(
            paths.multiple_testing_report
        ),
        "specification_registry": _read_optional_json_object(paths.specification_registry),
        "universe_quality_report": _read_optional_json_object(paths.universe_quality_report),
        "coverage_waterfall": _read_optional_json_object(paths.coverage_waterfall),
        "coverage_tables": {
            "by_target": _read_optional_csv_rows(paths.coverage_by_target),
            "by_split": _read_optional_csv_rows(paths.coverage_by_split),
            "by_ticker": _read_optional_csv_rows(paths.coverage_by_ticker),
            "by_model": _read_optional_csv_rows(paths.coverage_by_model),
        },
        "data_license_manifest": _read_data_license_manifest(paths.config),
        "document_count": _count_jsonl_records(paths.run_dir / "document_manifest.jsonl"),
        "label_count": _count_jsonl_records(paths.run_dir / "labels.jsonl"),
        "prediction_count": _count_jsonl_records(paths.run_dir / "predictions.jsonl"),
        "feature_count": _count_jsonl_records(paths.run_dir / "features.jsonl"),
    }


def _build_summary(
    *,
    run_id: str,
    generated_at_utc: datetime,
    artifacts: dict[str, Any],
    paths: ReportArtifactPaths,
    allow_failed_audit: bool,
) -> dict[str, Any]:
    config = artifacts["config"]
    run_status: RunStatusRecord = artifacts["run_status"]
    audit: AuditReportRecord = artifacts["audit_report"]
    metrics: list[EvaluationMetricRecord] = artifacts["evaluation_metrics"]
    backtests: list[PortfolioBacktestRecord] = artifacts["backtest_results"]
    model_manifest: list[ModelManifestRecord] = artifacts["model_manifest"]
    feature_manifest: list[FeatureManifestRecord] = artifacts["feature_manifest"]
    tuning_log: list[TuningLogRecord] = artifacts["tuning_log"]
    portfolio_metrics: list[PortfolioMetricRecord] = artifacts["portfolio_metrics"]
    delisting_application_report = artifacts["delisting_application_report"] or {}
    data_license_manifest: DataLicenseManifestRecord | None = artifacts[
        "data_license_manifest"
    ]
    multiple_testing_report: MultipleTestingReportRecord | None = artifacts[
        "multiple_testing_report"
    ]
    specification_registry = artifacts["specification_registry"] or {}
    universe_quality_report = artifacts["universe_quality_report"] or {}
    coverage_waterfall = artifacts["coverage_waterfall"] or {}
    coverage_tables = artifacts["coverage_tables"]
    vocabulary_manifest = artifacts["vocabulary_manifest"]
    section_length_quality_report = artifacts["section_length_quality_report"] or {}
    prediction_distribution_report = artifacts["prediction_distribution_report"] or {}
    feature_ablation_summary = artifacts["feature_ablation_summary"] or {}
    primary_rank_ic_bootstrap_report = (
        artifacts["primary_rank_ic_bootstrap_report"] or {}
    )

    best_prediction = _best_prediction_metric(metrics)
    best_backtest = _best_backtest(backtests)
    failed_checks = [check for check in audit.checks if check.status == "fail"]
    warning_checks = [check for check in audit.checks if check.status == "warn"]
    conclusion_level = _conclusion_level(audit, metrics, backtests, allow_failed_audit)
    formal_result_blockers = _formal_result_blockers(
        audit=audit,
        config=config,
        universe_quality_report=universe_quality_report,
    )

    return {
        "report_version": REPORT_VERSION,
        "run_id": run_id,
        "run_type": config.run.run_type,
        "generated_at_utc": generated_at_utc.isoformat(),
        "conclusion_level": conclusion_level,
        "formal_result_allowed": audit.formal_result_allowed and audit.audit_status == "pass",
        "formal_result_blockers": formal_result_blockers,
        "audit": {
            "status": audit.audit_status,
            "coverage": audit.coverage,
            "coverage_diagnosis": _coverage_diagnosis_summary(
                coverage_waterfall,
                coverage_tables,
            ),
            "check_count": audit.check_count,
            "fail_count": audit.fail_count,
            "warn_count": audit.warn_count,
            "failed_checks": [_check_summary(check) for check in failed_checks],
            "warning_checks": [_check_summary(check) for check in warning_checks],
        },
        "sample": {
            "universe": config.universe.name,
            "selection_date": config.universe.selection_date.isoformat(),
            "sample_start": config.sample.start_date.isoformat(),
            "sample_end": config.sample.end_date.isoformat(),
            "timezone": config.sample.timezone,
            "document_type": config.text_source.document_type,
            "text_source": config.text_source.source,
            "sections": config.text_source.sections,
            "document_count": artifacts["document_count"],
            "label_count": artifacts["label_count"],
            "prediction_count": artifacts["prediction_count"],
            "feature_count": artifacts["feature_count"],
        },
        "data_provider": {
            "market_data_provider": config.data_provider.market_data_provider,
            "filing_provider": config.data_provider.filing_provider,
            "price_source": config.data_provider.price_source,
            "return_source": config.data_provider.return_source,
            "delisting_return_source": config.data_provider.delisting_return_source,
            "link_source": config.data_provider.link_source,
            "allow_public_yahoo_fallback": config.data_provider.allow_public_yahoo_fallback,
            "license_manifest_available": data_license_manifest is not None,
            "license_manifest": (
                {
                    "data_stack": data_license_manifest.data_stack,
                    "license_note": data_license_manifest.license_note,
                    "raw_data_committed": data_license_manifest.raw_data_committed,
                    "data_rights_scope": data_license_manifest.data_rights_scope,
                    "permitted_public_outputs": (
                        data_license_manifest.permitted_public_outputs
                    ),
                }
                if data_license_manifest is not None
                else None
            ),
        },
        "labels": {
            "targets": config.labels.targets,
            "return_type": config.labels.return_type,
            "portfolio_return_type": config.labels.portfolio_return_type,
            "market_benchmark": config.labels.market_benchmark,
            "annualization_days": config.labels.annualization_days,
        },
        "features": {
            "methods": config.features.methods,
            "feature_manifest_count": len(feature_manifest),
            "feature_versions": sorted({record.feature_version for record in feature_manifest}),
            "text_scopes": sorted({record.text_scope for record in feature_manifest}),
            "vocabulary_manifest_count": len(vocabulary_manifest),
            "vocabulary_manifest_sample": vocabulary_manifest[:6],
        },
        "models": {
            "enabled": config.models.enabled,
            "manifest_count": len(model_manifest),
            "model_ids": sorted({record.model_id for record in model_manifest}),
            "families": sorted({record.model_family for record in model_manifest}),
            "tuning_log_count": len(tuning_log),
            "selection_metric": config.models.tuning.selection_metric,
        },
        "evaluation": {
            "metric_count": len(metrics),
            "best_prediction_metric": _metric_summary(best_prediction) if best_prediction else None,
            "test_metrics": [_metric_summary(metric) for metric in _top_test_metrics(metrics)],
            "feature_ablation": feature_ablation_summary,
            "primary_rank_ic_bootstrap": primary_rank_ic_bootstrap_report,
        },
        "backtest": {
            "result_count": len(backtests),
            "portfolio_metric_count": len(portfolio_metrics),
            "portfolio_return_sources": artifacts["portfolio_return_sources"],
            "portfolio_position_accounting": artifacts["portfolio_position_accounting"],
            "portfolio_method": config.backtest.portfolio_method,
            "weighting": config.backtest.weighting,
            "transaction_cost_bps_one_way": config.backtest.transaction_cost_bps_one_way,
            "newey_west_lag": config.backtest.newey_west_lag,
            "best_backtest": _backtest_summary(best_backtest) if best_backtest else None,
            "top_backtests": [_backtest_summary(record) for record in _top_backtests(backtests)],
            "portfolio_metrics": [
                _portfolio_metric_summary(record)
                for record in _top_portfolio_metrics(portfolio_metrics)
            ],
            "delisting_application_report": delisting_application_report,
        },
        "multiple_testing": _multiple_testing_summary(multiple_testing_report),
        "specification_registry": {
            "available": bool(specification_registry),
            "registry_version": specification_registry.get("registry_version"),
            "registry_designation": specification_registry.get("registry_designation"),
            "preregistration": specification_registry.get("preregistration", {}),
            "preregistered_primary_rules": specification_registry.get(
                "preregistered_primary_rules",
                [],
            ),
            "role_counts": specification_registry.get("role_counts", {}),
            "primary_specifications": specification_registry.get(
                "primary_specifications",
                [],
            ),
            "signal_direction_policy": _primary_signal_direction_policy(
                specification_registry.get("primary_specifications", [])
            ),
        },
        "quality_diagnostics": {
            "section_length": {
                "available": bool(section_length_quality_report),
                "section_count": section_length_quality_report.get("section_count", 0),
                "flag_counts": section_length_quality_report.get("flag_counts", {}),
                "section_level_feature_exclusion_count": (
                    section_length_quality_report.get(
                        "section_level_feature_exclusion_count",
                        0,
                    )
                ),
                "rules": section_length_quality_report.get("rules", {}),
                "manual_review_appendix_path": str(
                    paths.parser_manual_review_appendix
                ),
            },
            "prediction_distribution": {
                "available": bool(prediction_distribution_report),
                "ranking_policy": prediction_distribution_report.get("ranking_policy"),
                "outlier_rule": prediction_distribution_report.get("outlier_rule"),
                "prediction_scale_guard": prediction_distribution_report.get(
                    "prediction_scale_guard",
                    {},
                ),
                "top_outlier_rows": _top_prediction_outlier_rows(
                    prediction_distribution_report.get("rows", [])
                ),
            },
        },
        "interpretation": _interpretation_policy(
            audit=audit,
            best_prediction=best_prediction,
            best_backtest=best_backtest,
            multiple_testing_report=multiple_testing_report,
            allow_failed_audit=allow_failed_audit,
        ),
        "reproducibility": {
            "config_path": str(paths.config),
            "git_commit_sha": run_status.git_commit_sha,
            "package_version": run_status.package_version,
            "dirty_worktree_flag": run_status.dirty_worktree_flag,
            "report_markdown_path": str(paths.report_markdown),
            "empirical_report_path": str(paths.empirical_report),
            "factor_card_path": str(paths.factor_card),
            "appendix_tables_path": str(paths.appendix_tables),
            "parser_manual_review_appendix_path": str(
                paths.parser_manual_review_appendix
            ),
            "feature_ablation_summary_path": str(paths.feature_ablation_summary),
            "primary_rank_ic_bootstrap_report_path": str(
                paths.primary_rank_ic_bootstrap_report
            ),
            "report_summary_path": str(paths.report_summary),
            "commands": [
                f"python -m text_factor_lab audit --run-id {run_id} --run-dir {paths.run_dir}",
                f"python -m text_factor_lab report --run-id {run_id} --run-dir {paths.run_dir}",
            ],
        },
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Text Factor Research Report - {summary['run_id']}",
        "",
        "## Executive Summary",
        "",
        f"- Run type: `{summary['run_type']}`.",
        f"- Conclusion level: `{summary['conclusion_level']}`.",
        f"- Formal result allowed: `{summary['formal_result_allowed']}`.",
        _formal_result_blocker_section(summary["formal_result_blockers"]),
        (
            "- Audit: "
            f"`{summary['audit']['status']}` with coverage "
            f"{summary['audit']['coverage']:.3f}, "
            f"{summary['audit']['fail_count']} failures, "
            f"{summary['audit']['warn_count']} warnings."
        ),
        "",
        "## Research Question",
        "",
        (
            "Estimate whether audited 10-K text features predict future volatility, "
            "abnormal return, or related factor targets under a leakage-controlled "
            "rolling-split workflow."
        ),
        "",
        "## Data And Sample",
        "",
        f"- Universe: `{summary['sample']['universe']}`.",
        f"- Selection date: `{summary['sample']['selection_date']}`.",
        (
            f"- Sample window: `{summary['sample']['sample_start']}` "
            f"to `{summary['sample']['sample_end']}`."
        ),
        f"- Timezone: `{summary['sample']['timezone']}`.",
        (
            f"- Document type/source: `{summary['sample']['document_type']}` / "
            f"`{summary['sample']['text_source']}`."
        ),
        f"- Sections: {', '.join(f'`{section}`' for section in summary['sample']['sections'])}.",
        f"- Documents: {summary['sample']['document_count']}.",
        f"- Labels: {summary['sample']['label_count']}.",
        f"- Predictions: {summary['sample']['prediction_count']}.",
        "",
        "## Licensed Data Stack",
        "",
        _licensed_data_stack_section(summary["data_provider"]),
        "",
        "## Coverage And Audit Diagnosis",
        "",
        _coverage_diagnosis_section(summary["audit"]["coverage_diagnosis"]),
        "",
        "## Label Construction",
        "",
        f"- Targets: {', '.join(f'`{target}`' for target in summary['labels']['targets'])}.",
        f"- Return type: `{summary['labels']['return_type']}`.",
        f"- Portfolio return type: `{summary['labels']['portfolio_return_type']}`.",
        f"- Benchmark: `{summary['labels']['market_benchmark']}`.",
        f"- Annualization days: {summary['labels']['annualization_days']}.",
        "",
        "## Feature Construction",
        "",
        f"- Methods: {', '.join(f'`{method}`' for method in summary['features']['methods'])}.",
        f"- Feature records: {summary['sample']['feature_count']}.",
        f"- Feature manifests: {summary['features']['feature_manifest_count']}.",
        f"- Feature versions: {_inline_list(summary['features']['feature_versions'])}.",
        f"- Text scopes: {_inline_list(summary['features']['text_scopes'])}.",
        f"- Vocabulary manifest rows: {summary['features']['vocabulary_manifest_count']}.",
        "",
        _vocabulary_manifest_section(summary["features"]["vocabulary_manifest_sample"]),
        "",
        "## Parser Section Length Quality",
        "",
        _section_length_quality_section(summary["quality_diagnostics"]["section_length"]),
        "",
        "## Model Setup",
        "",
        f"- Configured models: {_inline_list(summary['models']['enabled'])}.",
        f"- Trained model manifests: {summary['models']['manifest_count']}.",
        f"- Model families: {_inline_list(summary['models']['families'])}.",
        f"- Tuning logs: {summary['models']['tuning_log_count']}.",
        f"- Selection metric: `{summary['models']['selection_metric']}`.",
        "",
        "## Out-Of-Sample Prediction Results",
        "",
        _primary_signal_policy_section(
            summary["specification_registry"]["signal_direction_policy"]
        ),
        "",
        _metrics_table(summary["evaluation"]["test_metrics"]),
        "",
        _ranking_objective_section(summary["evaluation"]["test_metrics"]),
        "",
        "## Industry-Neutral Incremental Signal",
        "",
        _industry_neutral_interpretation(summary["evaluation"]["test_metrics"]),
        "",
        "## Feature Ablation",
        "",
        _feature_ablation_table(summary["evaluation"]["feature_ablation"]),
        "",
        "## Primary Rank IC Bootstrap",
        "",
        _bootstrap_table(summary["evaluation"]["primary_rank_ic_bootstrap"]),
        "",
        "## Prediction Distribution Diagnostics",
        "",
        _prediction_distribution_section(
            summary["quality_diagnostics"]["prediction_distribution"]
        ),
        "",
        "## Factor Backtest",
        "",
        (
            "Portfolio results are diagnostic only in the current applied-grade run; "
            "the evidence supports exploratory prediction signals, not formal trading alpha."
        ),
        "",
        f"- Portfolio method: `{summary['backtest']['portfolio_method']}`.",
        f"- Weighting: `{summary['backtest']['weighting']}`.",
        f"- One-way transaction cost: {summary['backtest']['transaction_cost_bps_one_way']} bps.",
        f"- Newey-West lag: {summary['backtest']['newey_west_lag']}.",
        (
            "- Portfolio ranking uses `factor_score` ordering to form ranks and "
            "tie-aware quantiles. Tied boundary groups are never split, and a "
            "constant-score cross-section does not form a long-short portfolio."
        ),
        "",
        _backtest_table(summary["backtest"]["top_backtests"]),
        "",
        "## Delisting Return Handling",
        "",
        _delisting_report_section(summary["backtest"]["delisting_application_report"]),
        "",
        "## Multiple Testing Adjustment",
        "",
        _multiple_testing_section(summary["multiple_testing"]),
        "",
        "## Specification Registry",
        "",
        _specification_registry_section(summary["specification_registry"]),
        "",
        "## Robustness Checks",
        "",
        (
            "- Current MVP report summarizes split-level and `ALL_SPLITS` metrics. "
            "Subperiod stability, Deflated Sharpe, CPCV/PBO, borrow costs, and capacity "
            "diagnostics should be added before making production research claims."
        ),
        "",
        "## Leakage Audit",
        "",
        _audit_table(summary["audit"]["failed_checks"], summary["audit"]["warning_checks"]),
        "",
        "## Failure Cases",
        "",
        _failure_section(summary["audit"]),
        "",
        "## Conclusion Level",
        "",
        _conclusion_text(summary),
        "",
        "## Reproducible Commands",
        "",
        f"- Git commit SHA: `{summary['reproducibility'].get('git_commit_sha')}`.",
        f"- Package version: `{summary['reproducibility'].get('package_version')}`.",
        f"- Dirty worktree flag: `{summary['reproducibility'].get('dirty_worktree_flag')}`.",
        "",
        "```bash",
        *summary["reproducibility"]["commands"],
        "```",
        "",
        f"Generated at `{summary['generated_at_utc']}` by `{summary['report_version']}`.",
        "",
    ]
    return "\n".join(lines)


def _render_empirical_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# Empirical Report - {summary['run_id']}",
        "",
        "## 1. Research Design",
        "",
        (
            "This experiment evaluates whether SEC 10-K text features contain "
            "out-of-sample information about configured return or volatility targets. "
            "The workflow uses rolling splits, validation-only model selection, "
            "artifact-level audit checks, and multiple-testing disclosure."
        ),
        "",
        "## 2. Data And Universe Construction",
        "",
        f"- Universe: `{summary['sample']['universe']}`.",
        f"- Selection date: `{summary['sample']['selection_date']}`.",
        (
            f"- Sample window: `{summary['sample']['sample_start']}` to "
            f"`{summary['sample']['sample_end']}`."
        ),
        f"- Documents: {summary['sample']['document_count']}.",
        f"- Labels: {summary['sample']['label_count']}.",
        "",
        "## 2.1 Licensed Data Stack",
        "",
        _licensed_data_stack_section(summary["data_provider"]),
        "",
        "## 2.2 Formal Result Boundary",
        "",
        _formal_result_blocker_section(summary["formal_result_blockers"]),
        "",
        "## 2.3 Coverage And Audit Diagnosis",
        "",
        _coverage_diagnosis_section(summary["audit"]["coverage_diagnosis"]),
        "",
        "## 3. Event-Time Alignment",
        "",
        (
            f"The configured timezone is `{summary['sample']['timezone']}`. "
            "Document availability and prediction timestamps are audited before "
            "formal conclusions are allowed."
        ),
        "",
        "## 4. Text Feature Construction",
        "",
        f"- Methods: {_inline_list(summary['features']['methods'])}.",
        f"- Text scopes: {_inline_list(summary['features']['text_scopes'])}.",
        f"- Feature records: {summary['sample']['feature_count']}.",
        "",
        "## 5. Label Construction",
        "",
        f"- Targets: {_inline_list(summary['labels']['targets'])}.",
        f"- Return type: `{summary['labels']['return_type']}`.",
        f"- Benchmark: `{summary['labels']['market_benchmark']}`.",
        "",
        "## 6. Prediction Models",
        "",
        f"- Models: {_inline_list(summary['models']['enabled'])}.",
        f"- Selection metric: `{summary['models']['selection_metric']}`.",
        f"- Tuning logs: {summary['models']['tuning_log_count']}.",
        "",
        "## 7. Out-Of-Sample Forecasting Results",
        "",
        _metrics_table(summary["evaluation"]["test_metrics"]),
        "",
        _ranking_objective_section(summary["evaluation"]["test_metrics"]),
        "",
        "## 7.1 Industry-Neutral Incremental Signal",
        "",
        _industry_neutral_interpretation(summary["evaluation"]["test_metrics"]),
        "",
        "## 7.2 Feature Ablation",
        "",
        _feature_ablation_table(summary["evaluation"]["feature_ablation"]),
        "",
        "## 7.3 Bootstrap Confidence Intervals",
        "",
        _bootstrap_table(summary["evaluation"]["primary_rank_ic_bootstrap"]),
        "",
        "## 8. Portfolio Construction",
        "",
        (
            f"The backtest uses `{summary['backtest']['portfolio_method']}` with "
            f"`{summary['backtest']['weighting']}` weighting in the configured summary "
            "backtest. Portfolio variant diagnostics are reported when available. "
            "These portfolio outputs are diagnostic only and should not be presented as "
            "formal trading-alpha evidence. "
            "Portfolio return sources: "
            f"{_inline_list(summary['backtest']['portfolio_return_sources'])}. "
            "Position accounting: "
            f"{_inline_list(summary['backtest']['portfolio_position_accounting'])}."
        ),
        "",
        "## 9. Factor Backtest Results",
        "",
        _backtest_table(summary["backtest"]["top_backtests"]),
        "",
        "## 10. Sector-Neutral And Value-Weighted Robustness",
        "",
        _portfolio_metric_table(summary["backtest"]["portfolio_metrics"]),
        "",
        "## 11. Delisting Return Handling",
        "",
        _delisting_report_section(summary["backtest"]["delisting_application_report"]),
        "",
        "## 12. Multiple Testing Adjustment",
        "",
        _multiple_testing_section(summary["multiple_testing"]),
        "",
        "## 13. Specification Registry",
        "",
        _specification_registry_section(summary["specification_registry"]),
        "",
        "## 14. Failure Cases And Audit Results",
        "",
        _audit_table(summary["audit"]["failed_checks"], summary["audit"]["warning_checks"]),
        "",
        "## 15. Economic Interpretation",
        "",
        summary["interpretation"]["economic_interpretation"],
        "",
        "## 16. Limitations",
        "",
        _limitations_text(summary),
        "",
        "## 17. Conclusion",
        "",
        summary["interpretation"]["conclusion_text"],
        "",
    ]
    return "\n".join(lines)


def _render_factor_card(summary: dict[str, Any]) -> str:
    best_metric = summary["evaluation"]["best_prediction_metric"]
    signal_policy = summary["specification_registry"]["signal_direction_policy"]
    lines = [
        f"# Factor Card - {summary['run_id']}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Conclusion | `{summary['conclusion_level']}` |",
        f"| Formal result allowed | `{summary['formal_result_allowed']}` |",
        f"| Formal result blockers | {_inline_list(summary['formal_result_blockers'])} |",
        f"| Audit status | `{summary['audit']['status']}` |",
        f"| Coverage | `{summary['audit']['coverage']:.3f}` |",
        (
            "| Eligible OOS coverage | "
            f"`{_fmt(summary['audit']['coverage_diagnosis']['eligible_oos_coverage'])}` |"
        ),
        (
            "| Primary spec coverage | "
            f"`{_fmt(summary['audit']['coverage_diagnosis']['primary_spec_coverage'])}` |"
        ),
        (
            "| Primary prediction coverage | "
            f"`{_fmt(summary['audit']['coverage_diagnosis']['primary_prediction_coverage'])}` |"
        ),
        (
            "| Primary portfolio coverage | "
            f"`{_fmt(summary['audit']['coverage_diagnosis']['primary_portfolio_coverage'])}` |"
        ),
        (
            "| Signal direction policy | "
            f"`{signal_policy['policy']}` |"
        ),
        (
            "| Primary prediction sign | "
            f"`{signal_policy['primary_prediction_sign']}` |"
        ),
        f"| Universe | `{summary['sample']['universe']}` |",
        f"| Sample | `{summary['sample']['sample_start']}..{summary['sample']['sample_end']}` |",
        f"| Targets | {_inline_list(summary['labels']['targets'])} |",
        f"| Features | {_inline_list(summary['features']['methods'])} |",
        f"| Models | {_inline_list(summary['models']['enabled'])} |",
        f"| Multiple-testing families | `{summary['multiple_testing']['family_count']}` |",
        f"| Git commit SHA | `{summary['reproducibility'].get('git_commit_sha')}` |",
        f"| Package version | `{summary['reproducibility'].get('package_version')}` |",
        f"| Dirty worktree flag | `{summary['reproducibility'].get('dirty_worktree_flag')}` |",
        (
            "| Portfolio return sources | "
            f"{_inline_list(summary['backtest']['portfolio_return_sources'])} |"
        ),
        (
            "| Position accounting | "
            f"{_inline_list(summary['backtest']['portfolio_position_accounting'])} |"
        ),
        "",
        "## Best Observed Exploratory Ranking Result",
        "",
        _single_metric_block(best_metric),
        "",
        _ranking_objective_section(summary["evaluation"]["test_metrics"]),
        "",
        "## Incremental Text Diagnostics",
        "",
        _industry_neutral_interpretation(summary["evaluation"]["test_metrics"]),
        "",
        _feature_ablation_table(summary["evaluation"]["feature_ablation"]),
        "",
        "## Primary Rank IC Confidence Intervals",
        "",
        _bootstrap_table(summary["evaluation"]["primary_rank_ic_bootstrap"]),
        "",
        "## Preregistered Portfolio Result",
        "",
        _primary_portfolio_block(summary["specification_registry"]),
        "",
        (
            "Some split-level portfolio diagnostics may show high Sharpe ratios, but "
            "they are not the preregistered primary test and can remain statistically "
            "weak after Newey-West adjustment."
        ),
        "",
        "## Evidence Level",
        "",
        summary["interpretation"]["evidence_level"],
        "",
        "## Primary Sign Convention",
        "",
        signal_policy["explanation"],
        "",
        "## Diagnostics",
        "",
        (
            "- Vocabulary manifest rows: "
            f"`{summary['features']['vocabulary_manifest_count']}`."
        ),
        (
            "- Section length flags: "
            f"`{summary['quality_diagnostics']['section_length']['flag_counts']}`."
        ),
        (
            "- Section-level feature exclusions: "
            f"`{_section_exclusion_count(summary)}`."
        ),
        (
            "- Prediction ranking policy: "
            f"{summary['quality_diagnostics']['prediction_distribution']['ranking_policy']}"
        ),
        (
            "- Portfolio interpretation: diagnostic only; current evidence does not "
            "establish formal trading alpha."
        ),
        "",
        "## Usage Boundary",
        "",
        _formal_result_blocker_section(summary["formal_result_blockers"]),
        "",
        summary["interpretation"]["usage_boundary"],
        "",
    ]
    return "\n".join(lines)


def _render_appendix_tables(summary: dict[str, Any]) -> str:
    lines = [
        f"# Appendix Tables - {summary['run_id']}",
        "",
        "## Table 1 Sample Coverage",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| Documents | {summary['sample']['document_count']} |",
        f"| Labels | {summary['sample']['label_count']} |",
        f"| Predictions | {summary['sample']['prediction_count']} |",
        f"| Features | {summary['sample']['feature_count']} |",
        "",
        "## Table 1B Coverage Waterfall",
        "",
        _coverage_diagnosis_section(summary["audit"]["coverage_diagnosis"]),
        "",
        "## Table 2 Feature Summary",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Methods | {_inline_list(summary['features']['methods'])} |",
        f"| Versions | {_inline_list(summary['features']['feature_versions'])} |",
        f"| Text scopes | {_inline_list(summary['features']['text_scopes'])} |",
        "",
        "## Table 3 OOS Prediction Metrics",
        "",
        _metrics_table(summary["evaluation"]["test_metrics"]),
        "",
        "## Table 3B Industry-Neutral And Feature-Ablation Results",
        "",
        _feature_ablation_table(summary["evaluation"]["feature_ablation"]),
        "",
        "## Table 3C Primary Rank IC Bootstrap Confidence Intervals",
        "",
        _bootstrap_table(summary["evaluation"]["primary_rank_ic_bootstrap"]),
        "",
        "## Table 4 Portfolio Return Summary",
        "",
        _backtest_table(summary["backtest"]["top_backtests"]),
        "",
        "## Table 5 Portfolio Variant Metrics",
        "",
        _portfolio_metric_table(summary["backtest"]["portfolio_metrics"]),
        "",
        "## Table 6 Multiple-Testing-Adjusted Results",
        "",
        _multiple_testing_section(summary["multiple_testing"]),
        "",
        "## Table 7 Primary Specification Registry",
        "",
        _specification_registry_section(summary["specification_registry"]),
        "",
        "## Table 8 Audit Checks",
        "",
        _audit_table(summary["audit"]["failed_checks"], summary["audit"]["warning_checks"]),
        "",
    ]
    return "\n".join(lines)


def _vocabulary_manifest_section(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No vocabulary manifest artifact was available."
    lines = [
        "| Split | Scope | Fit Scope | Vocabulary Size | Hash | Sample Terms |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows[:8]:
        sample = ", ".join(f"`{term}`" for term in row.get("top_terms_sample", [])[:8])
        lines.append(
            "| "
            f"`{row.get('split_id')}` | "
            f"`{row.get('text_scope')}` | "
            f"`{row.get('fit_scope')}` | "
            f"{row.get('vocabulary_size')} | "
            f"`{str(row.get('vocabulary_hash', ''))[:12]}` | "
            f"{sample} |"
        )
    return "\n".join(lines)


def _section_length_quality_section(summary: dict[str, Any]) -> str:
    if not summary.get("available"):
        return "No section length quality artifact was available."
    return "\n".join(
        [
            f"- Section rows checked: `{summary.get('section_count', 0)}`.",
            f"- Flag counts: `{summary.get('flag_counts', {})}`.",
            (
                "- Section-level feature exclusions: "
                f"`{summary.get('section_level_feature_exclusion_count', 0)}`."
            ),
            (
                "- Core section rule: `item_1a` / `item_7` below 500 words is a "
                "warning; below 100 words requires manual review."
            ),
            (
                "- Feature policy: `item_1a` / `item_7` sections below 100 words "
                "are excluded from section-level features until manually reviewed; "
                "other text scopes remain available."
            ),
            (
                "- Manual-review appendix: "
                f"`{summary.get('manual_review_appendix_path')}`."
            ),
        ]
    )


def _section_exclusion_count(summary: dict[str, Any]) -> int:
    return int(
        summary["quality_diagnostics"]["section_length"].get(
            "section_level_feature_exclusion_count",
            0,
        )
    )


def _primary_signal_policy_section(policy: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- Signal direction policy: `{policy.get('policy')}`.",
            f"- Primary prediction sign: `{policy.get('primary_prediction_sign')}`.",
            f"- Explanation: {policy.get('explanation')}",
        ]
    )


def _prediction_distribution_section(summary: dict[str, Any]) -> str:
    if not summary.get("available"):
        return "No prediction distribution artifact was available."
    lines = [
        f"- Ranking policy: {summary.get('ranking_policy')}",
        f"- Outlier rule: {summary.get('outlier_rule')}",
        (
            "- Prediction scale guard: "
            f"{summary.get('prediction_scale_guard', {}).get('warning_row_count', 0)} "
            "model/target/role rows exceed warning thresholds."
        ),
        (
            "- Scale guard policy: "
            f"{summary.get('prediction_scale_guard', {}).get('policy')}"
        ),
        "",
        "| Model | Target | Role | N | Scale Ratio | Guard | Outliers | "
        "Prediction Range | Target Range |",
        "| --- | --- | --- | ---: | ---: | --- | ---: | --- | --- |",
    ]
    for row in summary.get("top_outlier_rows", [])[:10]:
        lines.append(
            "| "
            f"`{row.get('model_name')}` | "
            f"`{row.get('target_name')}` | "
            f"`{row.get('role')}` | "
            f"{row.get('observation_count')} | "
            f"{_fmt(row.get('scale_ratio'))} | "
            f"`{row.get('prediction_scale_guard_status')}` | "
            f"{row.get('outlier_count')} | "
            f"[{_fmt(row.get('prediction_min'))}, {_fmt(row.get('prediction_max'))}] | "
            f"[{_fmt(row.get('target_min'))}, {_fmt(row.get('target_max'))}] |"
        )
    return "\n".join(lines)


def _best_prediction_metric(
    metrics: list[EvaluationMetricRecord],
) -> EvaluationMetricRecord | None:
    candidates = [metric for metric in metrics if metric.role == "test"]
    if not candidates:
        return None
    aggregate = [metric for metric in candidates if metric.split_id == "ALL_SPLITS"]
    pool = aggregate or candidates
    return sorted(pool, key=lambda item: (-item.rank_ic, item.rmse, item.model_id))[0]


def _top_test_metrics(
    metrics: list[EvaluationMetricRecord],
    limit: int = 10,
) -> list[EvaluationMetricRecord]:
    candidates = [metric for metric in metrics if metric.role == "test"]
    aggregate = [metric for metric in candidates if metric.split_id == "ALL_SPLITS"]
    pool = aggregate or candidates
    return sorted(pool, key=lambda item: (-item.rank_ic, item.rmse, item.model_id))[:limit]


def _best_backtest(backtests: list[PortfolioBacktestRecord]) -> PortfolioBacktestRecord | None:
    eligible = [
        record
        for record in backtests
        if record.model_id.split("::", 1)[0] != "historical_mean"
    ]
    if not eligible:
        return None
    return sorted(eligible, key=lambda item: (-item.net_long_short_return, item.model_id))[0]


def _top_backtests(
    backtests: list[PortfolioBacktestRecord],
    limit: int = 10,
) -> list[PortfolioBacktestRecord]:
    eligible = [
        record
        for record in backtests
        if record.model_id.split("::", 1)[0] != "historical_mean"
    ]
    return sorted(eligible, key=lambda item: (-item.net_long_short_return, item.model_id))[:limit]


def _top_portfolio_metrics(
    records: list[PortfolioMetricRecord],
    limit: int = 12,
) -> list[PortfolioMetricRecord]:
    eligible = [
        record
        for record in records
        if record.model_id.split("::", 1)[0] != "historical_mean"
    ]
    return sorted(eligible, key=lambda item: (-item.sharpe_ratio, item.model_id))[:limit]


def _conclusion_level(
    audit: AuditReportRecord,
    metrics: list[EvaluationMetricRecord],
    backtests: list[PortfolioBacktestRecord],
    allow_failed_audit: bool,
) -> str:
    if audit.audit_status == "fail":
        return "diagnostic_only" if allow_failed_audit else "blocked"
    if not metrics:
        return "incomplete_no_metrics"
    if not backtests:
        return "prediction_only_no_backtest"
    if audit.formal_result_allowed and audit.audit_status == "pass":
        return "formal_report_allowed"
    return "exploratory_report"


def _formal_result_blockers(
    *,
    audit: AuditReportRecord,
    config: Any,
    universe_quality_report: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if config.run.run_type != "formal_run":
        blockers.append(
            "run_type is exploratory_run, so the run is intentionally not eligible "
            "for a formal empirical result."
        )
    price_source = str(config.data_provider.price_source).lower()
    return_source = str(config.data_provider.return_source).lower()
    if (
        "mixed" in price_source
        or "yahoo" in price_source
        or "mixed" in return_source
        or "yahoo" in return_source
        or config.data_provider.allow_public_yahoo_fallback
    ):
        blockers.append(
            "market data uses a mixed FMP/Yahoo public-source stack, not a single "
            "CRSP/WRDS-equivalent research-grade source."
        )
    estimated_market_cap_rows = int(
        universe_quality_report.get("membership_estimated_market_cap_rows")
        or universe_quality_report.get("estimated_market_cap_rows")
        or 0
    )
    if estimated_market_cap_rows > 0:
        blockers.append(
            "market_cap_at_selection is based on applied-grade estimates rather "
            "than licensed CRSP/Compustat/WRDS market-cap history."
        )
    if not universe_quality_report.get("is_research_grade", False):
        blockers.append(
            "the universe is an applied fixed-company panel, not a survivorship-free "
            "CRSP/WRDS research-grade universe."
        )
    if audit.audit_status != "pass":
        blockers.append(
            f"audit_status is {audit.audit_status}; warnings are boundary disclosures, "
            "not pipeline failures."
        )
    return list(dict.fromkeys(blockers))


def _metric_summary(metric: EvaluationMetricRecord) -> dict[str, Any]:
    return {
        "model_id": metric.model_id,
        "split_id": metric.split_id,
        "target_name": metric.target_name,
        "role": metric.role,
        "observation_count": metric.observation_count,
        "rmse": metric.rmse,
        "mae": metric.mae,
        "r_squared": metric.r_squared,
        "directional_accuracy": metric.directional_accuracy,
        "pearson_ic": metric.pearson_ic,
        "rank_ic": metric.rank_ic,
        "aggregation_method": metric.aggregation_method,
        "split_count": metric.split_count,
        "ic_grouping": metric.ic_grouping,
        "ic_observation_count": metric.ic_observation_count,
        "pearson_ic_t_stat": metric.pearson_ic_t_stat,
        "rank_ic_t_stat": metric.rank_ic_t_stat,
        "pearson_ic_newey_west_t_stat": metric.pearson_ic_newey_west_t_stat,
        "rank_ic_newey_west_t_stat": metric.rank_ic_newey_west_t_stat,
        "industry_neutral_rank_ic": metric.industry_neutral_rank_ic,
        "industry_neutral_rank_ic_t_stat": metric.industry_neutral_rank_ic_t_stat,
        "industry_neutral_rank_ic_newey_west_t_stat": (
            metric.industry_neutral_rank_ic_newey_west_t_stat
        ),
        "industry_neutral_ic_observation_count": (
            metric.industry_neutral_ic_observation_count
        ),
        "industry_neutral_group_count": metric.industry_neutral_group_count,
        "industry_neutral_singleton_group_count": (
            metric.industry_neutral_singleton_group_count
        ),
        "industry_neutral_method": metric.industry_neutral_method,
    }


def _backtest_summary(record: PortfolioBacktestRecord) -> dict[str, Any]:
    return {
        "model_id": record.model_id,
        "split_id": record.split_id,
        "target_name": record.target_name,
        "long_count": record.long_count,
        "short_count": record.short_count,
        "gross_long_short_return": record.gross_long_short_return,
        "net_long_short_return": record.net_long_short_return,
        "sharpe_ratio": record.sharpe_ratio,
        "newey_west_t_stat": record.newey_west_t_stat,
        "signal_direction": record.signal_direction,
        "target_aware_policy": record.target_aware_policy,
        "turnover": record.turnover,
    }


def _portfolio_metric_summary(record: PortfolioMetricRecord) -> dict[str, Any]:
    return {
        "model_id": record.model_id,
        "split_id": record.split_id,
        "target_name": record.target_name,
        "portfolio_variant": record.portfolio_variant,
        "weighting": record.weighting,
        "signal_direction": record.signal_direction,
        "target_aware_policy": record.target_aware_policy,
        "sector_neutral": record.sector_neutral,
        "observation_count": record.observation_count,
        "cumulative_return": record.cumulative_return,
        "annualized_return": record.annualized_return,
        "annualized_volatility": record.annualized_volatility,
        "sharpe_ratio": record.sharpe_ratio,
        "mean_period_return": record.mean_period_return,
        "period_return_t_stat": record.period_return_t_stat,
        "newey_west_lag": record.newey_west_lag,
        "newey_west_t_stat": record.newey_west_t_stat,
        "max_drawdown": record.max_drawdown,
        "hit_rate": record.hit_rate,
        "average_turnover": record.average_turnover,
        "average_gross_exposure": record.average_gross_exposure,
        "average_net_exposure": record.average_net_exposure,
    }


def _multiple_testing_summary(
    report: MultipleTestingReportRecord | None,
) -> dict[str, Any]:
    if report is None:
        return {
            "available": False,
            "specification_count": 0,
            "primary_specification_count": 0,
            "robustness_specification_count": 0,
            "exploratory_specification_count": 0,
            "p_value_count": 0,
            "family_count": 0,
            "role_family_counts": {},
            "primary_discoveries_at_5pct": 0,
            "primary_discoveries_at_10pct": 0,
            "robustness_discoveries_at_10pct": 0,
            "exploratory_discoveries_at_10pct": 0,
            "families": [],
        }
    return {
        "available": True,
        "specification_count": report.specification_count,
        "primary_specification_count": report.primary_specification_count,
        "robustness_specification_count": report.robustness_specification_count,
        "exploratory_specification_count": report.exploratory_specification_count,
        "p_value_count": report.p_value_count,
        "family_count": report.family_count,
        "role_family_counts": report.role_family_counts,
        "primary_discoveries_at_5pct": report.primary_discoveries_at_5pct,
        "primary_discoveries_at_10pct": report.primary_discoveries_at_10pct,
        "robustness_discoveries_at_10pct": report.robustness_discoveries_at_10pct,
        "exploratory_discoveries_at_10pct": report.exploratory_discoveries_at_10pct,
        "methods_applied": report.methods_applied,
        "families": [
            {
                "family_id": family.family_id,
                "base_family_id": family.base_family_id or family.family_id,
                "specification_role": family.specification_role,
                "number_of_tests": family.number_of_tests,
                "best_raw_p_value": family.best_raw_p_value,
                "best_adjusted_p_value": family.best_adjusted_p_value,
                "discoveries_at_5pct": family.discoveries_at_5pct,
                "discoveries_at_10pct": family.discoveries_at_10pct,
            }
            for family in report.families
        ],
    }


def _coverage_diagnosis_summary(
    waterfall: dict[str, Any],
    tables: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    counts = waterfall.get("counts", {}) if waterfall else {}
    failure_counts = waterfall.get("failure_counts", {}) if waterfall else {}
    return {
        "available": bool(waterfall),
        "raw_label_coverage": float(waterfall.get("raw_label_coverage", 0.0))
        if waterfall
        else 0.0,
        "eligible_oos_coverage": float(waterfall.get("eligible_oos_coverage", 0.0))
        if waterfall
        else 0.0,
        "model_expected_prediction_coverage": float(
            waterfall.get("model_expected_prediction_coverage", 0.0)
        )
        if waterfall
        else 0.0,
        "portfolio_eligible_coverage": float(
            waterfall.get("portfolio_eligible_coverage", 0.0)
        )
        if waterfall
        else 0.0,
        "primary_prediction_coverage": float(
            waterfall.get("primary_prediction_coverage", 0.0)
        )
        if waterfall
        else 0.0,
        "primary_portfolio_coverage": float(
            waterfall.get("primary_portfolio_coverage", 0.0)
        )
        if waterfall
        else 0.0,
        "primary_spec_coverage": float(waterfall.get("primary_spec_coverage", 0.0))
        if waterfall
        else 0.0,
        "counts": counts,
        "failure_counts": failure_counts,
        "top_failure_reasons": waterfall.get("top_failure_reasons", [])
        if waterfall
        else [],
        "by_target": tables.get("by_target", [])[:12],
        "by_split": tables.get("by_split", [])[:12],
        "by_model": tables.get("by_model", [])[:12],
        "by_ticker": tables.get("by_ticker", [])[:12],
    }


def _interpretation_policy(
    *,
    audit: AuditReportRecord,
    best_prediction: EvaluationMetricRecord | None,
    best_backtest: PortfolioBacktestRecord | None,
    multiple_testing_report: MultipleTestingReportRecord | None,
    allow_failed_audit: bool,
) -> dict[str, str]:
    if audit.audit_status == "fail":
        return {
            "evidence_level": "diagnostic_only",
            "economic_interpretation": (
                "The audit failed, so the run should be interpreted only as a "
                "pipeline diagnostic. No empirical factor claim should be made."
            ),
            "usage_boundary": "Use only for debugging failed artifacts and audit blockers.",
            "conclusion_text": (
                "This run is diagnostic only." if allow_failed_audit else "Report blocked."
            ),
        }
    adjusted_discovery = _has_adjusted_discovery(multiple_testing_report)
    prediction_positive = best_prediction is not None and best_prediction.rank_ic > 0
    backtest_positive = (
        best_backtest is not None and best_backtest.net_long_short_return > 0
    )
    best_prediction_model = (
        best_prediction.model_id.split("::", 1)[0] if best_prediction is not None else ""
    )
    if prediction_positive and not audit.formal_result_allowed:
        if best_prediction_model in {"historical_mean", "industry_mean"}:
            return {
                "evidence_level": (
                    "applied_pipeline_validated_with_positive_baseline_predictive_evidence"
                ),
                "economic_interpretation": (
                    "The applied pipeline is validated end-to-end and the best "
                    "out-of-sample prediction result is positive, but it is driven by "
                    f"the `{best_prediction_model}` baseline rather than a text model. "
                    "This is workflow and baseline evidence, not formal text alpha."
                ),
                "usage_boundary": (
                    "Report as an applied-grade pilot. Do not describe the result as "
                    "formal trading alpha; disclose mixed-source market data, the applied "
                    "public-data panel, and that industry structure dominates the best "
                    "prediction result."
                ),
                "conclusion_text": (
                    "The pipeline works and baseline predictive evidence is positive, "
                    "but formal text-factor and trading-alpha claims are not supported."
                ),
            }
        volatility_ranking = "volatility" in best_prediction.target_name.lower()
        return {
            "evidence_level": "exploratory_prediction_evidence_not_formal_trading_alpha",
            "economic_interpretation": (
                (
                    "The strongest evidence concerns cross-sectional ranking of future "
                    "realized volatility, not minimum-RMSE point forecasting. Industry "
                    "risk structure remains a strong baseline, so the current run does "
                    "not fully isolate the incremental contribution of text."
                )
                if volatility_ranking
                else (
                    "The run shows positive out-of-sample prediction evidence, but audit "
                    "or data-source boundaries prevent a formal trading-alpha conclusion."
                )
            ),
            "usage_boundary": (
                "Report as exploratory prediction evidence and disclose tested "
                "specifications, data-source boundaries, and portfolio limitations."
            ),
            "conclusion_text": (
                (
                    "Exploratory volatility-ranking evidence is present; return prediction "
                    "is weaker and formal trading-alpha evidence is not established."
                )
                if volatility_ranking
                else (
                    "Exploratory prediction evidence is present, but formal trading-alpha "
                    "evidence is not established."
                )
            ),
        }
    if prediction_positive and backtest_positive and adjusted_discovery:
        return {
            "evidence_level": "research_evidence_positive",
            "economic_interpretation": (
                "The run shows positive out-of-sample ranking evidence, positive "
                "net long-short performance, and at least one multiple-testing-adjusted "
                "discovery. The evidence supports further research review."
            ),
            "usage_boundary": (
                "Treat as research evidence, subject to universe quality, data rights, "
                "capacity diagnostics, borrow costs, and additional robustness checks."
            ),
            "conclusion_text": (
                "Evidence supports a candidate text factor under the current audited setup."
            ),
        }
    if prediction_positive and not backtest_positive:
        return {
            "evidence_level": "predictive_signal_economic_value_weak",
            "economic_interpretation": (
                "Prediction metrics are positive, but the available backtest does not "
                "show positive net economic value."
            ),
            "usage_boundary": "Do not describe the factor as economically validated.",
            "conclusion_text": "Predictive evidence exists, but economic value is weak.",
        }
    if prediction_positive and not adjusted_discovery:
        return {
            "evidence_level": "exploratory_signal_not_adjusted_significant",
            "economic_interpretation": (
            "The best predictive metric is positive, but the multiple-testing layer "
            "does not record an adjusted discovery. Primary, robustness, and "
            "exploratory specifications should be interpreted separately."
        ),
            "usage_boundary": "Report as exploratory only and disclose tested specifications.",
            "conclusion_text": "Pipeline works, but adjusted factor evidence is weak.",
        }
    return {
        "evidence_level": "weak_or_incomplete_evidence",
        "economic_interpretation": (
            "The current artifacts do not provide strong positive predictive and "
            "economic evidence after audit and multiple-testing review."
        ),
        "usage_boundary": "Use as a reproducible experiment log rather than a factor claim.",
        "conclusion_text": "Evidence is weak or incomplete under the current setup.",
    }


def _primary_signal_direction_policy(primary_specs: list[dict[str, Any]]) -> dict[str, Any]:
    prediction_specs = [
        spec for spec in primary_specs if spec.get("portfolio_method") == "prediction_metric"
    ]
    primary_prediction = prediction_specs[0] if prediction_specs else None
    raw_metric = (
        float(primary_prediction.get("raw_metric", 0.0))
        if primary_prediction is not None
        else 0.0
    )
    raw_p_value = primary_prediction.get("raw_p_value") if primary_prediction else None
    if raw_metric < 0:
        sign = "negative"
        explanation = (
            "The preregistered volatility prediction specification contains ranking "
            "information, but the Rank IC sign is negative under the current score "
            "convention. This must not be post-hoc inverted or described as a positive "
            "volatility forecast."
        )
    elif raw_metric > 0:
        sign = "positive"
        explanation = (
            "The preregistered prediction specification has a positive Rank IC under "
            "the current score convention."
        )
    else:
        sign = "zero_or_missing"
        explanation = (
            "The preregistered prediction specification is missing or has zero Rank IC "
            "under the current score convention."
        )
    return {
        "policy": "pre_registered_score_convention_no_post_hoc_sign_flip",
        "primary_prediction_sign": sign,
        "primary_prediction_model_id": (
            primary_prediction.get("model_id") if primary_prediction else None
        ),
        "primary_prediction_metric": raw_metric,
        "primary_prediction_p_value": raw_p_value,
        "explanation": explanation,
    }


def _top_prediction_outlier_rows(
    rows: list[dict[str, Any]],
    limit: int = 12,
) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -int(row.get("outlier_count", 0) or 0),
            -float(row.get("scale_ratio", 0.0) or 0.0),
            str(row.get("target_name", "")),
            str(row.get("model_name", "")),
        ),
    )[:limit]


def _has_adjusted_discovery(report: MultipleTestingReportRecord | None) -> bool:
    if report is None:
        return False
    return report.primary_discoveries_at_10pct > 0


def _check_summary(check: Any) -> dict[str, Any]:
    return {
        "check_id": check.check_id,
        "stage": check.stage,
        "severity": check.severity,
        "status": check.status,
        "message": check.message,
        "affected_artifacts": check.affected_artifacts,
        "observed_value": check.observed_value,
        "threshold": check.threshold,
    }


def _metrics_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No out-of-sample prediction metrics were available."
    lines = [
        "| Model | Split | Target | N | Agg | IC Group | Rank IC | Neutral Rank IC | "
        "Rank IC NW t | Neutral NW t | RMSE | Direction |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['model_id']} | {row['split_id']} | {row['target_name']} | "
            f"{row['observation_count']} | {row['aggregation_method']} | "
            f"{row['ic_grouping']} | {_fmt(row['rank_ic'])} | "
            f"{_fmt(row['industry_neutral_rank_ic'])} | "
            f"{_fmt(row['rank_ic_newey_west_t_stat'])} | "
            f"{_fmt(row['industry_neutral_rank_ic_newey_west_t_stat'])} | "
            f"{_fmt(row['rmse'])} | {_fmt(row['directional_accuracy'])} |"
        )
    return "\n".join(lines)


def _ranking_objective_section(rows: list[dict[str, Any]]) -> str:
    volatility_rows = [
        row for row in rows if "volatility" in str(row.get("target_name", "")).lower()
    ]
    if not volatility_rows:
        return (
            "Prediction metrics should be interpreted according to the registered "
            "target and evaluation objective."
        )

    best_rank = max(volatility_rows, key=lambda row: float(row.get("rank_ic", 0.0)))
    best_rmse = min(volatility_rows, key=lambda row: float(row.get("rmse", float("inf"))))
    industry = next(
        (
            row
            for row in volatility_rows
            if str(row.get("model_id", "")).split("::", 1)[0] == "industry_mean"
        ),
        None,
    )
    lines = [
        (
            "The model is evaluated primarily as a cross-sectional ranking signal, "
            "not as a minimum-RMSE volatility point forecast."
        ),
        (
            f"The highest volatility Rank IC is `{_fmt(best_rank.get('rank_ic'))}` "
            f"from `{best_rank.get('model_id')}`, while the lowest volatility RMSE is "
            f"`{_fmt(best_rmse.get('rmse'))}` from `{best_rmse.get('model_id')}`."
        ),
    ]
    if industry is not None:
        lines.append(
            "The industry-mean baseline remains strong "
            f"(Rank IC `{_fmt(industry.get('rank_ic'))}`), so the current experiment "
            "does not fully isolate the incremental contribution of text from industry "
            "risk structure."
        )
    lines.append(
        "ALL_SPLITS Rank IC is an aggregation across rolling out-of-sample splits, "
        "not a complete monthly cross-sectional IC time series."
    )
    return "\n\n".join(lines)


def _industry_neutral_interpretation(rows: list[dict[str, Any]]) -> str:
    volatility_rows = [
        row
        for row in rows
        if row.get("split_id") == "ALL_SPLITS"
        and "volatility" in str(row.get("target_name", "")).lower()
    ]
    if not volatility_rows:
        return "No ALL_SPLITS volatility rows were available for industry neutralization."
    lines = [
        (
            "Industry-neutral Rank IC separately demeans realized targets and model "
            "predictions within each OOS split-industry group before applying "
            "tie-aware rank correlation. It is a descriptive incremental-signal "
            "diagnostic, not a causal decomposition."
        ),
        "",
        "| Model | Raw Rank IC | Industry-Neutral Rank IC | Neutral NW t | Groups | Singletons |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        volatility_rows,
        key=lambda item: -float(item.get("industry_neutral_rank_ic", 0.0)),
    ):
        lines.append(
            "| "
            f"{row.get('model_id')} | {_fmt(row.get('rank_ic'))} | "
            f"{_fmt(row.get('industry_neutral_rank_ic'))} | "
            f"{_fmt(row.get('industry_neutral_rank_ic_newey_west_t_stat'))} | "
            f"{row.get('industry_neutral_group_count', 0)} | "
            f"{row.get('industry_neutral_singleton_group_count', 0)} |"
        )
    return "\n".join(lines)


def _feature_ablation_table(summary: dict[str, Any]) -> str:
    rows = summary.get("rows", []) if summary else []
    if not rows:
        return "No feature-ablation artifact was available."
    lines = [
        str(summary.get("comparison_policy", "")),
        "",
        "| Feature Set | Estimator | Target | Rank IC | Neutral Rank IC | "
        "Rank IC NW t | Neutral NW t | RMSE |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('feature_set')} | {row.get('estimator')} | "
            f"{row.get('target_name')} | {_fmt(row.get('rank_ic'))} | "
            f"{_fmt(row.get('industry_neutral_rank_ic'))} | "
            f"{_fmt(row.get('rank_ic_newey_west_t_stat'))} | "
            f"{_fmt(row.get('industry_neutral_rank_ic_newey_west_t_stat'))} | "
            f"{_fmt(row.get('rmse'))} |"
        )
    return "\n".join(lines)


def _bootstrap_table(summary: dict[str, Any]) -> str:
    rows = summary.get("rows", []) if summary else []
    if not rows:
        return "No primary Rank IC bootstrap artifact was available."
    lines = [
        (
            f"Bootstrap uses `{summary.get('iterations')}` deterministic resamples "
            f"(seed `{summary.get('random_seed')}`)."
        ),
        "",
        "| Estimand | Method | Point | 95% CI | Bootstrap SE | Zero p | Clusters |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('estimand')} | {row.get('bootstrap_method')} | "
            f"{_fmt(row.get('point_estimate'))} | "
            f"[{_fmt(row.get('ci_lower_95'))}, {_fmt(row.get('ci_upper_95'))}] | "
            f"{_fmt(row.get('bootstrap_standard_error'))} | "
            f"{_fmt(row.get('two_sided_zero_p_value'))} | "
            f"{row.get('cluster_count')} |"
        )
    return "\n".join(lines)


def _primary_portfolio_block(specification_registry: dict[str, Any]) -> str:
    primary = next(
        (
            spec
            for spec in specification_registry.get("primary_specifications", [])
            if spec.get("metric_name") == "portfolio_sharpe"
        ),
        None,
    )
    if primary is None:
        return "No preregistered primary portfolio specification was available."
    return "\n".join(
        [
            f"- Model: `{primary.get('model_id')}`.",
            f"- Target: `{primary.get('target_name')}`.",
            f"- Portfolio: `{primary.get('portfolio_method')}`.",
            f"- Sharpe ratio: `{_fmt(primary.get('raw_metric'))}`.",
            f"- Raw p-value: `{_fmt(primary.get('raw_p_value'))}`.",
            (
                "- Interpretation: diagnostic only; the preregistered portfolio test "
                "does not establish formal tradable alpha."
            ),
        ]
    )


def _backtest_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No factor backtest results were available."
    lines = [
        "| Model | Split | Target | Long | Short | Gross LS | Net LS | "
        "Sharpe | NW t-stat | Direction | Turnover |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['model_id']} | {row['split_id']} | {row['target_name']} | "
            f"{row['long_count']} | {row['short_count']} | "
            f"{_fmt(row['gross_long_short_return'])} | {_fmt(row['net_long_short_return'])} | "
            f"{_fmt(row['sharpe_ratio'])} | {_fmt(row['newey_west_t_stat'])} | "
            f"{row['signal_direction']} | {_fmt(row['turnover'])} |"
        )
    return "\n".join(lines)


def _portfolio_metric_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No portfolio variant metrics were available."
    lines = [
        "| Model | Variant | Target | Direction | N | Ann Ret | Ann Vol | "
        "Sharpe | NW t | Max DD | Turnover |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['model_id']} | {row['portfolio_variant']} | {row['target_name']} | "
            f"{row['signal_direction']} | {row['observation_count']} | "
            f"{_fmt(row['annualized_return'])} | "
            f"{_fmt(row['annualized_volatility'])} | {_fmt(row['sharpe_ratio'])} | "
            f"{_fmt(row['newey_west_t_stat'])} | {_fmt(row['max_drawdown'])} | "
            f"{_fmt(row['average_turnover'])} |"
        )
    return "\n".join(lines)


def _multiple_testing_section(summary: dict[str, Any]) -> str:
    if not summary["available"]:
        return "No multiple-testing report was available."
    lines = [
        (
            f"- Specifications: {summary['specification_count']}; "
            f"p-values: {summary['p_value_count']}; "
            f"families: {summary['family_count']}."
        ),
        (
            f"- Registry roles: primary={summary['primary_specification_count']}, "
            f"robustness={summary['robustness_specification_count']}, "
            f"exploratory={summary['exploratory_specification_count']}."
        ),
        (
            "- Role-split adjusted discoveries at 10% FDR: "
            f"primary={summary['primary_discoveries_at_10pct']}, "
            f"robustness={summary['robustness_discoveries_at_10pct']}, "
            f"exploratory={summary['exploratory_discoveries_at_10pct']}."
        ),
        f"- Methods: {_inline_list(summary.get('methods_applied', []))}.",
        "",
        "| Role | Family | Tests | Best raw p | Best BH-FDR p | Discoveries 5% | Discoveries 10% |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in summary["families"]:
        lines.append(
            "| "
            f"{family['specification_role']} | {family['base_family_id']} | "
            f"{family['number_of_tests']} | "
            f"{_fmt(family['best_raw_p_value'] or 0.0)} | "
            f"{_fmt(family['best_adjusted_p_value'] or 0.0)} | "
            f"{family['discoveries_at_5pct']} | {family['discoveries_at_10pct']} |"
        )
    return "\n".join(lines)


def _coverage_diagnosis_section(summary: dict[str, Any]) -> str:
    if not summary["available"]:
        return "No coverage waterfall artifact was available."
    counts = summary["counts"]
    lines = [
        (
            f"- Raw label coverage: `{_fmt(summary['raw_label_coverage'])}` "
            f"({counts.get('predicted_unique_labels', 0)} / "
            f"{counts.get('labels_total', 0)} labels)."
        ),
        (
            "- Raw label coverage includes train-window labels that are not expected "
            "to receive out-of-sample predictions; eligible OOS coverage is the "
            "prediction-completeness metric for validation/test labels."
        ),
        (
            f"- Eligible OOS coverage: `{_fmt(summary['eligible_oos_coverage'])}` "
            f"({counts.get('predicted_eligible_oos_labels', 0)} / "
            f"{counts.get('eligible_oos_labels', 0)} validation/test labels)."
        ),
        (
            "- Model-expected prediction coverage: "
            f"`{_fmt(summary['model_expected_prediction_coverage'])}` "
            f"({counts.get('model_predicted_label_pairs', 0)} / "
            f"{counts.get('model_expected_label_pairs', 0)} model-label pairs)."
        ),
        (
            f"- Primary spec coverage: `{_fmt(summary['primary_spec_coverage'])}` "
            f"({counts.get('primary_covered_specifications', 0)} / "
            f"{counts.get('primary_expected_specifications', 0)} primary specifications)."
        ),
        (
            "- Primary prediction coverage: "
            f"`{_fmt(summary['primary_prediction_coverage'])}` "
            f"({counts.get('primary_prediction_covered_specifications', 0)} / "
            f"{counts.get('primary_prediction_expected_specifications', 0)})."
        ),
        (
            "- Primary portfolio coverage: "
            f"`{_fmt(summary['primary_portfolio_coverage'])}` "
            f"({counts.get('primary_portfolio_covered_specifications', 0)} / "
            f"{counts.get('primary_portfolio_expected_specifications', 0)})."
        ),
        (
            "- Portfolio-eligible coverage: "
            f"`{_fmt(summary['portfolio_eligible_coverage'])}` "
            f"({counts.get('predicted_portfolio_eligible_labels', 0)} / "
            f"{counts.get('portfolio_eligible_labels', 0)} test labels)."
        ),
        "",
        "### Coverage By Target",
        "",
        _coverage_table(
            summary["by_target"],
            ["target_name", "labels_total", "eligible_oos_labels", "eligible_oos_coverage"],
        ),
        "",
        "### Coverage By Split",
        "",
        _coverage_table(
            summary["by_split"],
            [
                "split_id",
                "eligible_oos_labels",
                "predicted_eligible_oos_labels",
                "eligible_oos_coverage",
            ],
        ),
        "",
        "### Coverage By Model",
        "",
        _coverage_table(
            summary["by_model"],
            [
                "model_name",
                "expected_label_pairs",
                "predicted_label_pairs",
                "model_expected_prediction_coverage",
            ],
        ),
        "",
        "### Top Failure Reasons",
        "",
        _coverage_failure_table(summary["top_failure_reasons"]),
    ]
    return "\n".join(lines)


def _formal_result_blocker_section(blockers: list[str]) -> str:
    if not blockers:
        return "No formal-result blocker was detected."
    lines = [
        "Formal result is not allowed for data-boundary reasons, not because the "
        "pipeline failed:",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    return "\n".join(lines)


def _licensed_data_stack_section(summary: dict[str, Any]) -> str:
    manifest = summary.get("license_manifest")
    lines = [
        f"- Market data provider: `{summary['market_data_provider']}`.",
        f"- Filing provider: `{summary['filing_provider']}`.",
        f"- Price source: `{summary['price_source']}`.",
        f"- Return source: `{summary['return_source']}`.",
        f"- Delisting return source: `{summary.get('delisting_return_source')}`.",
        f"- Link source: `{summary.get('link_source')}`.",
        (
            "- Public Yahoo fallback allowed: "
            f"`{summary['allow_public_yahoo_fallback']}`."
        ),
    ]
    if not manifest:
        lines.append("- Licensed data manifest: `missing`.")
        return "\n".join(lines)
    lines.extend(
        [
            f"- Licensed data manifest: `{manifest['data_stack']}`.",
            f"- Raw licensed data committed: `{manifest['raw_data_committed']}`.",
            f"- Data rights scope: `{manifest.get('data_rights_scope') or 'unspecified'}`.",
            f"- License note: {manifest['license_note']}",
        ]
    )
    public_outputs = manifest.get("permitted_public_outputs", [])
    if public_outputs:
        lines.append(f"- Permitted public outputs: {_inline_list(public_outputs)}.")
    return "\n".join(lines)


def _coverage_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows available."
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _coverage_failure_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No coverage failure reasons were recorded."
    lines = [
        "| Stage | Reason | Count |",
        "| --- | --- | ---: |",
    ]
    for row in rows[:10]:
        lines.append(
            "| "
            f"{row.get('failure_stage', '')} | "
            f"{row.get('failure_reason', '')} | "
            f"{row.get('count', 0)} |"
        )
    return "\n".join(lines)


def _delisting_report_section(report: dict[str, Any]) -> str:
    if not report:
        return "No delisting application report was available."
    return "\n".join(
        [
            f"- Status: `{report.get('status', 'unknown')}`.",
            (
                "- Labels with delisting return applied: "
                f"`{report.get('labels_with_delisting_return_applied', 0)}`."
            ),
            (
                "- Portfolio positions affected by delisting: "
                f"`{report.get('positions_affected_by_delisting', 0)}`."
            ),
            (
                "- Delisting returns applied in portfolio rows: "
                f"`{report.get('delisting_returns_applied', 0)}`."
            ),
            (
                "- Missing delisting returns: "
                f"`{report.get('missing_delisting_returns', 0)}`."
            ),
        ]
    )


def _specification_registry_section(summary: dict[str, Any]) -> str:
    if not summary["available"]:
        return "No specification registry artifact was available."
    role_counts = summary.get("role_counts", {})
    primary_specs = summary.get("primary_specifications", [])
    preregistration = summary.get("preregistration", {})
    preregistered_rules = summary.get("preregistered_primary_rules", [])
    lines = [
        (
            "- Role counts: "
            f"primary={role_counts.get('primary', 0)}, "
            f"robustness={role_counts.get('robustness', 0)}, "
            f"exploratory={role_counts.get('exploratory', 0)}."
        ),
        f"- Registry version: `{summary.get('registry_version')}`.",
        f"- Registry designation: `{summary.get('registry_designation')}`.",
        (
            "- Preregistration status: "
            f"`{preregistration.get('status', 'unspecified')}`."
        ),
        (
            "- Preregistered primary rule count: "
            f"`{len(preregistered_rules)}`."
        ),
        "",
        "| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for spec in primary_specs[:12]:
        lines.append(
            "| primary | "
            f"{spec.get('rule_status', 'unspecified')} | "
            f"{spec['target_name']} | {spec['model_name']} | {spec['metric_name']} | "
            f"{spec['split_id']} | {spec['portfolio_method']} | "
            f"{_fmt(spec['raw_metric'])} | {_fmt(spec['raw_p_value'] or 0.0)} |"
        )
    if not primary_specs:
        lines.append("| primary | none | none | none | none | none | none | 0 | 0 |")
    return "\n".join(lines)


def _single_metric_block(row: dict[str, Any] | None) -> str:
    if row is None:
        return "No prediction metric is available."
    return "\n".join(
        [
            f"- Model: `{row['model_id']}`.",
            f"- Target: `{row['target_name']}`.",
            f"- Split: `{row['split_id']}`.",
            f"- Rank IC: `{_fmt(row['rank_ic'])}`.",
            f"- Rank IC Newey-West t-stat: `{_fmt(row['rank_ic_newey_west_t_stat'])}`.",
            f"- Aggregation: `{row['aggregation_method']}`.",
            f"- RMSE: `{_fmt(row['rmse'])}`.",
            f"- Directional accuracy: `{_fmt(row['directional_accuracy'])}`.",
        ]
    )


def _single_backtest_block(row: dict[str, Any] | None) -> str:
    if row is None:
        return "No backtest result is available."
    return "\n".join(
        [
            f"- Model: `{row['model_id']}`.",
            f"- Target: `{row['target_name']}`.",
            f"- Net long-short return: `{_fmt(row['net_long_short_return'])}`.",
            f"- Sharpe ratio: `{_fmt(row['sharpe_ratio'])}`.",
            f"- Newey-West t-stat: `{_fmt(row['newey_west_t_stat'])}`.",
            f"- Signal direction: `{row['signal_direction']}`.",
            f"- Turnover: `{_fmt(row['turnover'])}`.",
        ]
    )


def _limitations_text(summary: dict[str, Any]) -> str:
    primary_neutral = next(
        (
            row
            for row in summary["evaluation"]["test_metrics"]
            if row.get("model_id")
            == "ridge::realized_volatility_1_20::ALL_SPLITS"
        ),
        {},
    )
    limitations = [
        "Universe quality must be reviewed before formal empirical claims.",
        (
            "Portfolio diagnostics apply a tie-aware eligibility policy, but remain "
            "secondary to the preregistered prediction test."
        ),
        (
            "Industry-neutral Rank IC is descriptive rather than causal and is "
            "estimated from sparse groups: "
            f"{primary_neutral.get('industry_neutral_singleton_group_count', 0)} "
            "split-industry groups contain only one observation."
        ),
        (
            "Split bootstrap has only "
            f"{summary['evaluation']['primary_rank_ic_bootstrap'].get('split_count', 0)} "
            "OOS split clusters; event-date and ticker-cluster intervals are reported "
            "as complementary sensitivity checks."
        ),
        "Deflated Sharpe and CPCV/PBO are not included.",
    ]
    if not summary["multiple_testing"]["available"]:
        limitations.append("Multiple-testing artifacts were not available for this report.")
    if summary["audit"]["warn_count"]:
        limitations.append("Audit warnings should be resolved or disclosed.")
    return "\n".join(f"- {item}" for item in limitations)


def _audit_table(failed: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
    checks = failed + warnings
    if not checks:
        return "No failed or warning audit checks."
    lines = [
        "| Status | Check | Stage | Message |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        lines.append(
            f"| {check['status']} | {check['check_id']} | {check['stage']} | "
            f"{check['message']} |"
        )
    return "\n".join(lines)


def _failure_section(audit: dict[str, Any]) -> str:
    if audit["fail_count"] == 0:
        return "No blocking failures were recorded by the audit layer."
    return "\n".join(
        f"- `{check['check_id']}`: {check['message']}" for check in audit["failed_checks"]
    )


def _conclusion_text(summary: dict[str, Any]) -> str:
    level = summary["conclusion_level"]
    if level == "formal_report_allowed":
        return "The audit passed and the run may be cited as a formal result."
    if level == "exploratory_report":
        return (
            "The run is reportable as exploratory evidence only. Do not present it as a "
            "formal empirical-finance result."
        )
    if level == "prediction_only_no_backtest":
        return "The run has prediction metrics but no backtest results."
    if level == "diagnostic_only":
        return "The audit failed, so this report is diagnostic only."
    if level == "incomplete_no_metrics":
        return "The run does not yet contain evaluation metrics."
    return "Report generation was blocked by audit status."


def _inline_list(values: list[str]) -> str:
    if not values:
        return "`none`"
    return ", ".join(f"`{value}`" for value in values)


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _read_json_object(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json_object(path)


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON array in {path}")
    return payload


def _read_optional_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _read_json_array(path)


def _read_optional_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def _read_optional_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _read_optional_multiple_testing_report(path: Path) -> MultipleTestingReportRecord | None:
    if not path.exists():
        return None
    return MultipleTestingReportRecord.model_validate(_read_json_object(path))


def _read_data_license_manifest(config_path: Path) -> DataLicenseManifestRecord | None:
    config = load_experiment_config(config_path)
    manifest_path = config.data_provider.data_license_manifest_file
    if manifest_path is None:
        return None
    path = Path(manifest_path)
    if not path.exists():
        return None
    return DataLicenseManifestRecord.model_validate(_read_json_object(path))


def _count_jsonl_records(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def _mark_run_reported(path: Path, audit: AuditReportRecord) -> None:
    if not path.exists() or audit.audit_status == "fail":
        return
    status = RunStatusRecord.model_validate(_read_json_object(path))
    updated = status.model_copy(
        update={
            "status": "reported",
            "audit_status": audit.audit_status,
            "coverage": audit.coverage,
            "updated_at_utc": datetime.now(UTC),
        }
    )
    path.write_text(json.dumps(updated.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
