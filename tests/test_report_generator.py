from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml

from text_factor_lab.reports import generate_run_report
from text_factor_lab.schemas import (
    AuditCheckRecord,
    AuditReportRecord,
    EvaluationMetricRecord,
    LabelRecord,
    ModelManifestRecord,
    PortfolioBacktestRecord,
    PredictionRecord,
    RunStatusRecord,
    TuningLogRecord,
)


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def write_config_and_status(run_dir: Path, *, run_type: str = "exploratory_run") -> None:
    payload = yaml.safe_load(Path("configs/text_factor_lab/mvp_v0.yaml").read_text())
    payload["run"]["run_id"] = "report_test_run"
    payload["run"]["run_type"] = run_type
    payload["run"]["output_dir"] = str(run_dir)
    if run_type == "formal_run":
        manifest_path = run_dir / "licensed_data_manifest.json"
        payload["data_provider"] = {
            "market_data_provider": "crsp_wrds",
            "filing_provider": "sec_edgar",
            "price_source": "crsp_daily_stock",
            "return_source": "crsp_total_return",
            "delisting_return_source": "crsp_delisting",
            "link_source": "crsp_compustat_ccm",
            "allow_public_yahoo_fallback": False,
            "data_license_manifest_file": str(manifest_path),
        }
        payload["text_source"]["require_available_time"] = True
        payload["text_source"]["require_license_note"] = True
        payload["text_source"]["sec_user_agent"] = "test@example.com"
        payload["audit"]["require_available_time"] = True
        payload["audit"]["require_license_note"] = True
        manifest_path.write_text(
            json.dumps(
                {
                    "data_stack": "mock_crsp_wrds",
                    "market_data_provider": "crsp_wrds",
                    "filing_provider": "sec_edgar",
                    "price_source": "crsp_daily_stock",
                    "return_source": "crsp_total_return",
                    "delisting_return_source": "crsp_delisting",
                    "link_source": "crsp_compustat_ccm",
                    "data_rights_scope": "local research use only",
                    "license_note": "Mock licensed-data manifest.",
                    "raw_data_committed": False,
                    "allow_public_yahoo_fallback": False,
                    "created_at_utc": "2026-05-25T00:00:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    (run_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    status = RunStatusRecord(
        run_id="report_test_run",
        run_type=run_type,
        status="audited",
        created_at_utc=utc(2020, 1, 1),
        updated_at_utc=utc(2020, 1, 2),
        config_path=str(run_dir / "config_snapshot.yaml"),
        failure_reason=None,
        audit_status="pass",
        coverage=1.0,
    )
    (run_dir / "run_status.json").write_text(
        json.dumps(status.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )


def label_record() -> LabelRecord:
    return LabelRecord(
        label_id="sec:aapl:2020:CAR_1_20:labels-v0",
        entity_id="CIK0000320193",
        ticker="AAPL",
        event_time_utc=utc(2020, 1, 1),
        prediction_time_utc=utc(2020, 1, 1),
        label_start_date=date(2020, 1, 2),
        label_end_date=date(2020, 1, 31),
        target_name="CAR_1_20",
        target_value=0.05,
        benchmark_method="SPY",
        return_type="log",
        adjustment_method="adj_close",
        label_version="labels-v0",
    )


def prediction_record(label: LabelRecord) -> PredictionRecord:
    return PredictionRecord(
        run_id="report_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="split",
        label_id=label.label_id,
        role="test",
        ticker=label.ticker,
        event_date=label.event_time_utc.date(),
        target_name=label.target_name,
        prediction_value=0.04,
        factor_score=0.04,
        feature_version="features-v0:split",
        label_version=label.label_version,
        training_window="2010-01-01..2018-12-31",
        validation_window="2019-01-01..2019-12-31",
        test_window="2020-01-01..2020-12-31",
    )


def model_manifest_record(label: LabelRecord) -> ModelManifestRecord:
    return ModelManifestRecord(
        model_id="ridge::CAR_1_20::split",
        model_name="ridge",
        model_family="linear_regularized",
        model_level=2,
        model_version="model-training-v0",
        hyperparameters={"alpha": 1.0},
        random_seed=42,
        training_window="2010-01-01..2018-12-31",
        validation_window="2019-01-01..2019-12-31",
        test_window="2020-01-01..2020-12-31",
        feature_version="features-v0:split",
        label_version=label.label_version,
        train_observation_count=10,
        validation_observation_count=2,
        test_observation_count=1,
        feature_count=5,
        created_at_utc=utc(2020, 2, 1),
    )


def metric_record(label: LabelRecord) -> EvaluationMetricRecord:
    return EvaluationMetricRecord(
        run_id="report_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="ALL_SPLITS",
        target_name=label.target_name,
        role="test",
        observation_count=5,
        rmse=0.01,
        mae=0.01,
        r_squared=0.2,
        directional_accuracy=0.8,
        pearson_ic=0.5,
        rank_ic=0.6,
        created_at_utc=utc(2020, 2, 1),
    )


def backtest_record(label: LabelRecord) -> PortfolioBacktestRecord:
    return PortfolioBacktestRecord(
        run_id="report_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="split",
        target_name=label.target_name,
        role="test",
        portfolio_method="top_bottom_quintile_min_one",
        weighting="equal_weight",
        rebalance_frequency="event_based",
        long_count=1,
        short_count=1,
        gross_long_short_return=0.02,
        turnover=2.0,
        transaction_cost_bps_one_way=10.0,
        net_long_short_return=0.018,
        sharpe_ratio=0.5,
        newey_west_lag=19,
        newey_west_t_stat=0.1,
        created_at_utc=utc(2020, 2, 1),
    )


def tuning_log_record(label: LabelRecord) -> TuningLogRecord:
    return TuningLogRecord(
        run_id="report_test_run",
        split_id="split",
        target_name=label.target_name,
        model_id="ridge::CAR_1_20::split",
        parameter_grid={"alpha": [1.0]},
        searched_parameters=[{"alpha": 1.0}],
        validation_metric="validation_rank_ic",
        validation_scores=[1.0],
        selected_parameters={"alpha": 1.0},
        selection_reason="Selected highest validation rank IC.",
        created_at_utc=utc(2020, 2, 1),
    )


def audit_report_record(*, status: str = "pass") -> AuditReportRecord:
    checks = [
        AuditCheckRecord(
            run_id="report_test_run",
            check_id="artifact_presence",
            stage="audit",
            severity="fail" if status == "fail" else "info",
            status=status,
            message="Artifacts are present." if status != "fail" else "Missing required artifact.",
            affected_artifacts=["evaluation_metrics.json"],
            observed_value=None,
            threshold=None,
            created_at_utc=utc(2020, 2, 1),
        )
    ]
    return AuditReportRecord(
        run_id="report_test_run",
        run_type="exploratory_run",
        audit_status=status,
        formal_result_allowed=False,
        coverage=0.0 if status == "fail" else 1.0,
        check_count=len(checks),
        fail_count=1 if status == "fail" else 0,
        warn_count=0,
        checks=checks,
        created_at_utc=utc(2020, 2, 1),
    )


def write_jsonl(path: Path, records: list) -> None:
    path.write_text(
        "".join(record.model_dump_json() + "\n" for record in records),
        encoding="utf-8",
    )


def write_json_array(path: Path, records: list) -> None:
    path.write_text(
        json.dumps([record.model_dump(mode="json") for record in records], indent=2) + "\n",
        encoding="utf-8",
    )


def write_report_artifacts(run_dir: Path, *, audit_status: str = "pass") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_config_and_status(run_dir)
    label = label_record()
    write_jsonl(run_dir / "document_manifest.jsonl", [])
    write_jsonl(run_dir / "labels.jsonl", [label])
    write_jsonl(run_dir / "predictions.jsonl", [prediction_record(label)])
    write_jsonl(run_dir / "features.jsonl", [])
    write_json_array(run_dir / "feature_manifest.json", [])
    write_json_array(run_dir / "model_manifest.json", [model_manifest_record(label)])
    write_json_array(run_dir / "tuning_log.json", [tuning_log_record(label)])
    write_json_array(run_dir / "evaluation_metrics.json", [metric_record(label)])
    write_json_array(run_dir / "backtest_results.json", [backtest_record(label)])
    (run_dir / "audit_report.json").write_text(
        json.dumps(audit_report_record(status=audit_status).model_dump(mode="json"), indent=2)
        + "\n",
        encoding="utf-8",
    )


def test_generate_run_report_writes_markdown_summary_and_status(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "report_test_run"
    write_report_artifacts(run_dir)

    result = generate_run_report(run_id="report_test_run", run_dir=run_dir)

    assert result.conclusion_level == "exploratory_report"
    assert result.report_markdown_path.exists()
    assert result.empirical_report_path.exists()
    assert result.factor_card_path.exists()
    assert result.appendix_tables_path.exists()
    assert result.report_summary_path.exists()
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    empirical = result.empirical_report_path.read_text(encoding="utf-8")
    factor_card = result.factor_card_path.read_text(encoding="utf-8")
    appendix = result.appendix_tables_path.read_text(encoding="utf-8")
    assert "Executive Summary" in markdown
    assert "Out-Of-Sample Prediction Results" in markdown
    assert "Empirical Report" in empirical
    assert "Economic Interpretation" in empirical
    assert "Factor Card" in factor_card
    assert "Appendix Tables" in appendix
    summary = json.loads(result.report_summary_path.read_text(encoding="utf-8"))
    assert summary["evaluation"]["best_prediction_metric"]["rank_ic"] == 0.6
    assert "interpretation" in summary
    assert summary["reproducibility"]["empirical_report_path"].endswith(
        "empirical_report.md"
    )
    status = json.loads((run_dir / "run_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "reported"


def test_report_cli_writes_artifacts(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    run_dir = tmp_path / "runs" / "report_test_run"
    write_report_artifacts(run_dir)

    exit_code = main(["report", "--run-id", "report_test_run", "--run-dir", str(run_dir)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Report generated" in captured.out
    assert (run_dir / "report.md").exists()
    assert (run_dir / "empirical_report.md").exists()
    assert (run_dir / "factor_card.md").exists()
    assert (run_dir / "appendix_tables.md").exists()
    assert (run_dir / "report_summary.json").exists()


def test_report_blocks_failed_audit_by_default(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "report_test_run"
    write_report_artifacts(run_dir, audit_status="fail")

    with pytest.raises(ValueError, match="audit_status=fail"):
        generate_run_report(run_id="report_test_run", run_dir=run_dir)

    result = generate_run_report(
        run_id="report_test_run",
        run_dir=run_dir,
        allow_failed_audit=True,
    )
    assert result.conclusion_level == "diagnostic_only"


def test_formal_report_includes_licensed_data_stack(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "report_test_run"
    write_report_artifacts(run_dir)
    write_config_and_status(run_dir, run_type="formal_run")

    result = generate_run_report(run_id="report_test_run", run_dir=run_dir)
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    summary = json.loads(result.report_summary_path.read_text(encoding="utf-8"))

    assert "Licensed Data Stack" in markdown
    assert "`crsp_wrds`" in markdown
    assert summary["data_provider"]["license_manifest_available"] is True
    assert summary["data_provider"]["license_manifest"]["raw_data_committed"] is False
