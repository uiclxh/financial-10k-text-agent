from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

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
        self.orchestrator_report_path = self.run_dir / "orchestrator_report.json"
        self.document_manifest_path = self.run_dir / "document_manifest.jsonl"
        self.prices_path = self.run_dir / "prices.csv"
        self.parsed_sections_path = self.run_dir / "parsed_sections.jsonl"
        self.labels_path = self.run_dir / "labels.jsonl"
        self.label_failures_path = self.run_dir / "label_failures.jsonl"
        self.split_assignments_path = self.run_dir / "split_assignments.jsonl"
        self.split_leakage_path = self.run_dir / "split_leakage.jsonl"
        self.features_path = self.run_dir / "features.jsonl"
        self.vocabulary_path = self.run_dir / "vocabulary.json"
        self.feature_manifest_path = self.run_dir / "feature_manifest.json"
        self.predictions_path = self.run_dir / "predictions.jsonl"
        self.model_manifest_path = self.run_dir / "model_manifest.json"
        self.tuning_log_path = self.run_dir / "tuning_log.json"
        self.evaluation_metrics_path = self.run_dir / "evaluation_metrics.json"
        self.backtest_results_path = self.run_dir / "backtest_results.json"
        self.audit_report_path = self.run_dir / "audit_report.json"
        self.parsing_quality_report_path = self.run_dir / "parsing_quality_report.json"

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
            "current_scope": "complete_local_mvp_orchestrator",
            "implemented_cli_stages": [
                "run",
                "parse-10k",
                "build-labels",
                "build-splits",
                "build-features",
                "build-models",
                "evaluate-models",
                "audit",
                "report",
            ],
            "artifact_aware_orchestrator": {
                "enabled": True,
                "entrypoint": "python -m text_factor_lab run --config <config> --execute",
                "configured_input_paths": [
                    "inputs.document_manifest_path",
                    "inputs.prices_path",
                    "inputs.parsed_sections_path",
                    "inputs.raw_filings_dir",
                ],
                "standard_run_dir_inputs": [
                    "document_manifest.jsonl",
                    "prices.csv",
                    "parsed_sections.jsonl",
                    "labels.jsonl",
                    "split_assignments.jsonl",
                    "features.jsonl",
                ],
            },
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
            "orchestrator_status": "artifact_aware_pipeline_controller",
        }
        with self.pipeline_contract_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")

    def run_pipeline(self, *, allow_failed_audit_report: bool = False) -> dict[str, Any]:
        """Run available pipeline stages using standard files in the run directory.

        This controller is intentionally artifact-aware: it can continue from
        pre-built upstream files and records a blocked stage instead of inventing
        missing licensed or large data inputs.
        """

        if not self.status_path.exists():
            self.initialize_run()
        records: list[dict[str, Any]] = []
        try:
            current = self.read_status()
            if current.status in {"failed", "rejected"}:
                return self.write_orchestrator_report(
                    records,
                    final_status=current.status,
                    blocked_reason=current.failure_reason,
                )

            if not self._prepare_configured_inputs(records):
                return self.write_orchestrator_report(records, blocked_reason="inputs_not_ready")
            if not self._run_label_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="labels_not_ready")
            if not self._run_split_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="splits_not_ready")
            if not self._run_parsing_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="parsing_not_ready")
            if not self._run_feature_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="features_not_ready")
            if not self._run_model_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="models_not_ready")
            if not self._run_evaluation_stage(records):
                return self.write_orchestrator_report(
                    records,
                    blocked_reason="evaluation_not_ready",
                )
            if not self._run_audit_stage(records):
                return self.write_orchestrator_report(records, blocked_reason="audit_not_ready")
            self._run_report_stage(records, allow_failed_audit_report=allow_failed_audit_report)
            return self.write_orchestrator_report(records)
        except Exception as exc:
            self.fail_run(
                stage="orchestrator",
                failure_type="orchestrator_failed",
                failure_message=str(exc),
                affected_artifacts=[str(self.run_dir)],
                recoverable=True,
                recommended_action="Inspect orchestrator_report.json and rerun the failed stage.",
            )
            self._append_stage(
                records,
                stage="orchestrator",
                status="failed",
                message=str(exc),
            )
            return self.write_orchestrator_report(records, blocked_reason=str(exc))

    def write_orchestrator_report(
        self,
        stages: list[dict[str, Any]],
        *,
        final_status: str | None = None,
        blocked_reason: str | None = None,
    ) -> dict[str, Any]:
        status = self.read_status()
        payload = {
            "run_id": self.config.run.run_id,
            "orchestrator_version": "artifact-aware-orchestrator-v1",
            "final_run_status": final_status or status.status,
            "blocked_reason": blocked_reason,
            "stage_count": len(stages),
            "stages": stages,
            "created_at_utc": datetime.now(UTC).isoformat(),
        }
        with self.orchestrator_report_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")
        return payload

    def _prepare_configured_inputs(self, records: list[dict[str, Any]]) -> bool:
        copied: list[Path] = []
        skipped: list[Path] = []
        mappings = [
            (self.config.inputs.document_manifest_path, self.document_manifest_path),
            (self.config.inputs.prices_path, self.prices_path),
            (self.config.inputs.parsed_sections_path, self.parsed_sections_path),
        ]
        for source, destination in mappings:
            if source is None:
                continue
            source_path = Path(source)
            if not source_path.exists():
                self._append_stage(
                    records,
                    stage="prepare_inputs",
                    status="blocked_missing_inputs",
                    inputs=[source_path],
                    message=f"Configured input does not exist: {source_path}",
                )
                return False
            if destination.exists():
                skipped.append(destination)
                continue
            if not self.config.inputs.copy_inputs_to_run_dir:
                skipped.append(source_path)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source_path.resolve() != destination.resolve():
                shutil.copy2(source_path, destination)
            copied.append(destination)

        if copied or skipped or self.config.inputs.raw_filings_dir is not None:
            self._append_stage(
                records,
                stage="prepare_inputs",
                status="completed",
                inputs=[Path(path) for path, _ in mappings if path is not None],
                outputs=copied,
                metrics={
                    "copied": len(copied),
                    "skipped_existing_or_external": len(skipped),
                    "raw_filings_dir": (
                        str(self.config.inputs.raw_filings_dir)
                        if self.config.inputs.raw_filings_dir is not None
                        else None
                    ),
                },
            )
        return True

    def _run_label_stage(self, records: list[dict[str, Any]]) -> bool:
        if self.labels_path.exists():
            self.update_status("labels_ready")
            self._append_stage(records, stage="labels", status="skipped_existing")
            return True
        if not self._inputs_exist(self.document_manifest_path, self.prices_path):
            self._append_stage(
                records,
                stage="labels",
                status="blocked_missing_inputs",
                inputs=[self.document_manifest_path, self.prices_path],
            )
            return False

        from text_factor_lab.data import load_price_panel_csv
        from text_factor_lab.labels import (
            build_labels_for_documents,
            read_document_manifest_jsonl,
            write_label_artifacts,
        )

        documents = read_document_manifest_jsonl(self.document_manifest_path)
        price_panel = load_price_panel_csv(
            self.prices_path,
            price_field=self.config.labels.price_field,
        )
        result = build_labels_for_documents(
            documents=documents,
            price_panel=price_panel,
            target_names=self.config.labels.targets,
            benchmark_ticker=self.config.labels.market_benchmark,
            return_type=self.config.labels.return_type,
            adjustment_method=self.config.labels.price_field,
            annualization_days=self.config.labels.annualization_days,
        )
        write_label_artifacts(
            result,
            labels_path=self.labels_path,
            failures_path=self.label_failures_path,
        )
        self.update_status("labels_ready")
        self._append_stage(
            records,
            stage="labels",
            status="completed",
            outputs=[self.labels_path, self.label_failures_path],
            metrics={"labels": len(result.labels), "failures": len(result.failures)},
        )
        return True

    def _run_split_stage(self, records: list[dict[str, Any]]) -> bool:
        if self.split_assignments_path.exists():
            self._append_stage(records, stage="splits", status="skipped_existing")
            return True
        if not self._inputs_exist(self.labels_path):
            self._append_stage(
                records,
                stage="splits",
                status="blocked_missing_inputs",
                inputs=[self.labels_path],
            )
            return False

        from text_factor_lab.splits import (
            build_rolling_year_splits,
            read_labels_jsonl,
            write_split_artifacts,
        )

        result = build_rolling_year_splits(
            labels=read_labels_jsonl(self.labels_path),
            sample_start=self.config.sample.start_date,
            sample_end=self.config.sample.end_date,
            train_years_min=self.config.split.train_years_min,
            validation_years=self.config.split.validation_years,
            test_years=self.config.split.test_years,
            embargo_days=self.config.split.embargo_days,
        )
        write_split_artifacts(
            result,
            assignments_path=self.split_assignments_path,
            leakage_path=self.split_leakage_path,
        )
        self._append_stage(
            records,
            stage="splits",
            status="completed",
            outputs=[self.split_assignments_path, self.split_leakage_path],
            metrics={
                "assignments": len(result.assignments),
                "leakage_records": len(result.leakage_records),
            },
        )
        return True

    def _run_parsing_stage(self, records: list[dict[str, Any]]) -> bool:
        if self.parsed_sections_path.exists():
            self.update_status("parsed")
            self._append_stage(records, stage="parsing", status="skipped_existing")
            return True
        if self.features_path.exists() and self.feature_manifest_path.exists():
            self._append_stage(
                records,
                stage="parsing",
                status="skipped_existing_downstream_features",
                message="features already exist, so parsing is not required for this run",
            )
            return True
        if not self.document_manifest_path.exists():
            self._append_stage(
                records,
                stage="parsing",
                status="blocked_missing_inputs",
                inputs=[self.document_manifest_path],
            )
            return False
        if self.config.inputs.raw_filings_dir is None:
            self._append_stage(
                records,
                stage="parsing",
                status="blocked_missing_inputs",
                inputs=[self.document_manifest_path],
                message="raw_filings_dir is required when parsed_sections.jsonl is absent",
            )
            return False
        raw_filings_dir = Path(self.config.inputs.raw_filings_dir)
        if not raw_filings_dir.exists():
            self._append_stage(
                records,
                stage="parsing",
                status="blocked_missing_inputs",
                inputs=[raw_filings_dir],
                message=f"raw_filings_dir does not exist: {raw_filings_dir}",
            )
            return False

        from text_factor_lab.features import read_document_manifest_jsonl
        from text_factor_lab.parsing import parse_sec_10k_sections, write_section_artifacts

        manifests = read_document_manifest_jsonl(self.document_manifest_path)
        parsed_records = []
        missing_documents: list[str] = []
        parsed_output_root = self.run_dir / "parsed_documents"
        for manifest in manifests.values():
            raw_path = self._resolve_raw_filing_path(manifest.source_url_or_path, raw_filings_dir)
            if raw_path is None:
                missing_documents.append(manifest.document_id)
                continue
            result = parse_sec_10k_sections(raw_path.read_bytes(), manifest)
            document_output_dir = (
                parsed_output_root / self._safe_artifact_name(manifest.document_id)
            )
            parsed_records.extend(write_section_artifacts(result, document_output_dir))

        with self.parsed_sections_path.open("w", encoding="utf-8") as file:
            for record in parsed_records:
                file.write(record.model_dump_json())
                file.write("\n")
        quality_payload = {
            "documents_total": len(manifests),
            "documents_missing_raw": len(missing_documents),
            "parsed_section_records": len(parsed_records),
            "missing_document_ids": missing_documents,
            "created_at_utc": datetime.now(UTC).isoformat(),
        }
        with self.parsing_quality_report_path.open("w", encoding="utf-8") as file:
            json.dump(quality_payload, file, indent=2)
            file.write("\n")
        self.update_status("parsed")
        self._append_stage(
            records,
            stage="parsing",
            status="completed" if not missing_documents else "completed_with_warnings",
            inputs=[self.document_manifest_path, raw_filings_dir],
            outputs=[self.parsed_sections_path, self.parsing_quality_report_path],
            metrics=quality_payload,
        )
        return bool(parsed_records)

    def _run_feature_stage(self, records: list[dict[str, Any]]) -> bool:
        if self.features_path.exists() and self.feature_manifest_path.exists():
            self.update_status("features_ready")
            self._append_stage(records, stage="features", status="skipped_existing")
            return True
        if not self._inputs_exist(
            self.document_manifest_path,
            self.parsed_sections_path,
            self.split_assignments_path,
        ):
            self._append_stage(
                records,
                stage="features",
                status="blocked_missing_inputs",
                inputs=[
                    self.document_manifest_path,
                    self.parsed_sections_path,
                    self.split_assignments_path,
                ],
            )
            return False

        from text_factor_lab.features import (
            build_dictionary_feature_manifests,
            build_dictionary_tone_features,
            build_feature_input_hashes,
            build_tfidf_features,
            load_document_texts,
            read_document_manifest_jsonl,
            read_parsed_sections_jsonl,
            read_split_assignments_jsonl,
            write_feature_manifest_json,
            write_features_jsonl,
            write_vocabulary_json,
        )

        manifest_by_document_id = read_document_manifest_jsonl(self.document_manifest_path)
        parsed_sections = read_parsed_sections_jsonl(self.parsed_sections_path)
        split_assignments = read_split_assignments_jsonl(self.split_assignments_path)
        document_texts = load_document_texts(
            manifest_by_document_id=manifest_by_document_id,
            parsed_sections=parsed_sections,
        )
        input_hashes = build_feature_input_hashes(
            document_manifest_path=self.document_manifest_path,
            parsed_sections_path=self.parsed_sections_path,
            split_assignments_path=self.split_assignments_path,
        )
        features = []
        feature_manifests = []
        vocabulary_by_split = {}
        if "dictionary_tone" in self.config.features.methods:
            features.extend(build_dictionary_tone_features(document_texts))
            feature_manifests.extend(
                build_dictionary_feature_manifests(
                    document_texts,
                    split_assignments,
                    input_hashes=input_hashes,
                )
            )
        if "tfidf" in self.config.features.methods and self.config.features.tfidf is not None:
            tfidf_config = self.config.features.tfidf
            tfidf_result = build_tfidf_features(
                document_texts,
                split_assignments,
                max_features=tfidf_config.max_features,
                ngram_range=tfidf_config.ngram_range,
                min_df=tfidf_config.min_df,
                max_df=tfidf_config.max_df,
                input_hashes=input_hashes,
            )
            features.extend(tfidf_result.features)
            feature_manifests.extend(tfidf_result.feature_manifests)
            vocabulary_by_split = tfidf_result.vocabulary_by_split
        write_features_jsonl(features, self.features_path)
        write_vocabulary_json(vocabulary_by_split, self.vocabulary_path)
        write_feature_manifest_json(feature_manifests, self.feature_manifest_path)
        self.update_status("features_ready")
        self._append_stage(
            records,
            stage="features",
            status="completed",
            outputs=[self.features_path, self.vocabulary_path, self.feature_manifest_path],
            metrics={"features": len(features), "feature_manifests": len(feature_manifests)},
        )
        return True

    def _run_model_stage(self, records: list[dict[str, Any]]) -> bool:
        if (
            self.predictions_path.exists()
            and self.model_manifest_path.exists()
            and self.tuning_log_path.exists()
        ):
            self.update_status("trained")
            self._append_stage(records, stage="models", status="skipped_existing")
            return True
        if not self._inputs_exist(
            self.labels_path,
            self.features_path,
            self.split_assignments_path,
        ):
            self._append_stage(
                records,
                stage="models",
                status="blocked_missing_inputs",
                inputs=[self.labels_path, self.features_path, self.split_assignments_path],
            )
            return False

        from text_factor_lab.models import (
            build_model_artifacts,
            read_features_jsonl,
            read_labels_jsonl,
            read_split_assignments_jsonl,
            write_model_manifest_json,
            write_predictions_jsonl,
            write_tuning_log_json,
        )

        result = build_model_artifacts(
            run_id=self.config.run.run_id,
            labels=read_labels_jsonl(self.labels_path),
            features=read_features_jsonl(self.features_path),
            split_assignments=read_split_assignments_jsonl(self.split_assignments_path),
            models=self.config.models.enabled,
            random_seed=self.config.run.random_seed,
        )
        write_predictions_jsonl(result.predictions, self.predictions_path)
        write_model_manifest_json(result.model_manifests, self.model_manifest_path)
        write_tuning_log_json(result.tuning_logs, self.tuning_log_path)
        self.update_status("trained")
        self._append_stage(
            records,
            stage="models",
            status="completed",
            outputs=[self.predictions_path, self.model_manifest_path, self.tuning_log_path],
            metrics={
                "predictions": len(result.predictions),
                "model_manifests": len(result.model_manifests),
            },
        )
        return True

    def _run_evaluation_stage(self, records: list[dict[str, Any]]) -> bool:
        if self.evaluation_metrics_path.exists() and self.backtest_results_path.exists():
            self.update_status("evaluated")
            self._append_stage(records, stage="evaluation", status="skipped_existing")
            return True
        if not self._inputs_exist(self.predictions_path, self.labels_path):
            self._append_stage(
                records,
                stage="evaluation",
                status="blocked_missing_inputs",
                inputs=[self.predictions_path, self.labels_path],
            )
            return False

        from text_factor_lab.backtest import (
            build_evaluation_artifacts,
            read_labels_jsonl,
            read_predictions_jsonl,
            write_backtest_results_json,
            write_evaluation_metrics_json,
        )

        result = build_evaluation_artifacts(
            run_id=self.config.run.run_id,
            predictions=read_predictions_jsonl(self.predictions_path),
            labels=read_labels_jsonl(self.labels_path),
            transaction_cost_bps_one_way=self.config.backtest.transaction_cost_bps_one_way,
            newey_west_lag=self.config.backtest.newey_west_lag,
        )
        write_evaluation_metrics_json(result.metrics, self.evaluation_metrics_path)
        write_backtest_results_json(result.backtests, self.backtest_results_path)
        self.update_status("evaluated")
        self._append_stage(
            records,
            stage="evaluation",
            status="completed",
            outputs=[self.evaluation_metrics_path, self.backtest_results_path],
            metrics={"metrics": len(result.metrics), "backtests": len(result.backtests)},
        )
        return True

    def _run_audit_stage(self, records: list[dict[str, Any]]) -> bool:
        audit_inputs = [
            self.document_manifest_path,
            self.labels_path,
            self.split_leakage_path,
            self.features_path,
            self.feature_manifest_path,
            self.vocabulary_path,
            self.predictions_path,
            self.model_manifest_path,
            self.tuning_log_path,
            self.evaluation_metrics_path,
            self.backtest_results_path,
        ]
        if not self._inputs_exist(*audit_inputs):
            self._append_stage(
                records,
                stage="audit",
                status="blocked_missing_inputs",
                inputs=audit_inputs,
            )
            return False

        from text_factor_lab.audit import audit_run

        report = audit_run(
            run_id=self.config.run.run_id,
            run_dir=self.run_dir,
            config_path=self.config_snapshot_path,
            coverage_threshold=self.config.audit.coverage_threshold,
        )
        self._append_stage(
            records,
            stage="audit",
            status="completed",
            outputs=[self.audit_report_path],
            metrics={
                "audit_status": report.audit_status,
                "failures": report.fail_count,
                "warnings": report.warn_count,
            },
        )
        return report.audit_status in {"pass", "warn"}

    def _run_report_stage(
        self,
        records: list[dict[str, Any]],
        *,
        allow_failed_audit_report: bool,
    ) -> bool:
        if not self.audit_report_path.exists():
            self._append_stage(
                records,
                stage="report",
                status="blocked_missing_inputs",
                inputs=[self.audit_report_path],
            )
            return False

        from text_factor_lab.reports import generate_run_report

        result = generate_run_report(
            run_id=self.config.run.run_id,
            run_dir=self.run_dir,
            config_path=self.config_snapshot_path,
            allow_failed_audit=allow_failed_audit_report,
        )
        self._append_stage(
            records,
            stage="report",
            status="completed",
            outputs=[result.report_markdown_path, result.report_summary_path],
            metrics={"conclusion_level": result.conclusion_level},
        )
        return True

    def _inputs_exist(self, *paths: Path) -> bool:
        return all(path.exists() for path in paths)

    def _resolve_raw_filing_path(
        self,
        source_url_or_path: str,
        raw_filings_dir: Path,
    ) -> Path | None:
        source_path = Path(source_url_or_path)
        if source_path.exists():
            return source_path
        source_name = source_path.name
        candidates = []
        if source_name:
            candidates.append(raw_filings_dir / source_name)
        safe_name = self._safe_artifact_name(source_url_or_path)
        candidates.extend(
            [
                raw_filings_dir / safe_name,
                raw_filings_dir / f"{safe_name}.html",
                raw_filings_dir / f"{safe_name}.txt",
            ]
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _safe_artifact_name(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "artifact"

    def _append_stage(
        self,
        records: list[dict[str, Any]],
        *,
        stage: str,
        status: str,
        message: str | None = None,
        inputs: list[Path] | None = None,
        outputs: list[Path] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        records.append(
            {
                "stage": stage,
                "status": status,
                "message": message,
                "inputs": [str(path) for path in inputs or []],
                "outputs": [str(path) for path in outputs or []],
                "metrics": metrics or {},
                "created_at_utc": datetime.now(UTC).isoformat(),
            }
        )

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

