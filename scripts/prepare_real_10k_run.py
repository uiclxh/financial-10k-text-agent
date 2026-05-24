from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from text_factor_lab.calendar import resolve_event_date
from text_factor_lab.data.sec_edgar import (
    SEC_SUBMISSIONS_BASE_URL,
    build_archive_document_url,
    build_submissions_url,
    extract_annual_filings,
    normalize_cik,
    parse_sec_acceptance_datetime,
    zip_recent_filings,
)
from text_factor_lab.schemas import DocumentManifestRecord

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_LICENSE_NOTE = "Public SEC EDGAR filing; comply with SEC fair-access policy."
YAHOO_LICENSE_NOTE = (
    "Yahoo Finance chart endpoint; public exploratory use only. "
    "Replace with CRSP or licensed vendor data for formal research."
)


@dataclass(frozen=True)
class CompanySpec:
    ticker: str
    company_name: str
    sector: str
    industry: str
    include_in_10k_run: bool = True
    note: str = ""


COMPANIES = [
    CompanySpec("MSFT", "Microsoft Corporation", "Information Technology", "Software"),
    CompanySpec("NFLX", "Netflix, Inc.", "Communication Services", "Entertainment"),
    CompanySpec("NKE", "NIKE, Inc.", "Consumer Discretionary", "Textiles Apparel & Luxury Goods"),
    CompanySpec(
        "MCD",
        "McDonald's Corporation",
        "Consumer Discretionary",
        "Hotels Restaurants & Leisure",
    ),
    CompanySpec(
        "META",
        "Meta Platforms, Inc.",
        "Communication Services",
        "Interactive Media & Services",
    ),
    CompanySpec(
        "SBUX",
        "Starbucks Corporation",
        "Consumer Discretionary",
        "Hotels Restaurants & Leisure",
    ),
    CompanySpec(
        "SONY",
        "Sony Group Corporation",
        "Consumer Discretionary",
        "Consumer Electronics",
        include_in_10k_run=False,
        note="Foreign private issuer; normally files 20-F rather than 10-K.",
    ),
    CompanySpec("V", "Visa Inc.", "Financials", "Transaction & Payment Processing Services"),
    CompanySpec("XOM", "Exxon Mobil Corporation", "Energy", "Oil Gas & Consumable Fuels"),
    CompanySpec("LLY", "Eli Lilly and Company", "Health Care", "Pharmaceuticals"),
]


