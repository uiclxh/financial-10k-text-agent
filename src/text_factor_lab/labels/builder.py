from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import field_validator

from text_factor_lab.data.prices import PriceDataError, PricePanel, ReturnType
from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware
from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.labels import LabelRecord

LABEL_BUILDER_VERSION = "labels-v0"
LabelFailureType = Literal[
    "unsupported_target",
    "label_window_unavailable",
    "missing_price",
    "missing_benchmark",
]
TARGET_PATTERN = re.compile(
    r"^(?P<kind>CAR|realized_volatility|realized_volatility_annualized)_(?P<start>[0-9]+)_(?P<end>[0-9]+)$"
)


class LabelFailureRecord(StrictBaseModel):
    label_id: str
    entity_id: str
    ticker: str
    event_time_utc: datetime
    target_name: str
    failure_type: LabelFailureType
    failure_message: str
    label_version: str
    created_at_utc: datetime

    @field_validator("event_time_utc", "created_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("datetime fields must be timezone-aware")
        return value


@dataclass(frozen=True)
class LabelBuildResult:
    labels: list[LabelRecord]
    failures: list[LabelFailureRecord]


@dataclass(frozen=True)
class ParsedTarget:
    kind: str
    start_offset: int
    end_offset: int


def parse_target_name(target_name: str) -> ParsedTarget:
    match = TARGET_PATTERN.match(target_name)
    if match is None:
        raise ValueError(f"Unsupported target_name={target_name}")
    start_offset = int(match.group("start"))
    end_offset = int(match.group("end"))
    if start_offset < 1 or end_offset < start_offset:
        raise ValueError(f"Invalid target window in target_name={target_name}")
    return ParsedTarget(
        kind=match.group("kind"),
        start_offset=start_offset,
        end_offset=end_offset,
    )


def build_labels_for_document(
    *,
    document: DocumentManifestRecord,
    price_panel: PricePanel,
    target_names: list[str],
    benchmark_ticker: str,
    return_type: ReturnType,
    adjustment_method: str,
    annualization_days: int,
    label_version: str = LABEL_BUILDER_VERSION,
) -> LabelBuildResult:
    labels: list[LabelRecord] = []
    failures: list[LabelFailureRecord] = []
    benchmark_ticker = benchmark_ticker.upper()

    for target_name in target_names:
        label_id = f"{document.document_id}:{target_name}:{label_version}"
        try:
            target = parse_target_name(target_name)
            stock_window = price_panel.forward_return_window(
                ticker=document.ticker,
                event_date=document.event_date,
                start_offset=target.start_offset,
                end_offset=target.end_offset,
                return_type=return_type,
            )

            if target.kind == "CAR":
                benchmark_window = price_panel.forward_return_window(
                    ticker=benchmark_ticker,
                    event_date=document.event_date,
                    start_offset=target.start_offset,
                    end_offset=target.end_offset,
                    return_type=return_type,
                )
                target_value = float(stock_window.returns.sum() - benchmark_window.returns.sum())
                benchmark_method = benchmark_ticker
            elif target.kind == "realized_volatility":
                if len(stock_window.returns) < 2:
                    raise PriceDataError("Realized volatility requires at least two returns")
                target_value = float(stock_window.returns.std(ddof=1))
                benchmark_method = "none"
            elif target.kind == "realized_volatility_annualized":
                if len(stock_window.returns) < 2:
                    raise PriceDataError("Realized volatility requires at least two returns")
                target_value = float(stock_window.returns.std(ddof=1) * np.sqrt(annualization_days))
                benchmark_method = "none"
            else:
                raise ValueError(f"Unsupported target kind={target.kind}")

            labels.append(
                LabelRecord(
                    label_id=label_id,
                    entity_id=document.entity_id,
                    ticker=document.ticker,
                    event_time_utc=document.event_time_utc,
                    prediction_time_utc=document.event_time_utc,
                    label_start_date=stock_window.label_start_date,
                    label_end_date=stock_window.label_end_date,
                    target_name=target_name,
                    target_value=target_value,
                    benchmark_method=benchmark_method,
                    return_type=return_type,
                    adjustment_method=adjustment_method,
                    label_version=label_version,
                )
            )
        except PriceDataError as exc:
            failures.append(
                _failure_record(
                    document=document,
                    target_name=target_name,
                    label_id=label_id,
                    failure_type=_price_failure_type(str(exc), benchmark_ticker),
                    failure_message=str(exc),
                    label_version=label_version,
                )
            )
        except ValueError as exc:
            failures.append(
                _failure_record(
                    document=document,
                    target_name=target_name,
                    label_id=label_id,
                    failure_type="unsupported_target",
                    failure_message=str(exc),
                    label_version=label_version,
                )
            )
    return LabelBuildResult(labels=labels, failures=failures)


def _price_failure_type(message: str, benchmark_ticker: str) -> LabelFailureType:
    if f"ticker={benchmark_ticker}" in message:
        return "missing_benchmark"
    if "No prices available" in message:
        return "missing_price"
    return "label_window_unavailable"


def _failure_record(
    *,
    document: DocumentManifestRecord,
    target_name: str,
    label_id: str,
    failure_type: LabelFailureType,
    failure_message: str,
    label_version: str,
) -> LabelFailureRecord:
    return LabelFailureRecord(
        label_id=label_id,
        entity_id=document.entity_id,
        ticker=document.ticker,
        event_time_utc=document.event_time_utc,
        target_name=target_name,
        failure_type=failure_type,
        failure_message=failure_message,
        label_version=label_version,
        created_at_utc=datetime.now(UTC),
    )


def build_labels_for_documents(
    *,
    documents: list[DocumentManifestRecord],
    price_panel: PricePanel,
    target_names: list[str],
    benchmark_ticker: str,
    return_type: ReturnType,
    adjustment_method: str,
    annualization_days: int,
    label_version: str = LABEL_BUILDER_VERSION,
) -> LabelBuildResult:
    labels: list[LabelRecord] = []
    failures: list[LabelFailureRecord] = []
    for document in documents:
        result = build_labels_for_document(
            document=document,
            price_panel=price_panel,
            target_names=target_names,
            benchmark_ticker=benchmark_ticker,
            return_type=return_type,
            adjustment_method=adjustment_method,
            annualization_days=annualization_days,
            label_version=label_version,
        )
        labels.extend(result.labels)
        failures.extend(result.failures)
    return LabelBuildResult(labels=labels, failures=failures)


def read_document_manifest_jsonl(path: str | Path) -> list[DocumentManifestRecord]:
    records: list[DocumentManifestRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(DocumentManifestRecord.model_validate(json.loads(line)))
    return records


def write_label_artifacts(
    result: LabelBuildResult,
    *,
    labels_path: str | Path,
    failures_path: str | Path,
) -> None:
    labels_output = Path(labels_path)
    failures_output = Path(failures_path)
    labels_output.parent.mkdir(parents=True, exist_ok=True)
    failures_output.parent.mkdir(parents=True, exist_ok=True)

    with labels_output.open("w", encoding="utf-8") as file:
        for label in result.labels:
            file.write(label.model_dump_json())
            file.write("\n")

    with failures_output.open("w", encoding="utf-8") as file:
        for failure in result.failures:
            file.write(failure.model_dump_json())
            file.write("\n")
