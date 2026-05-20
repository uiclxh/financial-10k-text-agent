from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from text_factor_lab.orchestration import RunManager


def write_temp_config(source_config: Path, tmp_path: Path) -> Path:
    payload = yaml.safe_load(source_config.read_text(encoding="utf-8"))
    payload["run"]["run_id"] = "test_run_001"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "test_run_001")

    config_path = tmp_path / "mvp_v0_test.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path


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
    assert pipeline_payload["current_scope"] == "run_manager_plus_independent_cli_tools"


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


