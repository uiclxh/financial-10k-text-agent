from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from text_factor_lab.features import document_id_from_label_id
from text_factor_lab.schemas import (
    FeatureRecord,
    LabelRecord,
    ModelManifestRecord,
    PredictionRecord,
    SplitAssignmentRecord,
    TuningLogRecord,
)

MODEL_TRAINING_VERSION = "model-training-v0"
DEFAULT_RIDGE_ALPHA_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]
ModelName = Literal["historical_mean", "ridge"]


@dataclass(frozen=True)
class ModelBuildResult:
    predictions: list[PredictionRecord]
    model_manifests: list[ModelManifestRecord]
    tuning_logs: list[TuningLogRecord]


@dataclass(frozen=True)
class ModelRow:
    label: LabelRecord
    assignment: SplitAssignmentRecord
    document_id: str
    features: dict[str, float]


def read_features_jsonl(path: str | Path) -> list[FeatureRecord]:
    records: list[FeatureRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(FeatureRecord.model_validate(json.loads(line)))
    return records


def read_labels_jsonl(path: str | Path) -> list[LabelRecord]:
    records: list[LabelRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(LabelRecord.model_validate(json.loads(line)))
    return records


def read_split_assignments_jsonl(path: str | Path) -> list[SplitAssignmentRecord]:
    records: list[SplitAssignmentRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(SplitAssignmentRecord.model_validate(json.loads(line)))
    return records


def build_model_artifacts(
    *,
    run_id: str,
    labels: list[LabelRecord],
    features: list[FeatureRecord],
    split_assignments: list[SplitAssignmentRecord],
    models: list[ModelName],
    random_seed: int,
    ridge_alpha_grid: list[float] | None = None,
) -> ModelBuildResult:
    labels_by_id = {label.label_id: label for label in labels}
    rows_by_split_target_role = _build_rows_by_split_target_role(
        labels_by_id=labels_by_id,
        features=features,
        split_assignments=split_assignments,
    )
    alpha_grid = ridge_alpha_grid or DEFAULT_RIDGE_ALPHA_GRID
    predictions: list[PredictionRecord] = []
    manifests: list[ModelManifestRecord] = []
    tuning_logs: list[TuningLogRecord] = []

    split_targets = sorted(
        {
            (split_id, target_name)
            for split_id, target_map in rows_by_split_target_role.items()
            for target_name in target_map
        }
    )
    for split_id, target_name in split_targets:
        role_map = rows_by_split_target_role[split_id][target_name]
        train_rows = role_map.get("train", [])
        validation_rows = role_map.get("validation", [])
        test_rows = role_map.get("test", [])
        if not train_rows:
            continue
        feature_names = _feature_names_from_train_rows(train_rows)
        window_payload = _window_payload(train_rows[0].assignment)

        if "historical_mean" in models:
            model_predictions, manifest, tuning_log = _fit_historical_mean(
                run_id=run_id,
                split_id=split_id,
                target_name=target_name,
                train_rows=train_rows,
                validation_rows=validation_rows,
                test_rows=test_rows,
                feature_count=len(feature_names),
                feature_version=_feature_version(split_id),
                random_seed=random_seed,
                window_payload=window_payload,
            )
            predictions.extend(model_predictions)
            manifests.append(manifest)
            tuning_logs.append(tuning_log)

        if "ridge" in models and feature_names:
            model_predictions, manifest, tuning_log = _fit_ridge(
                run_id=run_id,
                split_id=split_id,
                target_name=target_name,
                train_rows=train_rows,
                validation_rows=validation_rows,
                test_rows=test_rows,
                feature_names=feature_names,
                alpha_grid=alpha_grid,
                random_seed=random_seed,
                window_payload=window_payload,
            )
            predictions.extend(model_predictions)
            manifests.append(manifest)
            tuning_logs.append(tuning_log)

    return ModelBuildResult(
        predictions=predictions,
        model_manifests=manifests,
        tuning_logs=tuning_logs,
    )


def _build_rows_by_split_target_role(
    *,
    labels_by_id: dict[str, LabelRecord],
    features: list[FeatureRecord],
    split_assignments: list[SplitAssignmentRecord],
) -> dict[str, dict[str, dict[str, list[ModelRow]]]]:
    features_by_document = _features_by_document_split_role(features)
    grouped: dict[str, dict[str, dict[str, list[ModelRow]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for assignment in split_assignments:
        label = labels_by_id.get(assignment.label_id)
        if label is None:
            continue
        document_id = document_id_from_label_id(assignment.label_id)
        row_features = _features_for_assignment(
            features_by_document=features_by_document,
            document_id=document_id,
            split_id=assignment.split_id,
            role=assignment.role,
        )
        grouped[assignment.split_id][assignment.target_name][assignment.role].append(
            ModelRow(
                label=label,
                assignment=assignment,
                document_id=document_id,
                features=row_features,
            )
        )
    return grouped


def _features_by_document_split_role(
    features: list[FeatureRecord],
) -> dict[str, dict[str, dict[str, float]]]:
    grouped: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for feature in features:
        if isinstance(feature.feature_value, str):
            continue
        if feature.feature_family == "tfidf":
            split_id, role = _tfidf_split_role(feature.feature_version)
            if split_id is None or role is None:
                continue
            key = f"tfidf::{split_id}::{role}"
        else:
            key = "global"
        grouped[feature.source_document_id][key][feature.feature_name] = float(
            feature.feature_value
        )
    return grouped


def _tfidf_split_role(feature_version: str) -> tuple[str | None, str | None]:
    parts = feature_version.split(":")
    if len(parts) < 4:
        return None, None
    role = parts[-1]
    if role not in {"train", "validation", "test"}:
        return None, None
    split_id = parts[1]
    return split_id, role


def _features_for_assignment(
    *,
    features_by_document: dict[str, dict[str, dict[str, float]]],
    document_id: str,
    split_id: str,
    role: str,
) -> dict[str, float]:
    document_features = features_by_document.get(document_id, {})
    row_features = dict(document_features.get("global", {}))
    row_features.update(document_features.get(f"tfidf::{split_id}::{role}", {}))
    return row_features


def _feature_names_from_train_rows(train_rows: list[ModelRow]) -> list[str]:
    names: set[str] = set()
    for row in train_rows:
        names.update(row.features)
    return sorted(names)


def _matrix(rows: list[ModelRow], feature_names: list[str]) -> np.ndarray:
    matrix = np.zeros((len(rows), len(feature_names)), dtype=float)
    for row_index, row in enumerate(rows):
        for column_index, feature_name in enumerate(feature_names):
            matrix[row_index, column_index] = row.features.get(feature_name, 0.0)
    return matrix


def _targets(rows: list[ModelRow]) -> np.ndarray:
    return np.array([row.label.target_value for row in rows], dtype=float)


def _fit_historical_mean(
    *,
    run_id: str,
    split_id: str,
    target_name: str,
    train_rows: list[ModelRow],
    validation_rows: list[ModelRow],
    test_rows: list[ModelRow],
    feature_count: int,
    feature_version: str,
    random_seed: int,
    window_payload: dict[str, str],
) -> tuple[list[PredictionRecord], ModelManifestRecord, TuningLogRecord]:
    mean_value = float(_targets(train_rows).mean())
    predictions = _constant_predictions(
        run_id=run_id,
        model_id=f"historical_mean::{target_name}::{split_id}",
        split_id=split_id,
        target_name=target_name,
        rows=[*validation_rows, *test_rows],
        prediction_value=mean_value,
        feature_version=feature_version,
        window_payload=window_payload,
    )
    manifest = _model_manifest(
        model_id=f"historical_mean::{target_name}::{split_id}",
        model_name="historical_mean",
        model_family="baseline",
        model_level=0,
        hyperparameters={"statistic": "train_mean"},
        random_seed=random_seed,
        target_rows=(train_rows, validation_rows, test_rows),
        feature_count=feature_count,
        feature_version=feature_version,
        label_version=train_rows[0].label.label_version,
        window_payload=window_payload,
    )
    tuning_log = TuningLogRecord(
        run_id=run_id,
        split_id=split_id,
        target_name=target_name,
        model_id=manifest.model_id,
        parameter_grid={},
        searched_parameters=[],
        validation_metric="not_applicable",
        validation_scores=[],
        selected_parameters={"statistic": "train_mean"},
        selection_reason="Baseline uses the training-window target mean.",
        created_at_utc=datetime.now(UTC),
    )
    return predictions, manifest, tuning_log


def _fit_ridge(
    *,
    run_id: str,
    split_id: str,
    target_name: str,
    train_rows: list[ModelRow],
    validation_rows: list[ModelRow],
    test_rows: list[ModelRow],
    feature_names: list[str],
    alpha_grid: list[float],
    random_seed: int,
    window_payload: dict[str, str],
) -> tuple[list[PredictionRecord], ModelManifestRecord, TuningLogRecord]:
    x_train = _matrix(train_rows, feature_names)
    y_train = _targets(train_rows)
    x_validation = _matrix(validation_rows, feature_names)
    y_validation = _targets(validation_rows)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_validation_scaled = scaler.transform(x_validation) if validation_rows else x_validation
    searched_parameters: list[dict[str, float]] = []
    validation_scores: list[float] = []
    best_alpha = float(alpha_grid[0])
    best_score = float("-inf")

    for alpha in alpha_grid:
        model = Ridge(alpha=float(alpha), random_state=random_seed)
        model.fit(x_train_scaled, y_train)
        validation_prediction = (
            model.predict(x_validation_scaled) if validation_rows else model.predict(x_train_scaled)
        )
        validation_target = y_validation if validation_rows else y_train
        score = rank_ic(validation_target, validation_prediction)
        searched_parameters.append({"alpha": float(alpha)})
        validation_scores.append(float(score))
        if score > best_score:
            best_score = float(score)
            best_alpha = float(alpha)

    x_fit_rows = [*train_rows, *validation_rows] if validation_rows else train_rows
    x_fit = _matrix(x_fit_rows, feature_names)
    y_fit = _targets(x_fit_rows)
    final_scaler = StandardScaler()
    final_x = final_scaler.fit_transform(x_fit)
    final_model = Ridge(alpha=best_alpha, random_state=random_seed)
    final_model.fit(final_x, y_fit)

    scored_rows = [*validation_rows, *test_rows]
    x_score = _matrix(scored_rows, feature_names)
    predictions_array = final_model.predict(final_scaler.transform(x_score)) if scored_rows else []
    predictions = _array_predictions(
        run_id=run_id,
        model_id=f"ridge::{target_name}::{split_id}",
        split_id=split_id,
        target_name=target_name,
        rows=scored_rows,
        predictions=predictions_array,
        feature_version=_feature_version(split_id),
        window_payload=window_payload,
    )
    manifest = _model_manifest(
        model_id=f"ridge::{target_name}::{split_id}",
        model_name="ridge",
        model_family="linear_regularized",
        model_level=2,
        hyperparameters={"alpha": best_alpha, "fit_intercept": True, "scaler": "standard"},
        random_seed=random_seed,
        target_rows=(train_rows, validation_rows, test_rows),
        feature_count=len(feature_names),
        feature_version=_feature_version(split_id),
        label_version=train_rows[0].label.label_version,
        window_payload=window_payload,
    )
    tuning_log = TuningLogRecord(
        run_id=run_id,
        split_id=split_id,
        target_name=target_name,
        model_id=manifest.model_id,
        parameter_grid={"alpha": [float(alpha) for alpha in alpha_grid]},
        searched_parameters=searched_parameters,
        validation_metric="validation_rank_ic",
        validation_scores=validation_scores,
        selected_parameters={"alpha": best_alpha},
        selection_reason="Selected highest validation rank IC; ties keep first grid value.",
        created_at_utc=datetime.now(UTC),
    )
    return predictions, manifest, tuning_log


def rank_ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0
    true_rank = _rank_values(y_true)
    pred_rank = _rank_values(y_pred)
    if np.std(true_rank) == 0 or np.std(pred_rank) == 0:
        return 0.0
    return float(np.corrcoef(true_rank, pred_rank)[0, 1])


def _rank_values(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks


def _constant_predictions(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rows: list[ModelRow],
    prediction_value: float,
    feature_version: str,
    window_payload: dict[str, str],
) -> list[PredictionRecord]:
    return _array_predictions(
        run_id=run_id,
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        rows=rows,
        predictions=np.full(len(rows), prediction_value, dtype=float),
        feature_version=feature_version,
        window_payload=window_payload,
    )


def _array_predictions(
    *,
    run_id: str,
    model_id: str,
    split_id: str,
    target_name: str,
    rows: list[ModelRow],
    predictions: np.ndarray,
    feature_version: str,
    window_payload: dict[str, str],
) -> list[PredictionRecord]:
    records: list[PredictionRecord] = []
    for row, prediction in zip(rows, predictions, strict=True):
        records.append(
            PredictionRecord(
                run_id=run_id,
                model_id=model_id,
                split_id=split_id,
                label_id=row.label.label_id,
                role="validation" if row.assignment.role == "validation" else "test",
                ticker=row.label.ticker,
                event_date=row.assignment.event_date,
                target_name=target_name,
                prediction_value=float(prediction),
                factor_score=float(prediction),
                feature_version=feature_version,
                label_version=row.label.label_version,
                training_window=window_payload["training_window"],
                validation_window=window_payload["validation_window"],
                test_window=window_payload["test_window"],
            )
        )
    return records


def _model_manifest(
    *,
    model_id: str,
    model_name: str,
    model_family: str,
    model_level: int,
    hyperparameters: dict[str, object],
    random_seed: int,
    target_rows: tuple[list[ModelRow], list[ModelRow], list[ModelRow]],
    feature_count: int,
    feature_version: str,
    label_version: str,
    window_payload: dict[str, str],
) -> ModelManifestRecord:
    train_rows, validation_rows, test_rows = target_rows
    return ModelManifestRecord(
        model_id=model_id,
        model_name=model_name,
        model_family=model_family,
        model_level=model_level,
        model_version=MODEL_TRAINING_VERSION,
        hyperparameters=hyperparameters,
        random_seed=random_seed,
        training_window=window_payload["training_window"],
        validation_window=window_payload["validation_window"],
        test_window=window_payload["test_window"],
        feature_version=feature_version,
        label_version=label_version,
        code_commit=None,
        train_observation_count=len(train_rows),
        validation_observation_count=len(validation_rows),
        test_observation_count=len(test_rows),
        feature_count=feature_count,
        created_at_utc=datetime.now(UTC),
    )


def _feature_version(split_id: str) -> str:
    return f"features-v0:{split_id}"


def _window_payload(assignment: SplitAssignmentRecord) -> dict[str, str]:
    return {
        "training_window": f"{assignment.train_start_date}..{assignment.train_end_date}",
        "validation_window": (
            f"{assignment.validation_start_date}..{assignment.validation_end_date}"
        ),
        "test_window": f"{assignment.test_start_date}..{assignment.test_end_date}",
    }


def write_predictions_jsonl(records: list[PredictionRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def write_model_manifest_json(records: list[ModelManifestRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([record.model_dump(mode="json") for record in records], file, indent=2)
        file.write("\n")


def write_tuning_log_json(records: list[TuningLogRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([record.model_dump(mode="json") for record in records], file, indent=2)
        file.write("\n")
