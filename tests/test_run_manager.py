from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml

from text_factor_lab.orchestration import RunManager
from text_factor_lab.schemas import (
    DocumentManifestRecord,
    FeatureRecord,
    LabelRecord,
    SplitAssignmentRecord,
)

SPLIT_ID = "train_2010_2014__val_2015_2015__test_2016_2016"


def write_temp_config(source_config: Path, tmp_path: Path) -> Path:
    payload = yaml.safe_load(source_config.read_text(encoding="utf-8"))
    payload["run"]["run_id"] = "test_run_001"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "test_run_001")
    payload["models"]["enabled"] = ["historical_mean", "ridge"]
    payload["audit"]["coverage_threshold"] = 0.6

    config_path = tmp_path / "mvp_v0_test.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def label(document_id: str, ticker: str, year: int, value: float) -> LabelRecord:
    return LabelRecord(
        label_id=f"{document_id}:CAR_1_20:labels-v0",
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        event_time_utc=utc(year, 3, 1),
        prediction_time_utc=utc(year, 3, 1),
        label_start_date=date(year, 3, 2),
        label_end_date=date(year, 3, 31),
        target_name="CAR_1_20",
        target_value=value,
        benchmark_method="SPY",
        return_type="log",
        adjustment_method="adj_close",
        label_version="labels-v0",
    )


def assignment(label_record: LabelRecord, role: str) -> SplitAssignmentRecord:
    return SplitAssignmentRecord(
        split_id=SPLIT_ID,
        label_id=label_record.label_id,
        entity_id=label_record.entity_id,
        ticker=label_record.ticker,
        target_name=label_record.target_name,
        role=role,
        event_date=label_record.event_time_utc.date(),
        label_start_date=label_record.label_start_date,
        label_end_date=label_record.label_end_date,
        train_start_date=date(2010, 1, 1),
        train_end_date=date(2014, 12, 31),
        validation_start_date=date(2015, 1, 1),
        validation_end_date=date(2015, 12, 31),
        test_start_date=date(2016, 1, 1),
        test_end_date=date(2016, 12, 31),
        embargo_days=20,
        split_version="rolling-year-split-v0",
    )


def feature(document_id: str, ticker: str, year: int, role: str, value: float) -> FeatureRecord:
    return FeatureRecord(
        feature_id=f"{document_id}:tfidf-v0:{role}:risk",
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        event_time_utc=utc(year, 3, 1),
        prediction_time_utc=utc(year, 3, 1),
        feature_time_utc=utc(year, 3, 1),
        feature_family="tfidf",
        feature_name="tfidf_item_1a__risk",
        feature_value=value,
        feature_version=f"tfidf-v0:{SPLIT_ID}:item_1a:{role}",
        source_document_id=document_id,
        source_chunk_id=f"{document_id}:item_1a",
    )


def manifest(document_id: str, ticker: str, year: int, source_path: Path) -> DocumentManifestRecord:
    return DocumentManifestRecord(
        document_id=document_id,
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        cik="0000000001",
        company_name=f"{ticker} Inc.",
        document_type="10-K",
        fiscal_year=year,
        fiscal_period="FY",
        source_id="SEC_EDGAR",
        source_url_or_path=str(source_path),
        retrieval_time_utc=utc(year, 3, 1),
        available_time_utc=utc(year, 3, 1),
        event_time_utc=utc(year, 3, 1),
        event_date=date(year, 3, 1),
        timezone="America/New_York",
        hash_sha256="a" * 64,
        license_note="Public SEC EDGAR filing; comply with SEC fair-access policy.",
        parser_version="sec-edgar-data-v0",
    )


def write_jsonl(path: Path, records: list) -> None:
    path.write_text(
        "".join(record.model_dump_json() + "\n" for record in records),
        encoding="utf-8",
    )


