"""Data acquisition and manifest building."""

from text_factor_lab.data.sec_edgar import (
    build_archive_document_url,
    build_document_manifest_from_submissions,
    build_submissions_url,
    extract_annual_filings,
    filing_row_to_manifest_record,
    normalize_cik,
    parse_sec_acceptance_datetime,
    write_manifest_jsonl,
)
from text_factor_lab.data.universe import (
    build_universe_quality_report,
    load_and_report_universe,
    load_universe_manifest,
)

__all__ = [
    "build_archive_document_url",
    "build_document_manifest_from_submissions",
    "build_universe_quality_report",
    "build_submissions_url",
    "extract_annual_filings",
    "filing_row_to_manifest_record",
    "load_and_report_universe",
    "load_universe_manifest",
    "normalize_cik",
    "parse_sec_acceptance_datetime",
    "write_manifest_jsonl",
]
