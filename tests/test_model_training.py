from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pytest

from text_factor_lab.models import (
    build_model_artifacts,
    rank_ic,
    read_features_jsonl,
    read_labels_jsonl,
    read_split_assignments_jsonl,
)
from text_factor_lab.schemas import FeatureRecord, LabelRecord, SplitAssignmentRecord

SPLIT_ID = "train_2010_2014__val_2015_2015__test_2016_2016"


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


def feature(
    *,
    document_id: str,
    ticker: str,
    year: int,
    family: str,
    name: str,
    value: float,
    version: str,
) -> FeatureRecord:
    return FeatureRecord(
        feature_id=f"{document_id}:{version}:{name}",
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        event_time_utc=utc(year, 3, 1),
        prediction_time_utc=utc(year, 3, 1),
        feature_time_utc=utc(year, 3, 1),
        feature_family=family,
        feature_name=name,
        feature_value=value,
        feature_version=version,
        source_document_id=document_id,
        source_chunk_id=f"{document_id}:full",
    )


def industry_feature(document_id: str, ticker: str, year: int, industry: str) -> FeatureRecord:
    return FeatureRecord(
        feature_id=f"{document_id}:metadata:industry",
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        event_time_utc=utc(year, 3, 1),
        prediction_time_utc=utc(year, 3, 1),
        feature_time_utc=utc(year, 3, 1),
        feature_family="metadata",
        feature_name="industry",
        feature_value=industry,
        feature_version="metadata-v0",
        source_document_id=document_id,
        source_chunk_id=None,
    )


def fixture_records() -> tuple[list[LabelRecord], list[FeatureRecord], list[SplitAssignmentRecord]]:
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
    features: list[FeatureRecord] = []
    for document_id, ticker, year, role, _, signal in rows:
        industry = "Software" if ticker in {"AAA", "CCC", "EEE"} else "Hardware"
        features.append(industry_feature(document_id, ticker, year, industry))
        features.append(
            feature(
                document_id=document_id,
                ticker=ticker,
                year=year,
                family="dictionary_tone",
                name="dictionary_full__risk_share",
                value=signal,
                version="dictionary-tone-v0",
            )
        )
        features.append(
            feature(
                document_id=document_id,
                ticker=ticker,
                year=year,
                family="tfidf",
                name="tfidf_item_1a__risk",
                value=signal,
                version=f"tfidf-v0:{SPLIT_ID}:item_1a:{role}",
            )
        )
    features.append(
        feature(
            document_id="sec:test:b",
            ticker="FFF",
            year=2016,
            family="tfidf",
            name="tfidf_item_1a__risk",
            value=999.0,
            version="tfidf-v0:other_split:item_1a:test",
        )
    )
    return labels, features, assignments


def write_jsonl(records: list, path: Path) -> None:
    path.write_text(
        "".join(record.model_dump_json() + "\n" for record in records),
        encoding="utf-8",
    )


def test_build_model_artifacts_outputs_predictions_manifests_and_tuning_logs() -> None:
    labels, features, assignments = fixture_records()

    result = build_model_artifacts(
        run_id="model_test_run",
        labels=labels,
        features=features,
        split_assignments=assignments,
        models=["historical_mean", "ridge"],
        random_seed=42,
        ridge_alpha_grid=[0.1, 1.0],
    )

    assert len(result.model_manifests) == 2
    assert len(result.tuning_logs) == 2
    assert len(result.predictions) == 8
    assert {record.role for record in result.predictions} == {"validation", "test"}
    ridge_manifest = next(
        record for record in result.model_manifests if record.model_name == "ridge"
    )
    assert ridge_manifest.feature_count == 2
    assert ridge_manifest.train_observation_count == 2
    ridge_tuning = next(
        record for record in result.tuning_logs if record.model_id.startswith("ridge")
    )
    assert ridge_tuning.validation_metric == "validation_rank_ic"
    assert ridge_tuning.selected_parameters["alpha"] in {0.1, 1.0}

    labels_by_id = {record.label_id: record for record in labels}
    historical_predictions = [
        record
        for record in result.predictions
        if record.model_id.startswith("historical_mean")
    ]
    for role in ("validation", "test"):
        role_predictions = [
            record for record in historical_predictions if record.role == role
        ]
        prediction_values = np.array(
            [record.prediction_value for record in role_predictions],
            dtype=float,
        )
        target_values = np.array(
            [labels_by_id[record.label_id].target_value for record in role_predictions],
            dtype=float,
        )

        assert len(np.unique(prediction_values)) == 1
        assert rank_ic(target_values, prediction_values) == 0.0