LARGE_CAP_10K_COMPANIES = [
    CompanySpec("AAPL", "Apple Inc.", "Information Technology", "Technology Hardware"),
    CompanySpec("MSFT", "Microsoft Corporation", "Information Technology", "Software"),
    CompanySpec("NVDA", "NVIDIA Corporation", "Information Technology", "Semiconductors"),
    CompanySpec("GOOGL", "Alphabet Inc.", "Communication Services", "Interactive Media"),
    CompanySpec("AMZN", "Amazon.com, Inc.", "Consumer Discretionary", "Broadline Retail"),
    CompanySpec("META", "Meta Platforms, Inc.", "Communication Services", "Interactive Media"),
    CompanySpec("AVGO", "Broadcom Inc.", "Information Technology", "Semiconductors"),
    CompanySpec("TSLA", "Tesla, Inc.", "Consumer Discretionary", "Automobiles"),
    CompanySpec("JPM", "JPMorgan Chase & Co.", "Financials", "Banks"),
    CompanySpec("WMT", "Walmart Inc.", "Consumer Staples", "Consumer Staples Distribution"),
    CompanySpec("LLY", "Eli Lilly and Company", "Health Care", "Pharmaceuticals"),
    CompanySpec("V", "Visa Inc.", "Financials", "Transaction & Payment Processing"),
    CompanySpec("ORCL", "Oracle Corporation", "Information Technology", "Software"),
    CompanySpec("MA", "Mastercard Incorporated", "Financials", "Transaction & Payment Processing"),
    CompanySpec("XOM", "Exxon Mobil Corporation", "Energy", "Oil Gas & Consumable Fuels"),
    CompanySpec(
        "COST",
        "Costco Wholesale Corporation",
        "Consumer Staples",
        "Consumer Staples Distribution",
    ),
    CompanySpec("HD", "The Home Depot, Inc.", "Consumer Discretionary", "Specialty Retail"),
    CompanySpec("PG", "The Procter & Gamble Company", "Consumer Staples", "Household Products"),
    CompanySpec("JNJ", "Johnson & Johnson", "Health Care", "Pharmaceuticals"),
    CompanySpec("NFLX", "Netflix, Inc.", "Communication Services", "Entertainment"),
    CompanySpec("ABBV", "AbbVie Inc.", "Health Care", "Biotechnology"),
    CompanySpec("BAC", "Bank of America Corporation", "Financials", "Banks"),
    CompanySpec("KO", "The Coca-Cola Company", "Consumer Staples", "Beverages"),
    CompanySpec("CRM", "Salesforce, Inc.", "Information Technology", "Software"),
    CompanySpec("CVX", "Chevron Corporation", "Energy", "Oil Gas & Consumable Fuels"),
    CompanySpec("AMD", "Advanced Micro Devices, Inc.", "Information Technology", "Semiconductors"),
    CompanySpec("MRK", "Merck & Co., Inc.", "Health Care", "Pharmaceuticals"),
    CompanySpec(
        "CSCO",
        "Cisco Systems, Inc.",
        "Information Technology",
        "Communications Equipment",
    ),
    CompanySpec("PEP", "PepsiCo, Inc.", "Consumer Staples", "Beverages"),
    CompanySpec("TMO", "Thermo Fisher Scientific Inc.", "Health Care", "Life Sciences Tools"),
    CompanySpec("MCD", "McDonald's Corporation", "Consumer Discretionary", "Restaurants"),
    CompanySpec("ABT", "Abbott Laboratories", "Health Care", "Health Care Equipment"),
    CompanySpec("AMGN", "Amgen Inc.", "Health Care", "Biotechnology"),
    CompanySpec(
        "IBM",
        "International Business Machines Corporation",
        "Information Technology",
        "IT Services",
    ),
    CompanySpec("GE", "GE Aerospace", "Industrials", "Aerospace & Defense"),
    CompanySpec("CAT", "Caterpillar Inc.", "Industrials", "Machinery"),
    CompanySpec("GS", "The Goldman Sachs Group, Inc.", "Financials", "Capital Markets"),
    CompanySpec("MS", "Morgan Stanley", "Financials", "Capital Markets"),
    CompanySpec("NOW", "ServiceNow, Inc.", "Information Technology", "Software"),
    CompanySpec("AXP", "American Express Company", "Financials", "Consumer Finance"),
    CompanySpec("DIS", "The Walt Disney Company", "Communication Services", "Entertainment"),
    CompanySpec("QCOM", "QUALCOMM Incorporated", "Information Technology", "Semiconductors"),
    CompanySpec(
        "TXN",
        "Texas Instruments Incorporated",
        "Information Technology",
        "Semiconductors",
    ),
    CompanySpec("INTU", "Intuit Inc.", "Information Technology", "Software"),
    CompanySpec("VZ", "Verizon Communications Inc.", "Communication Services", "Telecom Services"),
    CompanySpec("CMCSA", "Comcast Corporation", "Communication Services", "Media"),
    CompanySpec("PM", "Philip Morris International Inc.", "Consumer Staples", "Tobacco"),
    CompanySpec("UNP", "Union Pacific Corporation", "Industrials", "Ground Transportation"),
    CompanySpec("RTX", "RTX Corporation", "Industrials", "Aerospace & Defense"),
    CompanySpec("LOW", "Lowe's Companies, Inc.", "Consumer Discretionary", "Specialty Retail"),
    CompanySpec("ISRG", "Intuitive Surgical, Inc.", "Health Care", "Health Care Equipment"),
    CompanySpec("SPGI", "S&P Global Inc.", "Financials", "Capital Markets"),
    CompanySpec(
        "BKNG",
        "Booking Holdings Inc.",
        "Consumer Discretionary",
        "Hotels Restaurants & Leisure",
    ),
    CompanySpec("PFE", "Pfizer Inc.", "Health Care", "Pharmaceuticals"),
    CompanySpec("HON", "Honeywell International Inc.", "Industrials", "Industrial Conglomerates"),
    CompanySpec("UPS", "United Parcel Service, Inc.", "Industrials", "Air Freight & Logistics"),
    CompanySpec("NKE", "NIKE, Inc.", "Consumer Discretionary", "Textiles Apparel & Luxury Goods"),
    CompanySpec("COP", "ConocoPhillips", "Energy", "Oil Gas & Consumable Fuels"),
    CompanySpec("SCHW", "The Charles Schwab Corporation", "Financials", "Capital Markets"),
    CompanySpec("T", "AT&T Inc.", "Communication Services", "Telecom Services"),
    CompanySpec("DE", "Deere & Company", "Industrials", "Machinery"),
    CompanySpec("BA", "The Boeing Company", "Industrials", "Aerospace & Defense"),
    CompanySpec("SBUX", "Starbucks Corporation", "Consumer Discretionary", "Restaurants"),
    CompanySpec("MDLZ", "Mondelez International, Inc.", "Consumer Staples", "Food Products"),
    CompanySpec("GILD", "Gilead Sciences, Inc.", "Health Care", "Biotechnology"),
    CompanySpec("ADP", "Automatic Data Processing, Inc.", "Industrials", "Professional Services"),
    CompanySpec("MMC", "Marsh & McLennan Companies, Inc.", "Financials", "Insurance"),
    CompanySpec("BLK", "BlackRock, Inc.", "Financials", "Capital Markets"),
    CompanySpec("C", "Citigroup Inc.", "Financials", "Banks"),
    CompanySpec("LMT", "Lockheed Martin Corporation", "Industrials", "Aerospace & Defense"),
    CompanySpec(
        "AMAT",
        "Applied Materials, Inc.",
        "Information Technology",
        "Semiconductor Equipment",
    ),
    CompanySpec("SYK", "Stryker Corporation", "Health Care", "Health Care Equipment"),
    CompanySpec("TJX", "The TJX Companies, Inc.", "Consumer Discretionary", "Specialty Retail"),
    CompanySpec("PLD", "Prologis, Inc.", "Real Estate", "Industrial REITs"),
    CompanySpec("DUK", "Duke Energy Corporation", "Utilities", "Electric Utilities"),
    CompanySpec("SO", "The Southern Company", "Utilities", "Electric Utilities"),
    CompanySpec("CVS", "CVS Health Corporation", "Health Care", "Health Care Services"),
    CompanySpec("ELV", "Elevance Health, Inc.", "Health Care", "Managed Health Care"),
    CompanySpec("CI", "The Cigna Group", "Health Care", "Managed Health Care"),
    CompanySpec("MO", "Altria Group, Inc.", "Consumer Staples", "Tobacco"),
    CompanySpec("USB", "U.S. Bancorp", "Financials", "Banks"),
    CompanySpec("ADI", "Analog Devices, Inc.", "Information Technology", "Semiconductors"),
    CompanySpec("REGN", "Regeneron Pharmaceuticals, Inc.", "Health Care", "Biotechnology"),
    CompanySpec("VRTX", "Vertex Pharmaceuticals Incorporated", "Health Care", "Biotechnology"),
    CompanySpec("PANW", "Palo Alto Networks, Inc.", "Information Technology", "Software"),
    CompanySpec("MU", "Micron Technology, Inc.", "Information Technology", "Semiconductors"),
    CompanySpec(
        "LRCX",
        "Lam Research Corporation",
        "Information Technology",
        "Semiconductor Equipment",
    ),
    CompanySpec("KLAC", "KLA Corporation", "Information Technology", "Semiconductor Equipment"),
    CompanySpec("ZTS", "Zoetis Inc.", "Health Care", "Pharmaceuticals"),
    CompanySpec("BSX", "Boston Scientific Corporation", "Health Care", "Health Care Equipment"),
    CompanySpec("APD", "Air Products and Chemicals, Inc.", "Materials", "Chemicals"),
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare public real-data artifacts for the 2016-2025 10-K research run."
    )
    parser.add_argument(
        "--universe-mode",
        choices=["selected", "large_cap_10k"],
        default="selected",
        help=(
            "selected keeps the original curated 10-name run; large_cap_10k "
            "uses a wider public 10-K seed universe."
        ),
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        help="Optional cap for testing a prefix of the selected universe mode.",
    )
    parser.add_argument(
        "--company-seed-file",
        help=(
            "Optional CSV with ticker, company_name, sector, industry, "
            "include_in_10k_run, note. Overrides the built-in universe list."
        ),
    )
    parser.add_argument("--output-root", default="data/real_10k_2016_2025")
    parser.add_argument(
        "--config-output",
        default="configs/text_factor_lab/real_10k_2016_2025.yaml",
    )
    parser.add_argument("--universe-output", default="configs/universe/real_10k_2016_2025.csv")
    parser.add_argument(
        "--user-agent",
        default="financial-10k-text-agent/0.14 contact: linxihang0810@gmail.com",
    )
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--price-start", default="2015-01-01")
    parser.add_argument("--price-end", default=date.today().isoformat())
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    args = parser.parse_args()

    companies = company_specs_for_mode(
        args.universe_mode,
        max_companies=args.max_companies,
        company_seed_file=args.company_seed_file,
    )
    if args.universe_mode == "large_cap_10k":
        if args.output_root == "data/real_10k_2016_2025":
            args.output_root = "data/real_10k_large_universe_2016_2025"
        if args.config_output == "configs/text_factor_lab/real_10k_2016_2025.yaml":
            args.config_output = "configs/text_factor_lab/real_10k_large_universe_2016_2025.yaml"
        if args.universe_output == "configs/universe/real_10k_2016_2025.csv":
            args.universe_output = "configs/universe/real_10k_large_universe_2016_2025.csv"

    output_root = Path(args.output_root)
    raw_filings_dir = output_root / "raw_filings"
    output_root.mkdir(parents=True, exist_ok=True)
    raw_filings_dir.mkdir(parents=True, exist_ok=True)

    ticker_map = fetch_sec_company_ticker_map(args.user_agent)
    universe_rows = build_universe_rows(
        ticker_map,
        companies=companies,
        selection_date=f"{args.start_year}-01-01",
    )
    write_universe_csv(universe_rows, args.universe_output)

    manifest_records: list[DocumentManifestRecord] = []
    filing_coverage: list[dict[str, Any]] = []
    for company in companies:
        if not company.include_in_10k_run:
            filing_coverage.append(
                {
                    "ticker": company.ticker,
                    "company_name": company.company_name,
                    "status": "excluded_from_10k_run",
                    "reason": company.note,
                    "filing_count": 0,
                    "years": [],
                }
            )
            continue
        ticker_meta = ticker_map.get(company.ticker)
        if ticker_meta is None:
            filing_coverage.append(
                {
                    "ticker": company.ticker,
                    "company_name": company.company_name,
                    "status": "missing_sec_cik",
                    "reason": "Ticker not found in SEC company_tickers.json.",
                    "filing_count": 0,
                    "years": [],
                }
            )
            continue
        cik = ticker_meta["cik"]
        annual_filing_rows = collect_all_annual_filing_rows(
            cik=cik,
            submissions=fetch_json(build_submissions_url(cik), args.user_agent),
            user_agent=args.user_agent,
            sleep_seconds=args.sleep_seconds,
        )
        annual_filings = select_annual_10k_filings(
            annual_filing_rows,
            start_year=args.start_year,
            end_year=args.end_year,
        )
        records_for_company: list[DocumentManifestRecord] = []
        for filing in annual_filings:
            accession = str(filing["accessionNumber"])
            primary_document = str(filing["primaryDocument"])
            url = build_archive_document_url(cik, accession, primary_document)
            safe_name = safe_filename(
                f"{company.ticker}_{filing['report_year']}_{accession}_{primary_document}"
            )
            output_path = raw_filings_dir / safe_name
            if output_path.exists():
                payload = output_path.read_bytes()
            else:
                payload = fetch_bytes(url, args.user_agent, sleep_seconds=args.sleep_seconds)
                output_path.write_bytes(payload)
            records_for_company.append(
                manifest_record_for_filing(
                    company=company,
                    cik=cik,
                    filing=filing,
                    local_path=output_path,
                    document_hash=hashlib.sha256(payload).hexdigest(),
                )
            )
        manifest_records.extend(records_for_company)
        filing_coverage.append(
            {
                "ticker": company.ticker,
                "company_name": company.company_name,
                "status": "included",
                "filing_count": len(records_for_company),
                "years": sorted(record.fiscal_year for record in records_for_company),
            }
        )

    manifest_path = output_root / "document_manifest.jsonl"
    write_jsonl_manifest(manifest_records, manifest_path)

    price_tickers = [
        company.ticker
        for company in companies
        if company.include_in_10k_run and company.ticker in ticker_map
    ] + ["SPY"]
    price_rows, price_coverage = fetch_yahoo_prices(
        tickers=price_tickers,
        start=args.price_start,
        end=args.price_end,
        sleep_seconds=args.sleep_seconds,
    )
    prices_path = output_root / "prices.csv"
    write_prices_csv(price_rows, prices_path)

    config_path = Path(args.config_output)
    write_config(
        config_path=config_path,
        output_root=output_root,
        raw_filings_dir=raw_filings_dir,
        manifest_path=manifest_path,
        prices_path=prices_path,
        universe_path=Path(args.universe_output),
        user_agent=args.user_agent,
        start_year=args.start_year,
        end_year=args.end_year,
        universe_mode=args.universe_mode,
    )

    coverage_report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "run_scope": "public_real_data_exploratory_10k_run",
        "universe_mode": args.universe_mode,
        "document_source": "SEC EDGAR submissions API and filing archives",
        "price_source": "Yahoo Finance chart endpoint",
        "price_source_note": YAHOO_LICENSE_NOTE,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "companies_requested": [company.ticker for company in companies],
        "companies_in_10k_run": [
            company.ticker for company in companies if company.include_in_10k_run
        ],
        "filing_coverage": filing_coverage,
        "document_count": len(manifest_records),
        "price_coverage": price_coverage,
        "config_path": str(config_path),
        "universe_path": str(args.universe_output),
        "manifest_path": str(manifest_path),
        "prices_path": str(prices_path),
    }
    (output_root / "data_coverage_report.json").write_text(
        json.dumps(coverage_report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(coverage_report, indent=2))
    return 0


def fetch_sec_company_ticker_map(user_agent: str) -> dict[str, dict[str, str]]:
    payload = fetch_json(SEC_COMPANY_TICKERS_URL, user_agent)
    output: dict[str, dict[str, str]] = {}
    for item in payload.values():
        ticker = str(item["ticker"]).upper()
        output[ticker] = {
            "ticker": ticker,
            "cik": normalize_cik(str(item["cik_str"])),
            "title": str(item["title"]),
        }
    return output


def company_specs_for_mode(
    universe_mode: str,
    *,
    max_companies: int | None,
    company_seed_file: str | None,
) -> list[CompanySpec]:
    if company_seed_file:
        companies = read_company_seed_file(company_seed_file)
    elif universe_mode == "large_cap_10k":
        companies = LARGE_CAP_10K_COMPANIES
    else:
        companies = COMPANIES
    if max_companies is not None:
        return list(companies[:max_companies])
    return list(companies)


def read_company_seed_file(path: str | Path) -> list[CompanySpec]:
    records: list[CompanySpec] = []
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            records.append(
                CompanySpec(
                    ticker=str(row["ticker"]).upper(),
                    company_name=str(row["company_name"]),
                    sector=str(row.get("sector") or ""),
                    industry=str(row.get("industry") or ""),
                    include_in_10k_run=str(
                        row.get("include_in_10k_run", "true")
                    ).lower()
                    not in {"false", "0", "no"},
                    note=str(row.get("note") or ""),
                )
            )
    return records


def fetch_json(url: str, user_agent: str, *, retries: int = 4) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt >= retries:
                raise
            sleep_for_retry(exc, attempt)
    raise RuntimeError(f"failed to fetch JSON after retries: {url}")


def fetch_bytes(
    url: str,
    user_agent: str,
    *,
    sleep_seconds: float,
    retries: int = 4,
) -> bytes:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=120) as response:
                payload = response.read()
            time.sleep(sleep_seconds)
            return payload
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt >= retries:
                raise
            sleep_for_retry(exc, attempt)
    raise RuntimeError(f"failed to fetch bytes after retries: {url}")


def sleep_for_retry(exc: Exception, attempt: int) -> None:
    delay = min(30.0, 1.5 * (2**attempt))
    print(f"retrying after transient request error: {exc}; sleep={delay:.1f}s")
    time.sleep(delay)


def collect_all_annual_filing_rows(
    *,
    cik: str,
    submissions: dict[str, Any],
    user_agent: str,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    rows = extract_annual_filings(submissions, form_type="10-K")
    for file_meta in submissions.get("filings", {}).get("files", []):
        name = str(file_meta.get("name", ""))
        if not name:
            continue
        archive = fetch_json(f"{SEC_SUBMISSIONS_BASE_URL}/{name}", user_agent)
        rows.extend(row for row in zip_recent_filings(archive) if row.get("form") == "10-K")
        time.sleep(sleep_seconds)
    for row in rows:
        row.setdefault("cik", cik)
    return rows


def select_annual_10k_filings(
    filings: list[dict[str, Any]],
    *,
    start_year: int,
    end_year: int,
) -> list[dict[str, Any]]:
    by_year: dict[int, dict[str, Any]] = {}
    for filing in filings:
        report_date = str(filing.get("reportDate") or "")
        if not report_date:
            continue
        report_year = int(report_date[:4])
        if start_year <= report_year <= end_year and report_year not in by_year:
            filing = dict(filing)
            filing["report_year"] = report_year
            by_year[report_year] = filing
    return [by_year[year] for year in sorted(by_year)]


def manifest_record_for_filing(
    *,
    company: CompanySpec,
    cik: str,
    filing: dict[str, Any],
    local_path: Path,
    document_hash: str,
) -> DocumentManifestRecord:
    accession = str(filing["accessionNumber"])
    acceptance_utc = parse_acceptance_datetime(str(filing["acceptanceDateTime"]))
    filing_date = date.fromisoformat(str(filing["filingDate"]))
    event_resolution = resolve_event_date(
        acceptance_utc,
        exchange="NYSE",
        timezone="America/New_York",
    )
    return DocumentManifestRecord(
        document_id=f"sec:{cik}:{accession}:{filing['primaryDocument']}",
        entity_id=f"CIK{cik}",
        ticker=company.ticker,
        cik=cik,
        company_name=company.company_name,
        document_type="10-K",
        fiscal_year=int(filing["report_year"]),
        fiscal_period="FY",
        source_id="SEC_EDGAR_PUBLIC_ARCHIVE",
        source_url_or_path=str(local_path),
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
        hash_sha256=document_hash,
        license_note=SEC_LICENSE_NOTE,
        parser_version="real-sec-edgar-prep-v0",
    )


def build_universe_rows(
    ticker_map: dict[str, dict[str, str]],
    *,
    companies: list[CompanySpec],
    selection_date: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, company in enumerate(companies, start=1):
        cik = ticker_map.get(company.ticker, {}).get("cik", "")
        rows.append(
            {
                "entity_id": f"CIK{cik}" if cik else f"EXCLUDED_{company.ticker}",
                "ticker": company.ticker,
                "historical_ticker": company.ticker,
                "cik": cik or "0000000000",
                "company_name": company.company_name,
                "sector": company.sector,
                "industry": company.industry,
                "selection_date": selection_date,
                "market_cap_at_selection": str(max(len(companies) - index + 1, 1)),
                "entry_date": selection_date,
                "exit_date": "",
                "delisting_date": "",
                "mapping_source": "SEC_company_tickers_plus_manual_sector_mapping",
                "mapping_available_time_utc": "2016-01-01T00:00:00+00:00",
            }
        )
    return rows


def parse_acceptance_datetime(value: str) -> datetime:
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return parse_sec_acceptance_datetime(value)


def write_universe_csv(rows: list[dict[str, str]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fetch_yahoo_prices(
    *,
    tickers: list[str],
    start: str,
    end: str,
    sleep_seconds: float,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    rows: list[dict[str, str]] = []
    coverage: list[dict[str, Any]] = []
    period1 = int(datetime.fromisoformat(start).replace(tzinfo=UTC).timestamp())
    period2 = int(datetime.fromisoformat(end).replace(tzinfo=UTC).timestamp())
    for ticker in tickers:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{ticker}?period1={period1}&period2={period2}&interval=1d"
            "&events=history&includeAdjustedClose=true"
        )
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 financial-10k-text-agent",
                "Accept": "application/json",
            },
        )
        try:
            payload = None
            for attempt in range(5):
                try:
                    with urlopen(request, timeout=60) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                    break
                except (HTTPError, URLError, TimeoutError) as exc:
                    if attempt >= 4:
                        raise
                    sleep_for_retry(exc, attempt)
            if payload is None:
                raise RuntimeError(f"failed to fetch Yahoo price payload for {ticker}")
            result = payload["chart"]["result"][0]
            timestamps = result["timestamp"]
            adjclose = result["indicators"]["adjclose"][0]["adjclose"]
            ticker_count = 0
            for timestamp, value in zip(timestamps, adjclose, strict=True):
                if value is None:
                    continue
                rows.append(
                    {
                        "date": datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat(),
                        "ticker": ticker,
                        "adj_close": f"{float(value):.10f}",
                    }
                )
                ticker_count += 1
            coverage.append({"ticker": ticker, "status": "ok", "rows": ticker_count})
        except Exception as exc:
            coverage.append({"ticker": ticker, "status": "failed", "error": str(exc), "rows": 0})
        time.sleep(sleep_seconds)
    return rows, coverage


def write_prices_csv(rows: list[dict[str, str]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "ticker", "adj_close"])
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl_manifest(records: list[DocumentManifestRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def write_config(
    *,
    config_path: Path,
    output_root: Path,
    raw_filings_dir: Path,
    manifest_path: Path,
    prices_path: Path,
    universe_path: Path,
    user_agent: str,
    start_year: int,
    end_year: int,
    universe_mode: str,
) -> None:
    run_id = (
        "real_10k_large_universe_2016_2025_public_v0"
        if universe_mode == "large_cap_10k"
        else "real_10k_2016_2025_public_v0"
    )
    universe_name = (
        "real_public_10k_large_cap_seed_universe_2016_2025"
        if universe_mode == "large_cap_10k"
        else "real_public_10k_selected_large_caps_2016_2025"
    )
    payload = {
        "run": {
            "run_id": run_id,
            "run_type": "exploratory_run",
            "random_seed": 42,
            "output_dir": str(Path("runs/text_factor_lab") / run_id),
        },
        "inputs": {
            "document_manifest_path": str(manifest_path),
            "prices_path": str(prices_path),
            "parsed_sections_path": None,
            "raw_filings_dir": str(raw_filings_dir),
            "copy_inputs_to_run_dir": True,
        },
        "universe": {
            "name": universe_name,
            "selection_date": f"{start_year}-01-01",
            "tickers_file": str(universe_path),
            "universe_data_level": "exploratory",
            "survivorship_bias_control": False,
            "allow_delisted_firms": False,
            "historical_ticker_mapping": True,
        },
        "sample": {
            "start_date": f"{start_year}-01-01",
            "end_date": f"{end_year}-12-31",
            "timezone": "America/New_York",
        },
        "text_source": {
            "document_type": "10-K",
            "source": "SEC_EDGAR_PUBLIC_ARCHIVE",
            "sections": ["Risk Factors", "MD&A", "Business", "Legal Proceedings"],
            "require_available_time": True,
            "require_license_note": True,
            "sec_user_agent": user_agent,
        },
        "labels": {
            "targets": ["CAR_1_5", "CAR_1_20", "realized_volatility_1_20"],
            "return_type": "log",
            "portfolio_return_type": "simple",
            "price_field": "adj_close",
            "market_benchmark": "SPY",
            "annualization_days": 252,
        },
        "split": {
            "method": "rolling_year",
            "train_years_min": 5,
            "validation_years": 1,
            "test_years": 1,
            "embargo_days": 20,
        },
        "features": {
            "methods": ["dictionary_tone", "tfidf"],
            "dictionary_tone": {"dictionaries": ["builtin_mvp_toy_financial_dictionary"]},
            "tfidf": {
                "max_features": 1000 if universe_mode == "selected" else 3000,
                "ngram_range": [1, 2],
                "min_df": 3 if universe_mode == "selected" else 5,
                "max_df": 0.95,
                "fit_scope": "train_window_only",
                "write_long_features": False,
                "matrix_store_dir": str(Path("runs/text_factor_lab") / run_id / "feature_matrices"),
                "matrix_index_file": str(
                    Path("runs/text_factor_lab") / run_id / "feature_matrix_index.json"
                ),
                "svd_components": 16 if universe_mode == "selected" else 32,
            },
        },
        "models": {
            "enabled": ["historical_mean", "industry_mean", "ridge", "xgboost"],
            "tuning": {"selection_metric": "validation_rank_ic", "save_tuning_log": True},
        },
        "backtest": {
            "rebalance_frequency": "event_based",
            "portfolio_method": "top_bottom_quintile",
            "weighting": "equal_weight",
            "holding_window_days": 20,
            "transaction_cost_bps_one_way": 10,
            "sector_neutral": True,
            "newey_west_lag": 19,
            "portfolio_signal_direction": "long_high_score",
            "target_aware_portfolio_policy": "none",
        },
        "audit": {
            "coverage_threshold": 0.45 if universe_mode == "selected" else 0.55,
            "require_license_note": True,
            "require_available_time": True,
            "reject_on_lookahead": True,
            "reject_on_train_test_leakage": True,
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


if __name__ == "__main__":
    raise SystemExit(main())
