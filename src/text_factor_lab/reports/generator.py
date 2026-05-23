from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from text_factor_lab.schemas import (
    AuditReportRecord,
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
    model_manifest: Path
    tuning_log: Path
    feature_manifest: Path
    portfolio_metrics: Path
    multiple_testing_report: Path
    report_markdown: Path
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
            model_manifest=base / "model_manifest.json",
            tuning_log=base / "tuning_log.json",
            feature_manifest=base / "feature_manifest.json",
            portfolio_metrics=base / "portfolio_metrics.json",
            multiple_testing_report=base / "multiple_testing_report.json",
            report_markdown=output / "report.md",
            report_summary=output / "report_summary.json",
        )


@dataclass(frozen=True)
class ReportBuildResult:
    run_id: str
    report_markdown_path: Path
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

    paths.report_markdown.parent.mkdir(parents=True, exist_ok=True)
    paths.report_markdown.write_text(markdown, encoding="utf-8")
    paths.report_summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _mark_run_reported(paths.run_status, audit)
    return ReportBuildResult(
        run_id=run_id,
        report_markdown_path=paths.report_markdown,
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
        "portfolio_metrics": [
            PortfolioMetricRecord.model_validate(item)
            for item in _read_optional_json_array(paths.portfolio_metrics)
        ],
        "multiple_testing_report": _read_optional_multiple_testing_report(
            paths.multiple_testing_report
        ),
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
    audit: AuditReportRecord = artifacts["audit_report"]
    metrics: list[EvaluationMetricRecord] = artifacts["evaluation_metrics"]
    backtests: list[PortfolioBacktestRecord] = artifacts["backtest_results"]
    model_manifest: list[ModelManifestRecord] = artifacts["model_manifest"]
    feature_manifest: list[FeatureManifestRecord] = artifacts["feature_manifest"]
    tuning_log: list[TuningLogRecord] = artifacts["tuning_log"]
    portfolio_metrics: list[PortfolioMetricRecord] = artifacts["portfolio_metrics"]
    multiple_testing_report: MultipleTestingReportRecord | None = artifacts[
        "multiple_testing_report"
    ]

    best_prediction = _best_prediction_metric(metrics)
    best_backtest = _best_backtest(backtests)
    failed_checks = [check for check in audit.checks if check.status == "fail"]
    warning_checks = [check for check in audit.checks if check.status == "warn"]
    conclusion_level = _conclusion_level(audit, metrics, backtests, allow_failed_audit)

    return {
        "report_version": REPORT_VERSION,
        "run_id": run_id,
        "run_type": config.run.run_type,
        "generated_at_utc": generated_at_utc.isoformat(),
        "conclusion_level": conclusion_level,
        "formal_result_allowed": audit.formal_result_allowed and audit.audit_status == "pass",
        "audit": {
            "status": audit.audit_status,
            "coverage": audit.coverage,
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
        },
        "backtest": {
            "result_count": len(backtests),
            "portfolio_metric_count": len(portfolio_metrics),
            "portfolio_method": config.backtest.portfolio_method,
            "weighting": config.backtest.weighting,
            "transaction_cost_bps_one_way": config.backtest.transaction_cost_bps_one_way,
            "newey_west_lag": config.backtest.newey_west_lag,
            "best_backtest": _backtest_summary(best_backtest) if best_backtest else None,
            "top_backtests": [_backtest_summary(record) for record in _top_backtests(backtests)],
        },
        "multiple_testing": _multiple_testing_summary(multiple_testing_report),
        "reproducibility": {
            "config_path": str(paths.config),
            "report_markdown_path": str(paths.report_markdown),
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
        _metrics_table(summary["evaluation"]["test_metrics"]),
        "",
        "## Factor Backtest",
        "",
        f"- Portfolio method: `{summary['backtest']['portfolio_method']}`.",
        f"- Weighting: `{summary['backtest']['weighting']}`.",
        f"- One-way transaction cost: {summary['backtest']['transaction_cost_bps_one_way']} bps.",
        f"- Newey-West lag: {summary['backtest']['newey_west_lag']}.",
        "",
        _backtest_table(summary["backtest"]["top_backtests"]),
        "",
        "## Multiple Testing Adjustment",
        "",
        _multiple_testing_section(summary["multiple_testing"]),
        "",
        "## Robustness Checks",
        "",
        (
            "- Current MVP report summarizes split-level and `ALL_SPLITS` metrics. "
            "Subperiod stability, Deflated Sharpe, CPCV/PBO, and daily price-driven "
            "portfolio holdings should be added before making production research claims."
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
        "```bash",
        *summary["reproducibility"]["commands"],
        "```",
        "",
        f"Generated at `{summary['generated_at_utc']}` by `{summary['report_version']}`.",
        "",
    ]
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
    return sorted(candidates, key=lambda item: (-item.rank_ic, item.rmse, item.model_id))[:limit]


def _best_backtest(backtests: list[PortfolioBacktestRecord]) -> PortfolioBacktestRecord | None:
    if not backtests:
        return None
    return sorted(backtests, key=lambda item: (-item.net_long_short_return, item.model_id))[0]


def _top_backtests(
    backtests: list[PortfolioBacktestRecord],
    limit: int = 10,
) -> list[PortfolioBacktestRecord]:
    return sorted(backtests, key=lambda item: (-item.net_long_short_return, item.model_id))[:limit]


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
        "turnover": record.turnover,
    }


def _multiple_testing_summary(
    report: MultipleTestingReportRecord | None,
) -> dict[str, Any]:
    if report is None:
        return {
            "available": False,
            "specification_count": 0,
            "p_value_count": 0,
            "family_count": 0,
            "families": [],
        }
    return {
        "available": True,
        "specification_count": report.specification_count,
        "p_value_count": report.p_value_count,
        "family_count": report.family_count,
        "methods_applied": report.methods_applied,
        "families": [
            {
                "family_id": family.family_id,
                "number_of_tests": family.number_of_tests,
                "best_raw_p_value": family.best_raw_p_value,
                "best_adjusted_p_value": family.best_adjusted_p_value,
                "discoveries_at_5pct": family.discoveries_at_5pct,
                "discoveries_at_10pct": family.discoveries_at_10pct,
            }
            for family in report.families
        ],
    }


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
        "| Model | Split | Target | N | RMSE | MAE | R2 | Direction | Pearson IC | Rank IC |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['model_id']} | {row['split_id']} | {row['target_name']} | "
            f"{row['observation_count']} | {_fmt(row['rmse'])} | {_fmt(row['mae'])} | "
            f"{_fmt(row['r_squared'])} | {_fmt(row['directional_accuracy'])} | "
            f"{_fmt(row['pearson_ic'])} | {_fmt(row['rank_ic'])} |"
        )
    return "\n".join(lines)


def _backtest_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No factor backtest results were available."
    lines = [
        "| Model | Split | Target | Long | Short | Gross LS | Net LS | "
        "Sharpe | NW t-stat | Turnover |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['model_id']} | {row['split_id']} | {row['target_name']} | "
            f"{row['long_count']} | {row['short_count']} | "
            f"{_fmt(row['gross_long_short_return'])} | {_fmt(row['net_long_short_return'])} | "
            f"{_fmt(row['sharpe_ratio'])} | {_fmt(row['newey_west_t_stat'])} | "
            f"{_fmt(row['turnover'])} |"
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
        f"- Methods: {_inline_list(summary.get('methods_applied', []))}.",
        "",
        "| Family | Tests | Best raw p | Best BH-FDR p | Discoveries 5% | Discoveries 10% |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in summary["families"]:
        lines.append(
            "| "
            f"{family['family_id']} | {family['number_of_tests']} | "
            f"{_fmt(family['best_raw_p_value'] or 0.0)} | "
            f"{_fmt(family['best_adjusted_p_value'] or 0.0)} | "
            f"{family['discoveries_at_5pct']} | {family['discoveries_at_10pct']} |"
        )
    return "\n".join(lines)


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


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON array in {path}")
    return payload


def _read_optional_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _read_json_array(path)


def _read_optional_multiple_testing_report(path: Path) -> MultipleTestingReportRecord | None:
    if not path.exists():
        return None
    return MultipleTestingReportRecord.model_validate(_read_json_object(path))


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