def write_json_array(path: Path, records: list) -> None:
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def write_midstream_artifacts(run_dir: Path) -> None:
    rows = [
        ("sec:train:a", "AAA", 2014, "train", 0.0, 0.0),
        ("sec:train:b", "BBB", 2014, "train", 1.0, 1.0),
        ("sec:val:a", "CCC", 2015, "validation", 0.2, 0.25),
        ("sec:val:b", "DDD", 2015, "validation", 0.8, 0.75),
        ("sec:test:a", "EEE", 2016, "test", 0.1, 0.2),
        ("sec:test:b", "FFF", 2016, "test", 0.9, 0.8),
    ]
    labels = [
        label(document_id, ticker, year, target)
        for document_id, ticker, year, _, target, _ in rows
    ]
    labels_by_document = {record.label_id.rsplit(":", 2)[0]: record for record in labels}
    assignments = [
        assignment(labels_by_document[document_id], role)
        for document_id, _, _, role, _, _ in rows
    ]
    features = [
        feature(document_id, ticker, year, role, signal)
        for document_id, ticker, year, role, _, signal in rows
    ]

    run_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(run_dir / "document_manifest.jsonl", [])
    write_jsonl(run_dir / "labels.jsonl", labels)
    write_jsonl(run_dir / "split_assignments.jsonl", assignments)
    write_jsonl(run_dir / "split_leakage.jsonl", [])
    write_jsonl(run_dir / "features.jsonl", features)
    write_json_array(run_dir / "feature_manifest.json", [])
    write_json_array(run_dir / "vocabulary.json", {})


