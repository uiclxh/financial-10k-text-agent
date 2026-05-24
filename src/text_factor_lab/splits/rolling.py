from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from text_factor_lab.schemas.labels import LabelRecord
from text_factor_lab.schemas.splits import SplitAssignmentRecord, SplitLeakageRecord, SplitRole

SPLIT_VERSION = "rolling-year-split-v0"


@dataclass(frozen=True)
class RollingSplitWindow:
    split_id: str
    train_start_date: date
    train_end_date: date
    validation_start_date: date
    validation_end_date: date
    test_start_date: date
    test_end_date: date
    embargo_days: int


@dataclass(frozen=True)
class SplitBuildResult:
    assignments: list[SplitAssignmentRecord]
    leakage_records: list[SplitLeakageRecord]
    windows: list[RollingSplitWindow]


def _year_start(year: int) -> date:
    return date(year, 1, 1)


def _year_end(year: int) -> date:
    return date(year, 12, 31)


def build_rolling_windows(
    *,
    sample_start: date,
    sample_end: date,
    train_years_min: int,
    validation_years: int,
    test_years: int,
    embargo_days: int,
) -> list[RollingSplitWindow]:
    if train_years_min < 1 or validation_years < 1 or test_years < 1:
        raise ValueError("train, validation, and test year counts must be positive")
    if embargo_days < 0:
        raise ValueError("embargo_days must be non-negative")

    first_train_year = sample_start.year
    first_validation_year = first_train_year + train_years_min
    first_test_year = first_validation_year + validation_years
    last_test_start_year = sample_end.year - test_years + 1

    windows: list[RollingSplitWindow] = []
    for test_start_year in range(first_test_year, last_test_start_year + 1):
        validation_start_year = test_start_year - validation_years
        train_end_year = validation_start_year - 1
        test_end_year = test_start_year + test_years - 1
        split_id = (
            f"train_{first_train_year}_{train_end_year}"
            f"__val_{validation_start_year}_{test_start_year - 1}"
            f"__test_{test_start_year}_{test_end_year}"
        )
        windows.append(
            RollingSplitWindow(
                split_id=split_id,
                train_start_date=sample_start,
                train_end_date=_year_end(train_end_year),
                validation_start_date=_year_start(validation_start_year),
                validation_end_date=_year_end(test_start_year - 1),
                test_start_date=_year_start(test_start_year),
                test_end_date=min(_year_end(test_end_year), sample_end),
                embargo_days=embargo_days,
            )
        )
    return windows


def build_rolling_year_splits(
    *,
    labels: list[LabelRecord],
    sample_start: date,
    sample_end: date,
    train_years_min: int,
    validation_years: int,
    test_years: int,
    embargo_days: int,
    split_version: str = SPLIT_VERSION,
) -> SplitBuildResult:
    windows = build_rolling_windows(
        sample_start=sample_start,
        sample_end=sample_end,
        train_years_min=train_years_min,
        validation_years=validation_years,
        test_years=test_years,
        embargo_days=embargo_days,
    )
    assignments: list[SplitAssignmentRecord] = []
    leakage_records: list[SplitLeakageRecord] = []

    for window in windows:
        for label in labels:
            event_date = label.event_time_utc.date()
            role = _role_for_event_date(event_date, window)
            if role is None:
                continue
            leakage = _leakage_for_label(label, role, window)
            if leakage is not None:
                leakage_records.append(leakage)
                continue
            assignments.append(
                _assignment_for_label(
                    label=label,
                    role=role,
                    event_date=event_date,
                    window=window,
                    split_version=split_version,
                )
            )

    return SplitBuildResult(
        assignments=assignments,
        leakage_records=leakage_records,
        windows=windows,
    )


def _role_for_event_date(event_date: date, window: RollingSplitWindow) -> SplitRole | None:
    if window.train_start_date <= event_date <= window.train_end_date:
        return "train"
    if window.validation_start_date <= event_date <= window.validation_end_date:
        return "validation"
    if window.test_start_date <= event_date <= window.test_end_date:
        return "test"
    return None


