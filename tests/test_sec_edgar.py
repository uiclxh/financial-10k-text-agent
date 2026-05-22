from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

from text_factor_lab.data import (
    build_archive_document_url,
    build_document_manifest_from_submissions,
    build_submissions_url,
    extract_annual_filings,
    filing_row_to_manifest_record,
    normalize_cik,
    parse_sec_acceptance_datetime,
    sec_event_date_from_acceptance_time,
    sec_event_date_resolution_from_acceptance_time,
    write_manifest_jsonl,
)
from text_factor_lab.data.sec_edgar import sha256_bytes
from text_factor_lab.data.universe import load_universe_manifest


def load_fixture() -> dict:
    return json.loads(
        Path("tests/fixtures/sec_submissions_aapl_recent.json").read_text(encoding="utf-8")
    )


def test_sec_url_builders_normalize_cik_and_accession() -> None:
    assert normalize_cik("320193") == "0000320193"
    assert build_submissions_url("320193").endswith("/CIK0000320193.json")
    assert build_archive_document_url(
        "0000320193",
        "0000320193-23-000106",
        "aapl-20230930.htm",
    ) == (
        "https://www.sec.gov/Archives/edgar/data/"
        "320193/000032019323000106/aapl-20230930.htm"
    )


def test_parse_sec_acceptance_datetime_to_utc() -> None:
    parsed = parse_sec_acceptance_datetime("20231102183012")

    assert parsed.tzinfo == UTC
    assert parsed.isoformat() == "2023-11-02T22:30:12+00:00"


def test_sec_event_date_uses_us_equity_trading_session_rules() -> None:
    before_open = parse_sec_acceptance_datetime("20231103080000")
    during_session = parse_sec_acceptance_datetime("20231103120000")
    after_close_friday = parse_sec_acceptance_datetime("20231103160100")
    saturday = parse_sec_acceptance_datetime("20231104120000")

    assert sec_event_date_from_acceptance_time(before_open).isoformat() == "2023-11-03"
    assert sec_event_date_from_acceptance_time(during_session).isoformat() == "2023-11-03"
    assert sec_event_date_from_acceptance_time(after_close_friday).isoformat() == "2023-11-06"
    assert sec_event_date_from_acceptance_time(saturday).isoformat() == "2023-11-06"


def test_sec_event_date_resolution_exposes_market_calendar_audit_fields() -> None:
    after_close_friday = parse_sec_acceptance_datetime("20231103160100")

    resolution = sec_event_date_resolution_from_acceptance_time(after_close_friday)

    assert resolution.raw_event_date.isoformat() == "2023-11-03"
    assert resolution.resolved_event_date.isoformat() == "2023-11-06"
    assert resolution.event_date_policy == "after_close"
    assert resolution.market_open_utc.isoformat() == "2023-11-06T14:30:00+00:00"
    assert resolution.market_close_utc.isoformat() == "2023-11-06T21:00:00+00:00"


def test_extract_annual_filings_filters_10k() -> None:
    filings = extract_annual_filings(load_fixture())

    assert len(filings) == 1
    assert filings[0]["form"] == "10-K"
    assert filings[0]["primaryDocument"] == "aapl-20230930.htm"


def test_filing_row_to_manifest_record(tmp_path: Path) -> None:
    universe_record = load_universe_manifest("configs/universe/us_large_cap_2010.csv")[0]
    filing = extract_annual_filings(load_fixture())[0]
    document_hash = sha256_bytes(b"<html>fixture</html>")

    record = filing_row_to_manifest_record(
        universe_record=universe_record,
        filing_row=filing,
        document_hash_sha256=document_hash,
    )

    assert record.document_type == "10-K"
    assert record.ticker == "AAPL"
    assert record.fiscal_year == 2023
    assert record.event_date.isoformat() == "2023-11-03"
    assert record.raw_filing_date.isoformat() == "2023-11-03"
    assert record.available_time_utc.isoformat() == "2023-11-02T22:30:12+00:00"
    assert record.acceptance_time_utc is not None
    assert record.acceptance_time_utc.isoformat() == "2023-11-02T22:30:12+00:00"
    assert record.event_date_policy == "after_close"
    assert record.resolved_event_date is not None
    assert record.resolved_event_date.isoformat() == "2023-11-03"
    assert record.resolved_event_time_version == "market-calendar-event-date-v1"
    assert record.source_url_or_path.endswith("320193/000032019323000106/aapl-20230930.htm")

    output_path = tmp_path / "document_manifest.jsonl"
    write_manifest_jsonl([record], output_path)
    assert output_path.read_text(encoding="utf-8").count("\n") == 1


def test_build_document_manifest_from_submissions_requires_document_hash() -> None:
    universe_record = load_universe_manifest("configs/universe/us_large_cap_2010.csv")[0]
    submissions = load_fixture()
    filing = extract_annual_filings(submissions)[0]
    document_url = build_archive_document_url(
        universe_record.cik,
        filing["accessionNumber"],
        filing["primaryDocument"],
    )

    records_without_hash = build_document_manifest_from_submissions(
        universe_records=[universe_record],
        submissions_by_cik={universe_record.cik: submissions},
        document_hashes_by_url={},
    )
    records_with_hash = build_document_manifest_from_submissions(
        universe_records=[universe_record],
        submissions_by_cik={universe_record.cik: submissions},
        document_hashes_by_url={document_url: sha256_bytes(b"<html>fixture</html>")},
    )

    assert records_without_hash == []
    assert len(records_with_hash) == 1
    assert records_with_hash[0].document_id.startswith("sec:0000320193")
