from __future__ import annotations

import json
from datetime import UTC, date, datetime
from math import isclose, log
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from text_factor_lab.data.prices import build_price_panel, load_price_panel_csv
from text_factor_lab.labels import (
    build_labels_for_document,
    build_labels_for_documents,
    parse_target_name,
    read_document_manifest_jsonl,
    write_label_artifacts,
)
from text_factor_lab.schemas import DocumentManifestRecord


def utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


def sample_document() -> DocumentManifestRecord:
    return DocumentManifestRecord(
        document_id="sec:0000320193:0000320193-23-000106:aapl-20230930.htm",
        entity_id="CIK0000320193",
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        document_type="10-K",
        fiscal_year=2023,
        fiscal_period="FY",
        source_id="SEC_EDGAR",
        source_url_or_path="https://www.sec.gov/Archives/example/aapl-20230930.htm",
        retrieval_time_utc=utc(2023, 11, 3),
        available_time_utc=utc(2023, 11, 2, 22),
        event_time_utc=utc(2023, 11, 2, 22),
        event_date=date(2023, 11, 2),
        timezone="America/New_York",
        hash_sha256="a" * 64,
        license_note="Public SEC EDGAR filing; comply with SEC fair-access policy.",
        parser_version="sec-edgar-data-v0",
    )


def test_parse_target_name_extracts_kind_and_window() -> None:
    target = parse_target_name("CAR_1_20")

    assert target.kind == "CAR"
    assert target.start_offset == 1
    assert target.end_offset == 20


def test_build_labels_for_document_calculates_car_and_realized_volatility() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    result = build_labels_for_document(
        document=sample_document(),
        price_panel=panel,
        target_names=[
            "CAR_1_3",
            "realized_volatility_1_3",
            "realized_volatility_annualized_1_3",
        ],
        benchmark_ticker="SPY",
        return_type="log",
        adjustment_method="adj_close",
        annualization_days=252,
    )
    labels_by_target = {label.target_name: label for label in result.labels}

    aapl_returns = np.array([log(102 / 100), log(101 / 102), log(104 / 101)])
    spy_returns = np.array([log(402 / 400), log(404 / 402), log(403 / 404)])
    expected_car = float(aapl_returns.sum() - spy_returns.sum())
    expected_vol = float(aapl_returns.std(ddof=1))

    assert result.failures == []
    assert isclose(labels_by_target["CAR_1_3"].target_value, expected_car)
    assert labels_by_target["CAR_1_3"].benchmark_method == "SPY"
    assert labels_by_target["CAR_1_3"].label_start_date == date(2023, 11, 3)
    assert labels_by_target["CAR_1_3"].label_end_date == date(2023, 11, 7)
    assert isclose(labels_by_target["realized_volatility_1_3"].target_value, expected_vol)
    assert isclose(
        labels_by_target["realized_volatility_annualized_1_3"].target_value,
        expected_vol * np.sqrt(252),
    )


def test_label_builder_records_failure_for_insufficient_forward_window() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    result = build_labels_for_document(
        document=sample_document(),
        price_panel=panel,
        target_names=["CAR_1_20"],
        benchmark_ticker="SPY",
        return_type="log",
        adjustment_method="adj_close",
        annualization_days=252,
    )

    assert result.labels == []
    assert len(result.failures) == 1
    assert result.failures[0].failure_type == "label_window_unavailable"
    assert "Insufficient forward window" in result.failures[0].failure_message


def test_realized_volatility_requires_at_least_two_returns() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    result = build_labels_for_document(
        document=sample_document(),
        price_panel=panel,
        target_names=["realized_volatility_1_1"],
        benchmark_ticker="SPY",
        return_type="log",
        adjustment_method="adj_close",
        annualization_days=252,
    )

    assert result.labels == []
    assert result.failures[0].failure_type == "label_window_unavailable"
    assert "at least two returns" in result.failures[0].failure_message


def test_labels_apply_delisting_return_to_car() -> None:
    panel = build_price_panel(
        pd.DataFrame(
            [
                ("2023-11-02", "AAPL", "", "", ""),
                ("2023-11-03", "AAPL", "0.10", "", ""),
                ("2023-11-06", "AAPL", "-0.20", "-0.50", "500"),
                ("2023-11-02", "SPY", "", "", ""),
                ("2023-11-03", "SPY", "0.01", "", ""),
                ("2023-11-06", "SPY", "0.02", "", ""),
            ],
            columns=["date", "ticker", "ret", "dlret", "dlstcd"],
        )
    )

    result = build_labels_for_document(
        document=sample_document(),
        price_panel=panel,
        target_names=["CAR_1_2"],
        benchmark_ticker="SPY",
        return_type="simple",
        adjustment_method="crsp_ret_with_dlret",
        annualization_days=252,
    )

    assert result.failures == []
    label = result.labels[0]
    assert label.delisting_return_applied is True
    assert label.delisting_code == "500"
    assert label.return_quality_flag == "delisting_return_applied"
    assert label.target_value == pytest.approx((0.10 - 0.6) - (0.01 + 0.02))


def test_write_label_artifacts_round_trips_jsonl(tmp_path: Path) -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    result = build_labels_for_documents(
        documents=[sample_document()],
        price_panel=panel,
        target_names=["CAR_1_3"],
        benchmark_ticker="SPY",
        return_type="log",
        adjustment_method="adj_close",
        annualization_days=252,
    )
    labels_path = tmp_path / "labels.jsonl"
    failures_path = tmp_path / "label_failures.jsonl"

    write_label_artifacts(result, labels_path=labels_path, failures_path=failures_path)

    raw_label = json.loads(labels_path.read_text(encoding="utf-8").strip())
    assert raw_label["target_name"] == "CAR_1_3"
    assert failures_path.read_text(encoding="utf-8") == ""


def test_read_document_manifest_jsonl(tmp_path: Path) -> None:
    manifest_path = tmp_path / "document_manifest.jsonl"
    manifest_path.write_text(sample_document().model_dump_json() + "\n", encoding="utf-8")

    records = read_document_manifest_jsonl(manifest_path)

    assert len(records) == 1
    assert records[0].ticker == "AAPL"


def test_build_labels_cli_writes_labels_and_failures(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    manifest_path = tmp_path / "document_manifest.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    failures_path = tmp_path / "label_failures.jsonl"
    manifest_path.write_text(sample_document().model_dump_json() + "\n", encoding="utf-8")

    exit_code = main(
        [
            "build-labels",
            "--document-manifest",
            str(manifest_path),
            "--prices",
            "tests/fixtures/prices_aapl_spy.csv",
            "--labels-output",
            str(labels_path),
            "--failures-output",
            str(failures_path),
            "--target",
            "CAR_1_3",
            "--target",
            "CAR_1_20",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "labels=1" in captured.out
    assert "failures=1" in captured.out
    assert labels_path.read_text(encoding="utf-8").count("\n") == 1
    assert failures_path.read_text(encoding="utf-8").count("\n") == 1
