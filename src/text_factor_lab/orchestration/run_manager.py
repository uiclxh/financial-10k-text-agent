from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from text_factor_lab.data import load_and_report_universe
from text_factor_lab.schemas.base import StrictBaseModel
from text_factor_lab.schemas.config import ExperimentConfig, load_experiment_config
from text_factor_lab.schemas.run_status import AuditStatus, RunStatus, RunStatusRecord

FailureType = Literal[
    "data_missing",
    "license_missing",
    "timestamp_missing",
    "schema_validation_failed",
    "coverage_below_threshold",
    "parser_failed",
    "label_window_unavailable",
    "train_test_leakage",
    "lookahead_bias_detected",
    "model_training_failed",
    "metric_computation_failed",
    "audit_failed",
    "orchestrator_failed",
]


class FailureLogRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    status_before_failure: str = Field(min_length=1)
    failure_type: FailureType
    failure_message: str = Field(min_length=1)
    affected_artifacts: list[str]
    recoverable: bool
    recommended_action: str = Field(min_length=1)
    created_at_utc: datetime


class RunManager:
    """Creates run artifacts and owns run status transitions."""

    def __init__(self, config: ExperimentConfig, config_path: Path) -> None:
        self.config = config
        self.config_path = config_path
        self.run_dir = Path(config.run.output_dir)
        self.status_path = self.run_dir / "run_status.json"
        self.failure_log_path = self.run_dir / "failure_log.jsonl"
        self.config_snapshot_path = self.run_dir / "config_snapshot.yaml"
        self.universe_quality_report_path = self.run_dir / "universe_quality_report.json"
        self.pipeline_contract_path = self.run_dir / "pipeline_contract.json"

    @classmethod
    def from_config_path(cls, config_path: str | Path) -> RunManager:
        resolved_config_path = Path(config_path)
        config = load_experiment_config(resolved_config_path)
        return cls(config=config, config_path=resolved_config_path)

    def initialize_run(self) -> RunStatusRecord:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.config_path, self.config_snapshot_path)

        now = datetime.now(UTC)
        status = RunStatusRecord(
            run_id=self.config.run.run_id,
            run_type=self.config.run.run_type,
            status="created",
            created_at_utc=now,
            updated_at_utc=now,
            config_path=str(self.config_snapshot_path),
            failure_reason=None,
            audit_status="not_run",
            coverage=0.0,
        )
        self.write_status(status)
        self.write_pipeline_contract()
        try:
            universe_report = self.write_universe_quality_report()
            if self.config.run.run_type == "formal_run" and universe_report.formal_run_blockers:
                self.fail_run(
                    stage="universe",
                    failure_type="coverage_below_threshold",
                    failure_message=(
                        "Formal run rejected because universe manifest is not research-grade: "
                        + ", ".join(universe_report.formal_run_blockers)
                    ),
                    affected_artifacts=[str(self.config.universe.tickers_file)],
                    recoverable=True,
                    recommended_action=(
                        "Replace demo universe with a dated, research-grade large-cap "
                        "universe including market cap, mapping source, and delisted firms."
                    ),
                    rejected=True,
                )
        except Exception as exc:
            self.fail_run(
                stage="universe",
                failure_type="schema_validation_failed",
                failure_message=f"Universe validation failed: {exc}",
                affected_artifacts=[str(self.config.universe.tickers_file)],
                recoverable=True,
                recommended_action="Fix universe manifest rows and rerun.",
            )
            raise
        return self.read_status()

    def write_universe_quality_report(self):
        _, report = load_and_report_universe(self.config)
        with self.universe_quality_report_path.open("w", encoding="utf-8") as file:
            json.dump(report.model_dump(mode="json"), file, indent=2)
            file.write("\n")
        return report

    def write_pipeline_contract(self) -> None:
        payload = {
            "run_id": self.config.run.run_id,
            "current_scope": "run_manager_plus_independent_cli_tools",
            "implemented_cli_stages": [
                "run",
                "parse-10k",
                "build-labels",
                "build-splits",
                "build-features",
                "build-models",
                "evaluate-models",
            ],
            "full_orchestrator_sequence": [
                "Data",
                "Parsing",
                "Label",
                "Split",
                "Feature",
                "Model",
                "Backtest",
                "Audit",
                "Report",
            ],
            "orchestrator_status": "not_yet_full_pipeline_controller",
        }
        with self.pipeline_contract_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")

    def read_status(self) -> RunStatusRecord:
        with self.status_path.open("r", encoding="utf-8") as file:
            return RunStatusRecord.model_validate(json.load(file))

    def write_status(self, status: RunStatusRecord) -> None:
        with self.status_path.open("w", encoding="utf-8") as file:
            json.dump(status.model_dump(mode="json"), file, indent=2)
            file.write("\n")

    def update_status(
        self,
        status: RunStatus,
        *,
        audit_status: AuditStatus | None = None,
        coverage: float | None = None,
        failure_reason: str | None = None,
    ) -> RunStatusRecord:
        current = self.read_status()
        updated = current.model_copy(
            update={
                "status": status,
                "updated_at_utc": datetime.now(UTC),
                "audit_status": audit_status if audit_status is not None else current.audit_status,
                "coverage": coverage if coverage is not None else current.coverage,
                "failure_reason": failure_reason,
            }
        )
        self.write_status(updated)
        return updated

    def log_failure(
        self,
        *,
        stage: str,
        failure_type: FailureType,
        failure_message: str,
        affected_artifacts: list[str] | None = None,
        recoverable: bool,
        recommended_action: str,
    ) -> FailureLogRecord:
        current = self.read_status()
        record = FailureLogRecord(
            run_id=self.config.run.run_id,
            stage=stage,
            status_before_failure=current.status,
            failure_type=failure_type,
            failure_message=failure_message,
            affected_artifacts=affected_artifacts or [],
            recoverable=recoverable,
            recommended_action=recommended_action,
            created_at_utc=datetime.now(UTC),
        )
        with self.failure_log_path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json())
            file.write("\n")
        return record

    def fail_run(
        self,
        *,
        stage: str,
        failure_type: FailureType,
        failure_message: str,
        affected_artifacts: list[str] | None = None,
        recoverable: bool,
        recommended_action: str,
        rejected: bool = False,
    ) -> RunStatusRecord:
        self.log_failure(
            stage=stage,
            failure_type=failure_type,
            failure_message=failure_message,
            affected_artifacts=affected_artifacts,
            recoverable=recoverable,
            recommended_action=recommended_action,
        )
        return self.update_status(
            "rejected" if rejected else "failed",
            audit_status="fail",
            failure_reason=failure_message,
        )


def initialize_run_from_config(config_path: str | Path) -> RunStatusRecord:
    manager = RunManager.from_config_path(config_path)
    return manager.initialize_run()
