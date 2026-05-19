from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from text_factor_lab.schemas import LabelRecord, SplitAssignmentRecord
from text_factor_lab.splits import (
    build_rolling_year_splits,
    read_labels_jsonl,
    write_split_artifacts,
)
from text_factor_lab.splits.rolling import build_rolling_windows


def utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


def label(
    year: int,
    *,
    month: int = 6,
    day: int = 15,
    end_year: int | None = None,
    target_name: str = "CAR_1_20",
) -> LabelRecord:
    resolved_end_year = end_year or year
    return LabelRecord(
        label_id=f"AAPL-{target_name}-{year}-{day}",
        entity_id="CIK0000320193",
        ticker="AAPL",
        event_time_utc=utc(year, month, day),
        prediction_time_utc=utc(year, month, day),
        label_start_date=date(year, month, min(day + 1, 28)),
        label_end_date=date(resolved_end_year, month + 1 if month < 12 else 12, min(day + 20, 31)),
        target_name=target_name,
        target_value=0.01,
        benchmark_method="SPY",
        return_type="log",
        adjustment_method="adj_close",
        label_version="labels-v0",
    )


def test_build_rolling_windows_uses_expanding_train() -> None:
    windows = build_rolling_windows(
        sample_start=date(2010, 1, 1),
        sample_end=date(2018, 12, 31),
        train_years_min=5,
        validation_years=1,
        test_years=1,
        embargo_days=20,
    )

    assert [window.test_start_date.year for window in windows] == [2016, 2017, 2018]
    assert windows[0].train_start_date == date(2010, 1, 1)
    assert windows[0].train_end_date == date(2014, 12, 31)
    assert windows[1].train_end_date == date(2015, 12, 31)
    assert windows[0].validation_start_date == date(2015, 1, 1)


def test_build_rolling_year_splits_assigns_train_validation_test_roles() -> None:
    result = build_rolling_year_splits(
        labels=[label(2014), label(2015), label(2016), label(2017)],
        sample_start=date(2010, 1, 1),
        sample_end=date(2017, 12, 31),
        train_years_min=5,
        validation_years=1,
        test_years=1,
        embargo_days=0,
    )
    first_split = "train_2010_2014__val_2015_2015__test_2016_2016"
    roles = {
        assignment.label_id: assignment.role
        for assignment in result.assignments
        if assignment.split_id == first_split
    }

    assert roles["AAPL-CAR_1_20-2014-15"] == "train"
    assert roles["AAPL-CAR_1_20-2015-15"] == "validation"
    assert roles["AAPL-CAR_1_20-2016-15"] == "test"
    assert "AAPL-CAR_1_20-2017-15" not in roles
    assert result.leakage_records == []


def test_embargo_excludes_training_label_that_crosses_validation_boundary() -> None:
    result = build_rolling_year_splits(
        labels=[label(2014, month=12, day=27)],
        sample_start=date(2010, 1, 1),
        sample_end=date(2016, 12, 31),
        train_years_min=5,
        validation_years=1,
        test_years=1,
        embargo_days=20,
    )

    assert result.assignments == []
    assert len(result.leakage_records) == 1
    assert result.leakage_records[0].leakage_type == (
        "train_label_window_crosses_validation_embargo"
    )


def test_embargo_excludes_validation_label_that_crosses_test_boundary() -> None:
    result = build_rolling_year_splits(
        labels=[label(2015, month=12, day=27)],
        sample_start=date(2010, 1, 1),
        sample_end=date(2016, 12, 31),
        train_years_min=5,
        validation_years=1,
        test_years=1,
        embargo_days=20,
    )

    assert result.assignments == []
    assert result.leakage_records[0].leakage_type == (
        "validation_label_window_crosses_test_embargo"
    )


def test_split_assignment_schema_requires_ordered_windows() -> None:
    with pytest.raises(ValidationError, match="train < validation < test"):
        SplitAssignmentRecord(
            split_id="bad",
            label_id="label",
            entity_id="entity",
            ticker="AAPL",
            target_name="CAR_1_20",
            role="train",
            event_date=date(2015, 1, 1),
            label_start_date=date(2015, 1, 2),
            label_end_date=date(2015, 1, 30),
            train_start_date=date(2010, 1, 1),
            train_end_date=date(2015, 12, 31),
            validation_start_date=date(2015, 1, 1),
            validation_end_date=date(2015, 12, 31),
            test_start_date=date(2016, 1, 1),
            test_end_date=date(2016, 12, 31),
            embargo_days=20,
            split_version="rolling-year-split-v0",
        )


def test_write_split_artifacts_round_trips_jsonl(tmp_path: Path) -> None:
    result = build_rolling_year_splits(
        labels=[label(2014), label(2015), label(2016)],
        sample_start=date(2010, 1, 1),
        sample_end=date(2016, 12, 31),
        train_years_min=5,
        validation_years=1,
        test_years=1,
        embargo_days=0,
    )
    assignments_path = tmp_path / "split_assignments.jsonl"
    leakage_path = tmp_path / "split_leakage.jsonl"

    write_split_artifacts(result, assignments_path=assignments_path, leakage_path=leakage_path)

    first_assignment = json.loads(assignments_path.read_text(encoding="utf-8").splitlines()[0])
    assert first_assignment["split_version"] == "rolling-year-split-v0"
    assert leakage_path.read_text(encoding="utf-8") == ""


def test_read_labels_jsonl(tmp_path: Path) -> None:
    labels_path = tmp_path / "labels.jsonl"
    labels_path.write_text(label(2016).model_dump_json() + "\n", encoding="utf-8")

    labels = read_labels_jsonl(labels_path)

    assert len(labels) == 1
    assert labels[0].ticker == "AAPL"


def test_build_splits_cli_writes_assignments_and_leakage(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    labels_path = tmp_path / "labels.jsonl"
    assignments_path = tmp_path / "split_assignments.jsonl"
    leakage_path = tmp_path / "split_leakage.jsonl"
    labels_path.write_text(
        label(2014).model_dump_json()
        + "\n"
        + label(2015).model_dump_json()
        + "\n"
        + label(2016).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "build-splits",
            "--labels",
            str(labels_path),
            "--assignments-output",
            str(assignments_path),
            "--leakage-output",
            str(leakage_path),
            "--sample-start",
            "2010-01-01",
            "--sample-end",
            "2016-12-31",
            "--train-years-min",
            "5",
            "--validation-years",
            "1",
            "--test-years",
            "1",
            "--embargo-days",
            "0",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "assignments=3" in captured.out
    assert assignments_path.read_text(encoding="utf-8").count("\n") == 3
    assert leakage_path.read_text(encoding="utf-8") == ""
