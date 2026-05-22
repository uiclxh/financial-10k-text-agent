"""Data acquisition and manifest building."""

from text_factor_lab.data.prices import (
    PriceDataError,
    PricePanel,
    build_price_panel,
    load_price_panel_csv,
)
from text_factor_lab.data.sec_edgar import (
    build_archive_document_url,
    build_document_manifest_from_submissions,
    build_submissions_url,
    extract_annual_filings,
    filing_row_to_manifest_record,
    normalize_cik,
    parse_sec_acceptance_datetime,
    sec_event_date_from_acceptance_time,
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
    "build_price_panel",
    "build_universe_quality_report",
    "build_submissions_url",
    "extract_annual_filings",
    "filing_row_to_manifest_record",
    "load_and_report_universe",
    "load_price_panel_csv",
    "load_universe_manifest",
    "normalize_cik",
    "sec_event_date_from_acceptance_time",
    "parse_sec_acceptance_datetime",
    "PriceDataError",
    "PricePanel",
    "write_manifest_jsonl",
]