def _leakage_for_label(
    label: LabelRecord,
    role: SplitRole,
    window: RollingSplitWindow,
) -> SplitLeakageRecord | None:
    event_date = label.event_time_utc.date()
    if role == "train":
        cutoff = window.validation_start_date - timedelta(days=window.embargo_days)
        if label.label_end_date >= cutoff:
            return _leakage_record(
                label=label,
                role=role,
                severity="purged",
                split_id=window.split_id,
                leakage_type="purged_train_label_window_crosses_validation_embargo",
                message=(
                    f"Purged train label because label_end_date={label.label_end_date} "
                    "crosses the embargo cutoff before "
                    f"validation_start_date={window.validation_start_date}."
                ),
                event_date=event_date,
            )
    elif role == "validation":
        cutoff = window.test_start_date - timedelta(days=window.embargo_days)
        if label.label_end_date >= cutoff:
            return _leakage_record(
                label=label,
                role=role,
                severity="purged",
                split_id=window.split_id,
                leakage_type="purged_validation_label_window_crosses_test_embargo",
                message=(
                    f"Purged validation label because label_end_date={label.label_end_date} "
                    "crosses the embargo cutoff before "
                    f"test_start_date={window.test_start_date}."
                ),
                event_date=event_date,
            )
    elif role == "test" and label.label_start_date <= event_date:
        return _leakage_record(
            label=label,
            role=role,
            severity="fail",
            split_id=window.split_id,
            leakage_type="test_label_starts_before_or_on_event_date",
            message="Test label_start_date must be after event_date.",
            event_date=event_date,
        )
    return None


def _leakage_record(
    *,
    label: LabelRecord,
    role: SplitRole,
    severity: str,
    split_id: str,
    leakage_type: str,
    message: str,
    event_date: date,
) -> SplitLeakageRecord:
    return SplitLeakageRecord(
        split_id=split_id,
        label_id=label.label_id,
        ticker=label.ticker,
        target_name=label.target_name,
        role=role,
        severity=severity,
        leakage_type=leakage_type,
        message=message,
        event_date=event_date,
        label_end_date=label.label_end_date,
    )


def _assignment_for_label(
    *,
    label: LabelRecord,
    role: SplitRole,
    event_date: date,
    window: RollingSplitWindow,
    split_version: str,
) -> SplitAssignmentRecord:
    return SplitAssignmentRecord(
        split_id=window.split_id,
        label_id=label.label_id,
        entity_id=label.entity_id,
        ticker=label.ticker,
        target_name=label.target_name,
        role=role,
        event_date=event_date,
        label_start_date=label.label_start_date,
        label_end_date=label.label_end_date,
        train_start_date=window.train_start_date,
        train_end_date=window.train_end_date,
        validation_start_date=window.validation_start_date,
        validation_end_date=window.validation_end_date,
        test_start_date=window.test_start_date,
        test_end_date=window.test_end_date,
        embargo_days=window.embargo_days,
        split_version=split_version,
    )


def read_labels_jsonl(path: str | Path) -> list[LabelRecord]:
    labels: list[LabelRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                labels.append(LabelRecord.model_validate(json.loads(line)))
    return labels


def write_split_artifacts(
    result: SplitBuildResult,
    *,
    assignments_path: str | Path,
    leakage_path: str | Path,
) -> None:
    assignment_output = Path(assignments_path)
    leakage_output = Path(leakage_path)
    assignment_output.parent.mkdir(parents=True, exist_ok=True)
    leakage_output.parent.mkdir(parents=True, exist_ok=True)

    with assignment_output.open("w", encoding="utf-8") as file:
        for assignment in result.assignments:
            file.write(assignment.model_dump_json())
            file.write("\n")

    with leakage_output.open("w", encoding="utf-8") as file:
        for leakage in result.leakage_records:
            file.write(leakage.model_dump_json())
            file.write("\n")
