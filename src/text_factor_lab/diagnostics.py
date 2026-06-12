from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from text_factor_lab.schemas import LabelRecord, ParsedSectionRecord, PredictionRecord

WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']*")
CORE_SECTION_KEYS = {"item_1a", "item_7"}


def build_vocabulary_manifest(
    *,
    matrix_index_records: list[Any],
    tfidf_params: dict[str, Any],
    sample_size: int = 25,
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    for record in matrix_index_records:
        key = (record.split_id, record.text_scope)
        if key in seen:
            continue
        seen.add(key)
        terms = json.loads(Path(record.feature_names_path).read_text(encoding="utf-8"))
        rows.append(
            {
                "split_id": record.split_id,
                "text_scope": record.text_scope,
                "fit_scope": "train_window_only",
                "vocabulary_size": len(terms),
                "top_terms_sample": terms[:sample_size],
                "vocabulary_hash": _hash_terms(terms),
                "tfidf_params": tfidf_params,
                "feature_names_path": record.feature_names_path,
                "created_at_utc": datetime.now(UTC).isoformat(),
            }
        )
    return sorted(rows, key=lambda row: (row["split_id"], row["text_scope"]))


def write_vocabulary_manifest_json(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_section_length_quality_report(
    parsed_sections: list[ParsedSectionRecord],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for section in parsed_sections:
        text = ""
        if section.parser_status == "parsed" and section.artifact_path is not None:
            path = Path(section.artifact_path)
            if path.exists():
                text = path.read_text(encoding="utf-8")
        word_count = len(WORD_PATTERN.findall(text))
        char_count = len(text)
        quality_flag = _section_quality_flag(section.section_key, word_count)
        excluded = _exclude_from_section_level_features(section.section_key, quality_flag)
        rows.append(
            {
                "document_id": section.document_id,
                "ticker": section.ticker,
                "section": section.section_key,
                "section_name": section.section_name,
                "parser_status": section.parser_status,
                "char_count": char_count,
                "word_count": word_count,
                "quality_flag": quality_flag,
                "excluded_from_section_level_features": excluded,
                "feature_usage_policy": (
                    "exclude_from_section_level_features_keep_other_scopes"
                    if excluded
                    else "include"
                ),
            }
        )
    flag_counts = dict(sorted(_counts(row["quality_flag"] for row in rows).items()))
    exclusion_count = sum(1 for row in rows if row["excluded_from_section_level_features"])
    return {
        "report_version": "section-length-quality-v0",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "section_count": len(rows),
        "flag_counts": flag_counts,
        "section_level_feature_exclusion_count": exclusion_count,
        "rules": {
            "item_1a_item_7_warn_below_words": 500,
            "item_1a_item_7_manual_check_below_words": 100,
            "section_level_feature_exclusion_policy": (
                "item_1a/item_7 sections below 100 words are excluded from "
                "section-level features until parser boundaries are manually reviewed."
            ),
        },
        "rows": rows,
    }


def write_section_length_quality_report_json(report: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_prediction_distribution_report(
    *,
    predictions: list[PredictionRecord],
    labels: list[LabelRecord],
) -> dict[str, Any]:
    labels_by_id = {label.label_id: label for label in labels}
    grouped: dict[tuple[str, str, str], list[tuple[PredictionRecord, LabelRecord]]] = (
        defaultdict(list)
    )
    for prediction in predictions:
        if prediction.label_id is None or prediction.label_id not in labels_by_id:
            continue
        model_name = prediction.model_id.split("::", 1)[0]
        role = prediction.role or "unknown"
        grouped[(model_name, prediction.target_name, role)].append(
            (prediction, labels_by_id[prediction.label_id])
        )
    rows = [
        _prediction_distribution_row(model_name, target_name, role, items)
        for (model_name, target_name, role), items in grouped.items()
    ]
    rows.sort(key=lambda row: (row["target_name"], row["model_name"], row["role"]))
    warning_rows = [
        row
        for row in rows
        if row["prediction_scale_guard_status"] in {"warn", "fail"}
    ]
    return {
        "report_version": "prediction-distribution-v0",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "ranking_policy": (
            "Portfolio construction uses factor_score ordering to form ranks and "
            "quantiles; raw prediction magnitude is not used for equal-weight ranking "
            "except in explicitly risk-scaled variants."
        ),
        "outlier_rule": (
            "outlier_count flags predictions outside the observed target range or with "
            "absolute value greater than five times the target absolute scale."
        ),
        "prediction_scale_guard": {
            "warn_scale_ratio": 100.0,
            "fail_scale_ratio": 1000.0,
            "warning_row_count": len(warning_rows),
            "policy": (
                "Scale guard warnings do not change rank-based portfolio sorting; "
                "they require reporting raw-magnitude instability and favor rank_score "
                "or winsorized diagnostics over raw prediction magnitudes."
            ),
        },
        "rows": rows,
    }


def write_prediction_distribution_report_json(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prediction_distribution_row(
    model_name: str,
    target_name: str,
    role: str,
    items: list[tuple[PredictionRecord, LabelRecord]],
) -> dict[str, Any]:
    prediction_values = np.array(
        [item[0].prediction_value for item in items],
        dtype=float,
    )
    target_values = np.array([item[1].target_value for item in items], dtype=float)
    target_abs_scale = max(float(np.nanmax(np.abs(target_values))), 1e-12)
    prediction_abs_scale = float(np.nanmax(np.abs(prediction_values)))
    outlier_mask = (
        (prediction_values < float(np.nanmin(target_values)))
        | (prediction_values > float(np.nanmax(target_values)))
        | (np.abs(prediction_values) > 5.0 * target_abs_scale)
    )
    scale_ratio = prediction_abs_scale / target_abs_scale
    guard_status, guard_reason = _prediction_scale_guard(scale_ratio)
    return {
        "model_name": model_name,
        "target_name": target_name,
        "role": role,
        "observation_count": int(len(items)),
        "prediction_min": float(np.nanmin(prediction_values)),
        "prediction_max": float(np.nanmax(prediction_values)),
        "prediction_p1": float(np.nanpercentile(prediction_values, 1)),
        "prediction_p99": float(np.nanpercentile(prediction_values, 99)),
        "target_min": float(np.nanmin(target_values)),
        "target_max": float(np.nanmax(target_values)),
        "target_p1": float(np.nanpercentile(target_values, 1)),
        "target_p99": float(np.nanpercentile(target_values, 99)),
        "scale_ratio": scale_ratio,
        "outlier_count": int(np.sum(outlier_mask)),
        "prediction_scale_guard_status": guard_status,
        "prediction_scale_guard_reason": guard_reason,
        "recommended_score_for_portfolio": (
            "rank_score_or_winsorized_prediction_score"
            if guard_status in {"warn", "fail"}
            else "factor_score"
        ),
    }


def _section_quality_flag(section_key: str, word_count: int) -> str:
    if section_key not in CORE_SECTION_KEYS:
        return "ok"
    if word_count < 100:
        return "manual_check_lt_100_words"
    if word_count < 500:
        return "warn_lt_500_words"
    return "ok"


def _exclude_from_section_level_features(section_key: str, quality_flag: str) -> bool:
    return section_key in CORE_SECTION_KEYS and quality_flag == "manual_check_lt_100_words"


def _prediction_scale_guard(scale_ratio: float) -> tuple[str, str]:
    if scale_ratio >= 1000.0:
        return (
            "fail",
            "Raw prediction magnitude exceeds 1000x target scale; report as scale outlier.",
        )
    if scale_ratio >= 100.0:
        return (
            "warn",
            "Raw prediction magnitude exceeds 100x target scale; prefer rank-based scoring.",
        )
    return "pass", "Raw prediction scale is within guard threshold."


def _hash_terms(terms: list[str]) -> str:
    payload = json.dumps(terms, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts
