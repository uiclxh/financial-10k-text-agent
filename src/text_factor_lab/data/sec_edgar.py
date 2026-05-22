from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from text_factor_lab.calendar import EventDateResolution, resolve_event_date
from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.universe import UniverseRecord

SEC_SUBMISSIONS_BASE_URL = "https://data.sec.gov/submissions"
SEC_ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"
SEC_LICENSE_NOTE = "Public SEC EDGAR filing; comply with SEC fair-access policy."
SEC_ACCEPTANCE_TIMEZONE = ZoneInfo("America/New_York")


def normalize_cik(cik: str) -> str:
    cleaned = cik.strip()
    if not cleaned.isdigit():
        raise ValueError("CIK must contain only digits")
    if len(cleaned) > 10:
        raise ValueError("CIK must not exceed 10 digits")
    return cleaned.zfill(10)


def cik_for_archive_url(cik: str) -> str:
    return str(int(normalize_cik(cik)))


def accession_no_dashes(accession_number: str) -> str:
    return accession_number.replace("-", "")


def build_submissions_url(cik: str) -> str:
    return f"{SEC_SUBMISSIONS_BASE_URL}/CIK{normalize_cik(cik)}.json"


def build_archive_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    return (
        f"{SEC_ARCHIVES_BASE_URL}/"
        f"{cik_for_archive_url(cik)}/"
        f"{accession_no_dashes(accession_number)}/"
        f"{primary_document}"
    )


def build_headers(user_agent: str) -> dict[str, str]:
    if not user_agent.strip():
        raise ValueError("SEC requests require a non-empty User-Agent")
    return {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }


def fetch_json(url: str, *, user_agent: str, timeout_seconds: int = 30) -> dict[str, Any]:
    request = Request(url, headers=build_headers(user_agent))
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str, *, user_agent: str, timeout_seconds: int = 30) -> bytes:
    headers = build_headers(user_agent)
    if "www.sec.gov" in url:
        headers["Host"] = "www.sec.gov"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_sec_acceptance_datetime(value: str) -> datetime:
    local_dt = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=SEC_ACCEPTANCE_TIMEZONE)
    return local_dt.astimezone(UTC)


def sec_event_date_resolution_from_acceptance_time(
    acceptance_time_utc: datetime,
    *,
    exchange: str = "NYSE",
) -> EventDateResolution:
    return resolve_event_date(
        acceptance_time_utc,
        exchange=exchange,
        timezone="America/New_York",
    )


def sec_event_date_from_acceptance_time(
    acceptance_time_utc: datetime,
    *,
    holidays: set[date] | None = None,
) -> date:
    del holidays
    return sec_event_date_resolution_from_acceptance_time(
        acceptance_time_utc,
    ).resolved_event_date


def zip_recent_filings(recent: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(recent.keys())
    if not keys:
        return []
    row_count = len(recent[keys[0]])
    rows: list[dict[str, Any]] = []
    for index in range(row_count):
        rows.append({key: recent[key][index] for key in keys})
    return rows


def extract_annual_filings(
    submissions: dict[str, Any],
    *,
    form_type: str = "10-K",
) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    rows = zip_recent_filings(recent)
    return [row for row in rows if row.get("form") == form_type]


def document_id_for_filing(cik: str, accession_number: str, primary_document: str) -> str:
    return f"sec:{normalize_cik(cik)}:{accession_number}:{primary_document}"


def filing_row_to_manifest_record(
    *,
    universe_record: UniverseRecord,
    filing_row: dict[str, Any],
    document_hash_sha256: str,
) -> DocumentManifestRecord:
    accession_number = str(filing_row["accessionNumber"])
    primary_document = str(filing_row["primaryDocument"])
    acceptance_utc = parse_sec_acceptance_datetime(str(filing_row["acceptanceDateTime"]))
    filing_date = date.fromisoformat(str(filing_row["filingDate"]))
    event_resolution = sec_event_date_resolution_from_acceptance_time(acceptance_utc)
    fiscal_year = int(str(filing_row.get("reportDate") or filing_date)[:4])

    return DocumentManifestRecord(
        document_id=document_id_for_filing(
            universe_record.cik,
            accession_number,
            primary_document,
        ),
        entity_id=universe_record.entity_id,
        ticker=universe_record.ticker,
        cik=universe_record.cik,
        company_name=universe_record.company_name,
        document_type=str(filing_row["form"]),
        fiscal_year=fiscal_year,
        fiscal_period="FY",
        source_id="SEC_EDGAR",
        source_url_or_path=build_archive_document_url(
            universe_record.cik,
            accession_number,
            primary_document,
        ),
        retrieval_time_utc=datetime.now(UTC),
        available_time_utc=acceptance_utc,
        event_time_utc=acceptance_utc,
        event_date=event_resolution.resolved_event_date,
        raw_filing_date=filing_date,
        acceptance_time_utc=acceptance_utc,
        market_open_utc=event_resolution.market_open_utc,
        market_close_utc=event_resolution.market_close_utc,
        is_trading_day=event_resolution.is_trading_day,
        is_early_close=event_resolution.is_early_close,
        event_date_policy=event_resolution.event_date_policy,
        resolved_event_date=event_resolution.resolved_event_date,
        resolved_event_time_version=event_resolution.resolver_version,
        timezone="America/New_York",
        hash_sha256=document_hash_sha256,
        license_note=SEC_LICENSE_NOTE,
        parser_version="sec-edgar-data-v0",
    )


def build_document_manifest_from_submissions(
    *,
    universe_records: list[UniverseRecord],
    submissions_by_cik: dict[str, dict[str, Any]],
    document_hashes_by_url: dict[str, str],
    form_type: str = "10-K",
    max_filings_per_company: int | None = None,
) -> list[DocumentManifestRecord]:
    records: list[DocumentManifestRecord] = []
    for universe_record in universe_records:
        submissions = submissions_by_cik.get(normalize_cik(universe_record.cik))
        if submissions is None:
            continue

        filings = extract_annual_filings(submissions, form_type=form_type)
        if max_filings_per_company is not None:
            filings = filings[:max_filings_per_company]

        for filing in filings:
            document_url = build_archive_document_url(
                universe_record.cik,
                str(filing["accessionNumber"]),
                str(filing["primaryDocument"]),
            )
            document_hash = document_hashes_by_url.get(document_url)
            if document_hash is None:
                continue
            records.append(
                filing_row_to_manifest_record(
                    universe_record=universe_record,
                    filing_row=filing,
                    document_hash_sha256=document_hash,
                )
            )
    return records


def write_manifest_jsonl(records: list[DocumentManifestRecord], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def download_filing_document(
    *,
    url: str,
    output_path: str | Path,
    user_agent: str,
    sleep_seconds: float = 0.1,
) -> str:
    payload = fetch_bytes(url, user_agent=user_agent)
    time.sleep(sleep_seconds)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_bytes(payload)