def write_parse_ready_artifacts(run_dir: Path, raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "sample_10k.html"
    raw_file.write_text(
        Path("tests/fixtures/sec_10k_sample_with_toc.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    rows = [
        ("sec:train:a", "AAA", 2014, "train", 0.0),
        ("sec:train:b", "BBB", 2014, "train", 1.0),
        ("sec:val:a", "CCC", 2015, "validation", 0.2),
        ("sec:val:b", "DDD", 2015, "validation", 0.8),
        ("sec:test:a", "EEE", 2016, "test", 0.1),
        ("sec:test:b", "FFF", 2016, "test", 0.9),
    ]
    labels = [
        label(document_id, ticker, year, target)
        for document_id, ticker, year, _, target in rows
    ]
    labels_by_document = {record.label_id.rsplit(":", 2)[0]: record for record in labels}
    assignments = [
        assignment(labels_by_document[document_id], role)
        for document_id, _, _, role, _ in rows
    ]
    manifests = [
        manifest(document_id, ticker, year, raw_file)
        for document_id, ticker, year, _, _ in rows
    ]
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_source = run_dir.parent / "configured_document_manifest.jsonl"
    write_jsonl(manifest_source, manifests)
    write_jsonl(run_dir / "labels.jsonl", labels)
    write_jsonl(run_dir / "split_assignments.jsonl", assignments)
    write_jsonl(run_dir / "split_leakage.jsonl", [])
    return manifest_source


@pytest.fixture
def temp_config(tmp_path: Path) -> Path:
    return write_temp_config(Path("configs/text_factor_lab/mvp_v0.yaml"), tmp_path)


def test_initialize_run_creates_status_and_config_snapshot(temp_config: Path) -> None:
    manager = RunManager.from_config_path(temp_config)
    status = manager.initialize_run()

    assert status.run_id == "test_run_001"
    assert status.status == "created"
    assert status.audit_status == "not_run"
    assert status.coverage == 0
    assert manager.status_path.exists()
    assert manager.config_snapshot_path.exists()
    assert manager.pipeline_contract_path.exists()

    saved_payload = json.loads(manager.status_path.read_text(encoding="utf-8"))
    assert saved_payload["run_id"] == "test_run_001"
    assert saved_payload["status"] == "created"

    pipeline_payload = json.loads(manager.pipeline_contract_path.read_text(encoding="utf-8"))
    assert pipeline_payload["current_scope"] == "complete_local_mvp_orchestrator"
    assert "inputs.raw_filings_dir" in pipeline_payload["artifact_aware_orchestrator"][
        "configured_input_paths"
    ]


def test_update_status_persists_state(temp_config: Path) -> None:
    manager = RunManager.from_config_path(temp_config)
    manager.initialize_run()

    status = manager.update_status("data_ready", coverage=0.81)

    assert status.status == "data_ready"
    assert status.coverage == 0.81
    assert manager.read_status().status == "data_ready"


def test_fail_run_writes_failure_log(temp_config: Path) -> None:
    manager = RunManager.from_config_path(temp_config)
    manager.initialize_run()

    status = manager.fail_run(
        stage="data",
        failure_type="data_missing",
        failure_message="Missing SEC filing",
        affected_artifacts=["document_manifest.parquet"],
        recoverable=True,
        recommended_action="Retry data acquisition",
    )

    assert status.status == "failed"
    assert status.audit_status == "fail"
    assert status.failure_reason == "Missing SEC filing"

    lines = manager.failure_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["failure_type"] == "data_missing"
    assert record["status_before_failure"] == "created"


def test_fail_run_can_reject_run(temp_config: Path) -> None:
    manager = RunManager.from_config_path(temp_config)
    manager.initialize_run()

    status = manager.fail_run(
        stage="audit",
        failure_type="lookahead_bias_detected",
        failure_message="Feature timestamp is after prediction timestamp",
        recoverable=False,
        recommended_action="Remove leaked feature rows",
        rejected=True,
    )

    assert status.status == "rejected"


def test_formal_run_rejects_demo_universe(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        Path("configs/text_factor_lab/mvp_v0.yaml").read_text(encoding="utf-8")
    )
    payload["run"]["run_id"] = "formal_demo_universe"
    payload["run"]["run_type"] = "formal_run"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "formal_demo_universe")
    config_path = tmp_path / "formal_config.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    manager = RunManager.from_config_path(config_path)
    status = manager.initialize_run()

    assert status.status == "rejected"
    assert status.audit_status == "fail"
    assert "universe manifest is not research-grade" in (status.failure_reason or "")


def test_run_pipeline_executes_available_artifact_chain(temp_config: Path) -> None:
    manager = RunManager.from_config_path(temp_config)
    write_midstream_artifacts(manager.run_dir)
    manager.initialize_run()

    report = manager.run_pipeline()

    assert report["blocked_reason"] is None
    assert manager.read_status().status == "reported"
    assert manager.predictions_path.exists()
    assert manager.evaluation_metrics_path.exists()
    assert manager.audit_report_path.exists()
    assert (manager.run_dir / "report.md").exists()
    stages = {stage["stage"]: stage["status"] for stage in report["stages"]}
    assert stages["labels"] == "skipped_existing"
    assert stages["models"] == "completed"
    assert stages["report"] == "completed"


def test_run_pipeline_records_blocked_stage_when_inputs_are_missing(
    temp_config: Path,
) -> None:
    manager = RunManager.from_config_path(temp_config)
    manager.initialize_run()

    report = manager.run_pipeline()

    assert report["blocked_reason"] == "labels_not_ready"
    assert manager.orchestrator_report_path.exists()
    assert report["stages"][0]["stage"] == "labels"
    assert report["stages"][0]["status"] == "blocked_missing_inputs"


def test_run_pipeline_copies_inputs_and_parses_raw_filings(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        Path("configs/text_factor_lab/mvp_v0.yaml").read_text(encoding="utf-8")
    )
    payload["run"]["run_id"] = "test_run_parse_inputs"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "test_run_parse_inputs")
    payload["models"]["enabled"] = ["historical_mean", "ridge"]
    payload["audit"]["coverage_threshold"] = 0.6
    payload["features"]["tfidf"]["min_df"] = 1
    payload["features"]["tfidf"]["max_df"] = 1.0

    run_dir = Path(payload["run"]["output_dir"])
    raw_dir = tmp_path / "raw_filings"
    manifest_source = write_parse_ready_artifacts(run_dir, raw_dir)
    payload["inputs"]["document_manifest_path"] = str(manifest_source)
    payload["inputs"]["raw_filings_dir"] = str(raw_dir)

    config_path = tmp_path / "parse_inputs.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    manager = RunManager.from_config_path(config_path)
    manager.initialize_run()

    report = manager.run_pipeline()

    assert report["blocked_reason"] is None
    assert manager.document_manifest_path.exists()
    assert manager.parsed_sections_path.exists()
    assert manager.parsing_quality_report_path.exists()
    assert manager.features_path.exists()
    assert manager.read_status().status == "reported"
    stages = {stage["stage"]: stage["status"] for stage in report["stages"]}
    assert stages["prepare_inputs"] == "completed"
    assert stages["parsing"] == "completed"

