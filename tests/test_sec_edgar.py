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
    assert record.available_time_utc.isoformat() == "2023-11-02T22:30:12+00:00"
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
