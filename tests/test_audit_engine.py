from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

from text_factor_lab.audit import audit_run
from text_factor_lab.schemas import (
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


def prediction_record(label: LabelRecord, *, label_id: str | None = None) -> PredictionRecord:
    return PredictionRecord(
        run_id="audit_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="split",
        label_id=label.label_id if label_id is None else label_id,
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
        code_commit=None,
        train_observation_count=10,
        validation_observation_count=2,
        test_observation_count=1,
        feature_count=5,
        created_at_utc=utc(2020, 2, 1),
    )


def metric_record(label: LabelRecord) -> EvaluationMetricRecord:
    return EvaluationMetricRecord(
        run_id="audit_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="split",
        target_name=label.target_name,
        role="test",
        observation_count=1,
        rmse=0.01,
        mae=0.01,
        r_squared=0.0,
        directional_accuracy=1.0,
        pearson_ic=0.0,
        rank_ic=0.0,
        created_at_utc=utc(2020, 2, 1),
    )


def backtest_record(label: LabelRecord) -> PortfolioBacktestRecord:
    return PortfolioBacktestRecord(
        run_id="audit_test_run",
        model_id="ridge::CAR_1_20::split",
        split_id="split",
        target_name=label.target_name,
        role="test",
        portfolio_method="top_bottom_quintile",
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
        newey_west_t_stat=0.0,
        created_at_utc=utc(2020, 2, 1),
    )


def tuning_log_record(label: LabelRecord) -> TuningLogRecord:
    return TuningLogRecord(
        run_id="audit_test_run",
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


def write_config_and_status(run_dir: Path) -> None:
    payload = yaml.safe_load(Path("configs/text_factor_lab/mvp_v0.yaml").read_text())
    payload["run"]["run_id"] = "audit_test_run"
    payload["run"]["run_type"] = "exploratory_run"
    payload["run"]["output_dir"] = str(run_dir)
    (run_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    status = RunStatusRecord(
        run_id="audit_test_run",
        run_type="exploratory_run",
        status="evaluated",
        created_at_utc=utc(2020, 1, 1),
        updated_at_utc=utc(2020, 1, 1),
        config_path=str(run_dir / "config_snapshot.yaml"),
        failure_reason=None,
        audit_status="not_run",
        coverage=0.0,
    )
    (run_dir / "run_status.json").write_text(
        json.dumps(status.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )


def write_complete_audit_artifacts(run_dir: Path, *, bad_prediction_label: bool = False) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_config_and_status(run_dir)
    label = label_record()
    prediction = prediction_record(
        label,
        label_id="missing-label" if bad_prediction_label else None,
    )
    write_jsonl(run_dir / "document_manifest.jsonl", [])
    write_jsonl(run_dir / "labels.jsonl", [label])
    write_jsonl(run_dir / "split_leakage.jsonl", [])
    write_jsonl(run_dir / "features.jsonl", [])
    write_json_array(run_dir / "feature_manifest.json", [])
    write_jsonl(run_dir / "predictions.jsonl", [prediction])
    write_json_array(run_dir / "model_manifest.json", [model_manifest_record(label)])
    write_json_array(run_dir / "tuning_log.json", [tuning_log_record(label)])
    write_json_array(run_dir / "evaluation_metrics.json", [metric_record(label)])
    write_json_array(run_dir / "backtest_results.json", [backtest_record(label)])


def test_audit_run_passes_complete_exploratory_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "audit_test_run"
    write_complete_audit_artifacts(run_dir)

    report = audit_run(run_id="audit_test_run", run_dir=run_dir)

    assert report.audit_status == "pass"
    assert report.coverage == 1.0
    assert report.formal_result_allowed is False
    assert (run_dir / "audit_report.json").exists()
    status = json.loads((run_dir / "run_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "audited"
    assert status["audit_status"] == "pass"


def test_audit_run_rejects_missing_prediction_alignment(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "audit_test_run"
    write_complete_audit_artifacts(run_dir, bad_prediction_label=True)

    report = audit_run(run_id="audit_test_run", run_dir=run_dir)

    assert report.audit_status == "fail"
    assert report.coverage == 0.0
    assert any(check.check_id == "prediction_label_alignment" for check in report.checks)
    status = json.loads((run_dir / "run_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "rejected"


def test_audit_cli_writes_report(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    run_dir = tmp_path / "runs" / "audit_test_run"
    write_complete_audit_artifacts(run_dir)

    exit_code = main(["audit", "--run-id", "audit_test_run", "--run-dir", str(run_dir)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Audit completed" in captured.out
    assert "status=pass" in captured.out
