from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from text_factor_lab.parsing import (
    find_item_heading_candidates,
    normalize_sec_document_text,
    parse_sec_10k_sections,
    raw_document_diagnostics,
    read_parsed_sections_jsonl,
    should_parse_sec_filing,
    write_section_artifacts,
)
from text_factor_lab.schemas import DocumentManifestRecord, ParsedSectionRecord


def utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


def sample_manifest() -> DocumentManifestRecord:
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
        event_date=date(2023, 11, 3),
        timezone="America/New_York",
        hash_sha256="a" * 64,
        license_note="Public SEC EDGAR filing; comply with SEC fair-access policy.",
        parser_version="sec-edgar-data-v0",
    )


def load_sample_html() -> str:
    return Path("tests/fixtures/sec_10k_sample_with_toc.html").read_text(encoding="utf-8")


def test_normalize_sec_document_text_removes_html_and_scripts() -> None:
    normalized = normalize_sec_document_text(load_sample_html())

    assert "<h2>" not in normalized
    assert ".hidden" not in normalized
    assert "Item 1. Business" in normalized


def test_heading_candidates_mark_table_of_contents_lines() -> None:
    normalized = normalize_sec_document_text(load_sample_html())
    candidates = find_item_heading_candidates(normalized)

    toc_item_1 = next(candidate for candidate in candidates if candidate.line.endswith("3"))
    body_item_1 = next(
        candidate
        for candidate in candidates
        if candidate.item == "1" and candidate.line == "Item 1. Business"
    )

    assert toc_item_1.is_toc_like is True
    assert body_item_1.is_toc_like is False


def test_parse_sec_10k_sections_ignores_toc_and_records_spans_hashes() -> None:
    result = parse_sec_10k_sections(load_sample_html(), sample_manifest())
    records_by_key = {record.section_key: record for record in result.records}

    assert set(records_by_key) == {"item_1", "item_1a", "item_3", "item_7"}
    assert all(record.parser_status == "parsed" for record in records_by_key.values())
    assert records_by_key["item_1"].char_start is not None
    assert records_by_key["item_1"].char_start > result.normalized_text.index("PART I")
    assert "Apple designs" in result.section_text_by_key["item_1"]
    assert "Risk Factors" not in result.section_text_by_key["item_1"]
    assert records_by_key["item_7"].text_hash_sha256 is not None
    assert len(records_by_key["item_7"].text_hash_sha256 or "") == 64
    assert result.quality_report.parsed_coverage == 1.0
    assert result.quality_report.inline_xbrl_detected is True
    assert result.quality_report.table_tag_count == 1
    assert result.quality_report.sample_review_required is True


def test_missing_section_is_recorded_as_missing_not_silent_success() -> None:
    result = parse_sec_10k_sections(
        "<html><body><h2>Item 1. Business</h2><p>Business text.</p></body></html>",
        sample_manifest(),
        target_sections=["item_1", "item_3"],
    )
    records_by_key = {record.section_key: record for record in result.records}

    assert records_by_key["item_1"].parser_status == "parsed"
    assert records_by_key["item_3"].parser_status == "missing"
    assert "Could not locate Item 3" in (records_by_key["item_3"].failure_reason or "")


def test_write_section_artifacts_round_trips_records(tmp_path: Path) -> None:
    result = parse_sec_10k_sections(load_sample_html(), sample_manifest())

    records = write_section_artifacts(result, tmp_path)
    parsed_sections_path = tmp_path / "parsed_sections.jsonl"
    normalized_text_path = tmp_path / "normalized_document_text.txt"
    quality_path = tmp_path / "parsing_quality_report.json"
    loaded = read_parsed_sections_jsonl(parsed_sections_path)

    assert parsed_sections_path.exists()
    assert normalized_text_path.exists()
    assert quality_path.exists()
    assert len(loaded) == len(records)
    assert all(record.artifact_path for record in loaded if record.parser_status == "parsed")
    assert Path(records[0].artifact_path or "").read_text(encoding="utf-8")

    raw_json = json.loads(parsed_sections_path.read_text(encoding="utf-8").splitlines()[0])
    assert raw_json["source_hash_sha256"] == "a" * 64

    quality_payload = json.loads(quality_path.read_text(encoding="utf-8"))
    assert quality_payload["parsed_sections"] == 4
    assert quality_payload["sample_review_required"] is True


def test_raw_document_diagnostics_detects_inline_xbrl_and_tables() -> None:
    inline_xbrl_detected, table_count = raw_document_diagnostics(load_sample_html())

    assert inline_xbrl_detected is True
    assert table_count == 1


def test_parse_10k_cli_writes_artifacts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from text_factor_lab.cli import main

    manifest_path = tmp_path / "manifest_record.json"
    output_dir = tmp_path / "parsed"
    manifest_path.write_text(sample_manifest().model_dump_json(), encoding="utf-8")

    exit_code = main(
        [
            "parse-10k",
            "--manifest-record",
            str(manifest_path),
            "--document",
            "tests/fixtures/sec_10k_sample_with_toc.html",
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "parsed=4" in captured.out
    assert (output_dir / "parsed_sections.jsonl").exists()


def test_parsed_section_schema_rejects_parsed_record_without_hash() -> None:
    with pytest.raises(ValidationError, match="text_hash_sha256"):
        ParsedSectionRecord(
            section_id="doc:item_1",
            document_id="doc",
            entity_id="entity",
            ticker="AAPL",
            cik="0000320193",
            document_type="10-K",
            fiscal_year=2023,
            section_key="item_1",
            section_name="Business",
            parser_status="parsed",
            char_start=10,
            char_end=20,
            text_length=10,
            text_hash_sha256=None,
            source_hash_sha256="a" * 64,
            artifact_path=None,
            parser_version="parser-v0",
            failure_reason=None,
            created_at_utc=utc(2023, 11, 3),
        )


def test_amendment_policy_excludes_10k_amendments_by_default() -> None:
    assert should_parse_sec_filing("10-K") is True
    assert should_parse_sec_filing("10-K/A") is False
    assert should_parse_sec_filing("10-K/A", amendment_policy="include") is True