def test_ridge_feature_ablation_uses_distinct_feature_blocks() -> None:
    labels, features, assignments = fixture_records()

    result = build_model_artifacts(
        run_id="ablation_test_run",
        labels=labels,
        features=features,
        split_assignments=assignments,
        models=["industry_mean", "ridge"],
        random_seed=42,
        ridge_alpha_grid=[0.1],
        ridge_feature_ablation_sets=[
            "dictionary_only",
            "tfidf_svd_only",
            "industry_plus_text",
        ],
    )

    manifests_by_id = {
        record.model_id.split("::", 1)[0]: record
        for record in result.model_manifests
    }
    assert manifests_by_id["industry_mean"].feature_set == "industry_only"
    assert manifests_by_id["ridge"].feature_set == "combined_text"
    assert manifests_by_id["ridge_dictionary_only"].feature_set == "dictionary_only"
    assert manifests_by_id["ridge_tfidf_svd_only"].feature_set == "tfidf_svd_only"
    assert manifests_by_id["ridge_industry_plus_text"].feature_set == "industry_plus_text"
    assert manifests_by_id["ridge_dictionary_only"].feature_count == 1
    assert manifests_by_id["ridge_tfidf_svd_only"].feature_count == 1
    assert manifests_by_id["ridge_industry_plus_text"].feature_count == 4


def test_build_models_cli_writes_artifacts(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    labels, features, assignments = fixture_records()
    labels_path = tmp_path / "labels.jsonl"
    features_path = tmp_path / "features.jsonl"
    assignments_path = tmp_path / "split_assignments.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    manifest_path = tmp_path / "model_manifest.json"
    tuning_path = tmp_path / "tuning_log.json"
    write_jsonl(labels, labels_path)
    write_jsonl(features, features_path)
    write_jsonl(assignments, assignments_path)

    exit_code = main(
        [
            "build-models",
            "--run-id",
            "model_test_run",
            "--labels",
            str(labels_path),
            "--features",
            str(features_path),
            "--split-assignments",
            str(assignments_path),
            "--predictions-output",
            str(predictions_path),
            "--model-manifest-output",
            str(manifest_path),
            "--tuning-log-output",
            str(tuning_path),
            "--ridge-alpha",
            "0.1",
            "--ridge-alpha",
            "1.0",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "predictions=8" in captured.out
    assert predictions_path.read_text(encoding="utf-8").count("\n") == 8
    assert len(json.loads(manifest_path.read_text(encoding="utf-8"))) == 2
    assert len(json.loads(tuning_path.read_text(encoding="utf-8"))) == 2


def test_model_artifact_readers_round_trip_jsonl(tmp_path: Path) -> None:
    labels, features, assignments = fixture_records()
    labels_path = tmp_path / "labels.jsonl"
    features_path = tmp_path / "features.jsonl"
    assignments_path = tmp_path / "split_assignments.jsonl"
    write_jsonl(labels, labels_path)
    write_jsonl(features, features_path)
    write_jsonl(assignments, assignments_path)

    assert len(read_labels_jsonl(labels_path)) == 6
    assert len(read_features_jsonl(features_path)) == 19
    assert len(read_split_assignments_jsonl(assignments_path)) == 6


def test_industry_mean_outputs_baseline_predictions() -> None:
    labels, features, assignments = fixture_records()

    result = build_model_artifacts(
        run_id="model_test_run",
        labels=labels,
        features=features,
        split_assignments=assignments,
        models=["industry_mean"],
        random_seed=42,
    )

    assert len(result.model_manifests) == 1
    assert result.model_manifests[0].model_name == "industry_mean"
    assert len(result.predictions) == 4


def test_xgboost_outputs_optional_model_predictions() -> None:
    pytest.importorskip("xgboost")
    labels, features, assignments = fixture_records()

    result = build_model_artifacts(
        run_id="model_test_run",
        labels=labels,
        features=features,
        split_assignments=assignments,
        models=["xgboost"],
        random_seed=42,
    )

    assert len(result.model_manifests) == 1
    assert result.model_manifests[0].model_name == "xgboost"
    assert len(result.predictions) == 4


def test_ridge_records_missing_feature_failures_but_baseline_still_covers_oos() -> None:
    labels, features, assignments = fixture_records()
    test_document_id = "sec:test:b"
    filtered_features = [
        record for record in features if record.source_document_id != test_document_id
    ]

    result = build_model_artifacts(
        run_id="model_test_run",
        labels=labels,
        features=filtered_features,
        split_assignments=assignments,
        models=["historical_mean", "ridge"],
        random_seed=42,
    )

    historical_predictions = [
        record for record in result.predictions if record.model_id.startswith("historical_mean")
    ]
    ridge_predictions = [
        record for record in result.predictions if record.model_id.startswith("ridge")
    ]

    assert len(historical_predictions) == 4
    assert len(ridge_predictions) == 3
    assert all(record.model_expected for record in result.predictions)
    assert any(
        failure.failure_stage == "missing_feature"
        and failure.model_id.startswith("ridge")
        and failure.label_id.startswith(test_document_id)
        for failure in result.prediction_failures
    )
