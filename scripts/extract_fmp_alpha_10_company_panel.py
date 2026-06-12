from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from http.client import IncompleteRead
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
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
from text_factor_lab.data.sec_edgar import (
    fetch_json as fetch_sec_json,
)
from text_factor_lab.schemas import DataLicenseManifestRecord, DocumentManifestRecord

FMP_BASE_URL = "https://financialmodelingprep.com"
ALPHA_BASE_URL = "https://www.alphavantage.co/query"
SEC_LICENSE_NOTE = "Public SEC EDGAR filing; comply with SEC fair-access policy."
FMP_LICENSE_NOTE = (
    "Financial Modeling Prep API output stored under private local data paths; "
    "do not commit raw vendor data."
)
ALPHA_LICENSE_NOTE = (
    "Alpha Vantage API output used as backup/cross-check data; do not commit raw output."
)
YAHOO_FALLBACK_LICENSE_NOTE = (
    "Yahoo Finance chart endpoint is used only as a narrow price fallback for "
    "predeclared missing tickers in this applied-grade run; do not treat mixed "
    "vendor prices as CRSP/WRDS-equivalent market data."
)
LM_LICENSE_NOTE = (
    "Loughran-McDonald master dictionary is provided by Notre Dame SRAF for "
    "academic research use. Keep the downloaded CSV under data_private/ unless "
    "redistribution rights are separately confirmed."
)
LM_DICTIONARY_PAGE = "https://sraf.nd.edu/loughranmcdonald-master-dictionary/"


@dataclass(frozen=True)
class CompanySpec:
    ticker: str
    historical_ticker: str
    company_name: str
    cik: str
    sector: str
    industry: str


DEFAULT_COMPANIES = [
    CompanySpec(
        "MSFT",
        "MSFT",
        "Microsoft Corporation",
        "0000789019",
        "Information Technology",
        "Software",
    ),
    CompanySpec(
        "NFLX",
        "NFLX",
        "Netflix, Inc.",
        "0001065280",
        "Communication Services",
        "Entertainment",
    ),
    CompanySpec(
        "NKE",
        "NKE",
        "NIKE, Inc.",
        "0000320187",
        "Consumer Discretionary",
        "Textiles Apparel and Luxury Goods",
    ),
    CompanySpec(
        "MCD",
        "MCD",
        "McDonald's Corporation",
        "0000063908",
        "Consumer Discretionary",
        "Hotels Restaurants and Leisure",
    ),
    CompanySpec(
        "META",
        "FB",
        "Meta Platforms, Inc.",
        "0001326801",
        "Communication Services",
        "Interactive Media and Services",
    ),
    CompanySpec(
        "SBUX",
        "SBUX",
        "Starbucks Corporation",
        "0000829224",
        "Consumer Discretionary",
        "Hotels Restaurants and Leisure",
    ),
    CompanySpec("JPM", "JPM", "JPMorgan Chase & Co.", "0000019617", "Financials", "Banks"),
    CompanySpec(
        "V",
        "V",
        "Visa Inc.",
        "0001403161",
        "Financials",
        "Transaction and Payment Processing Services",
    ),
    CompanySpec(
        "XOM",
        "XOM",
        "Exxon Mobil Corporation",
        "0000034088",
        "Energy",
        "Oil Gas and Consumable Fuels",
    ),
    CompanySpec(
        "LLY",
        "LLY",
        "Eli Lilly and Company",
        "0000059478",
        "Health Care",
        "Pharmaceuticals",
    ),
]
BENCHMARK_TICKER = "SPY"
UNIVERSE_COLUMNS = [
    "entity_id",
    "ticker",
    "historical_ticker",
    "cik",
    "company_name",
    "sector",
    "industry",
    "selection_date",
    "market_cap_at_selection",
    "market_cap_source",
    "market_cap_available_time_utc",
    "market_cap_quality_flag",
    "entry_date",
    "exit_date",
    "delisting_date",
    "mapping_source",
    "mapping_available_time_utc",
]
MEMBERSHIP_COLUMNS = [
    "universe_id",
    "entity_id",
    "ticker",
    "selection_date",
    "entry_date",
    "exit_date",
    "delisting_date",
    "selection_rank",
    "market_cap_at_selection",
    "market_cap_source",
    "market_cap_available_time_utc",
    "market_cap_quality_flag",
    "price_at_selection",
    "shares_outstanding_at_selection",
    "liquidity_filter_pass",
    "source",
    "source_version",
]


@dataclass(frozen=True)
class ExtractionConfig:
    companies: list[CompanySpec]
    start_date: str
    end_date: str
    filing_start_year: int
    filing_end_year: int
    selection_date: str
    output_root: Path
    fmp_api_key: str | None
    alpha_api_key: str | None
    sec_user_agent: str | None
    lm_dictionary_file: Path | None
    dry_run: bool
    skip_sec: bool
    skip_alpha_crosscheck: bool
    yahoo_fallback_tickers: list[str]
    sleep_seconds: float


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract the fixed 10-company applied-grade panel using SEC EDGAR, "
            "FMP primary market data, Alpha Vantage backup checks, and optional "
            "local Loughran-McDonald dictionary input."
        )
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=[company.ticker for company in DEFAULT_COMPANIES],
        help="Target tickers. Defaults to the Sony->JPM 10-company 10-K panel.",
    )
    parser.add_argument("--start-date", default="2015-12-01")
    parser.add_argument("--end-date", default="2026-04-30")
    parser.add_argument("--filing-start-year", type=int, default=2016)
    parser.add_argument("--filing-end-year", type=int, default=2025)
    parser.add_argument("--selection-date", default="2016-01-01")
    parser.add_argument("--output-root", default="data_private")
    parser.add_argument("--fmp-api-key", default=os.environ.get("FMP_API_KEY"))
    parser.add_argument(
        "--alpha-api-key",
        default=os.environ.get("ALPHAVANTAGE_API_KEY")
        or os.environ.get("ALPHA_VANTAGE_API_KEY"),
    )
    parser.add_argument("--sec-user-agent", default=os.environ.get("SEC_USER_AGENT"))
    parser.add_argument("--lm-dictionary-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-sec", action="store_true")
    parser.add_argument("--skip-alpha-crosscheck", action="store_true")
    parser.add_argument(
        "--yahoo-fallback-tickers",
        nargs="+",
        default=["MCD", "LLY"],
        help=(
            "Tickers allowed to use Yahoo as a price fallback when FMP is unavailable. "
            "Defaults to MCD and LLY only."
        ),
    )
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    args = parser.parse_args()

    company_by_ticker = {company.ticker: company for company in DEFAULT_COMPANIES}
    companies = [company_by_ticker[ticker.upper()] for ticker in normalize_tickers(args.tickers)]
    config = ExtractionConfig(
        companies=companies,
        start_date=args.start_date,
        end_date=args.end_date,
        filing_start_year=args.filing_start_year,
        filing_end_year=args.filing_end_year,
        selection_date=args.selection_date,
        output_root=Path(args.output_root),
        fmp_api_key=args.fmp_api_key,
        alpha_api_key=args.alpha_api_key,
        sec_user_agent=args.sec_user_agent,
        lm_dictionary_file=args.lm_dictionary_file,
        dry_run=args.dry_run,
        skip_sec=args.skip_sec,
        skip_alpha_crosscheck=args.skip_alpha_crosscheck,
        yahoo_fallback_tickers=normalize_yahoo_fallback_tickers(
            args.yahoo_fallback_tickers,
            args.tickers,
        ),
        sleep_seconds=args.sleep_seconds,
    )
    if config.dry_run:
        print_plan(config)
        return 0
    if not config.fmp_api_key:
        raise SystemExit("Missing FMP_API_KEY. Set FMP_API_KEY or pass --fmp-api-key.")
    if not config.skip_sec and not config.sec_user_agent:
        raise SystemExit("Missing SEC_USER_AGENT. Set SEC_USER_AGENT or pass --sec-user-agent.")

    extract_panel(config)
    print(f"FMP/Alpha applied-grade private extraction completed under {config.output_root}")
    return 0


def normalize_tickers(values: list[str]) -> list[str]:
    allowed = {company.ticker for company in DEFAULT_COMPANIES}
    tickers = []
    for value in values:
        ticker = value.strip().upper()
        if ticker not in allowed:
            raise ValueError(f"Unsupported ticker for this fixed panel: {ticker}")
        tickers.append(ticker)
    return sorted(set(tickers))


def normalize_yahoo_fallback_tickers(
    values: list[str],
    requested_tickers: list[str],
) -> list[str]:
    requested = set(normalize_tickers(requested_tickers))
    fallback = []
    for value in values:
        ticker = value.strip().upper()
        if ticker not in requested:
            raise ValueError(
                f"Yahoo fallback ticker must be in requested fixed panel: {ticker}"
            )
        fallback.append(ticker)
    return sorted(set(fallback))


def print_plan(config: ExtractionConfig) -> None:
    print("FMP + Alpha Vantage + SEC 10-company extraction plan")
    print(f"tickers={', '.join(company.ticker for company in config.companies)}")
    print(f"benchmark={BENCHMARK_TICKER}")
    print(f"price_window={config.start_date}..{config.end_date}")
    print(f"filing_years={config.filing_start_year}..{config.filing_end_year}")
    print(f"output_root={config.output_root}")
    print("primary_market_data=FMP historical EOD adjusted close")
    print("backup_checks=Alpha Vantage listing status and optional price cross-check")
    print(
        "yahoo_price_fallback="
        + (", ".join(config.yahoo_fallback_tickers) or "disabled")
    )
    print("dictionary=Loughran-McDonald local CSV copy when --lm-dictionary-file is supplied")


def extract_panel(config: ExtractionConfig) -> None:
    sec_dir = config.output_root / "sec"
    market_dir = config.output_root / "market"
    metadata_dir = config.output_root / "metadata"
    dictionaries_dir = config.output_root / "dictionaries"
    for directory in [sec_dir, market_dir, metadata_dir, dictionaries_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    profile_rows = load_fmp_profiles(config)
    marketcap_rows = load_fmp_market_caps(config)
    existing_prices = load_existing_prices(market_dir / "prices_with_returns.csv")
    price_rows = load_fmp_prices(config, existing_prices=existing_prices)
    prices = build_prices_with_returns(price_rows)
    security_master = build_security_master(config, profile_rows)
    membership = build_universe_membership(
        config,
        security_master,
        profile_rows,
        marketcap_rows,
        prices,
    )
    entity_links = build_entity_links(config)
    listing_status = load_listing_status(config)
    symbol_changes = load_fmp_symbol_changes(config)
    delisted_companies = load_fmp_delisted_companies(config)

    write_csv(security_master, metadata_dir / "security_master.csv")
    write_csv(membership[UNIVERSE_COLUMNS], metadata_dir / "tickers.csv")
    write_csv(membership[MEMBERSHIP_COLUMNS], metadata_dir / "universe_membership.csv")
    write_csv(entity_links, metadata_dir / "entity_link_history.csv")
    write_csv(listing_status, metadata_dir / "listing_status.csv")
    write_csv(symbol_changes, metadata_dir / "symbol_changes.csv")
    write_csv(delisted_companies, metadata_dir / "fmp_delisted_companies.csv")
    write_csv(prices, market_dir / "prices_with_returns.csv")
    write_csv(prices[prices["ticker"] == BENCHMARK_TICKER], market_dir / "spy_benchmark.csv")
    write_csv(marketcap_rows, market_dir / "daily_marketcap.csv")
    corporate_actions = pd.DataFrame(
        columns=["date", "ticker", "action_type", "value", "source"]
    )
    write_csv(corporate_actions, market_dir / "corporate_actions.csv")

    price_quality = build_price_quality_report(
        prices,
        benchmark_ticker=BENCHMARK_TICKER,
        expected_tickers=[company.ticker for company in config.companies],
    )
    write_json(price_quality, market_dir / "price_quality_report.json")
    write_json(
        build_data_provenance(config, price_quality),
        metadata_dir / "data_provenance.json",
    )
    write_license_manifest(config, metadata_dir)
    write_dictionary_artifacts(config, dictionaries_dir)

    if not config.skip_sec:
        manifest_records = extract_sec_filings(config, sec_dir / "raw_filings")
        write_jsonl_manifest(manifest_records, sec_dir / "document_manifest.jsonl")
        write_json(
            build_filing_coverage_report(config, manifest_records),
            sec_dir / "filing_coverage_report.json",
        )


def load_fmp_profiles(config: ExtractionConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for company in config.companies:
        payload = fetch_fmp_json(
            "/stable/profile",
            {"symbol": company.ticker},
            config.fmp_api_key,
        )
        row = payload[0] if isinstance(payload, list) and payload else {}
        rows.append({"ticker": company.ticker, **row})
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def load_existing_prices(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        prices = pd.read_csv(path)
    except Exception:
        return None
    if prices.empty or "ticker" not in prices or "date" not in prices:
        return None
    prices["ticker"] = prices["ticker"].astype(str).str.upper()
    return prices


def existing_price_rows_for_ticker(
    existing_prices: pd.DataFrame | None,
    ticker: str,
) -> list[dict[str, Any]]:
    if existing_prices is None or existing_prices.empty:
        return []
    if "closeadj" not in existing_prices:
        return []
    subset = existing_prices[
        (existing_prices["ticker"].astype(str).str.upper() == ticker.upper())
        & pd.to_numeric(existing_prices["closeadj"], errors="coerce").notna()
    ].copy()
    if subset.empty:
        return []
    return subset.to_dict("records")


def load_fmp_prices(
    config: ExtractionConfig,
    *,
    existing_prices: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ticker in [company.ticker for company in config.companies] + [BENCHMARK_TICKER]:
        cached_rows = existing_price_rows_for_ticker(existing_prices, ticker)
        if cached_rows:
            rows.extend(cached_rows)
            continue
        try:
            payload = fetch_fmp_json(
                "/stable/historical-price-eod/full",
                {
                    "symbol": ticker,
                    "from": config.start_date,
                    "to": config.end_date,
                },
                config.fmp_api_key,
            )
            historical = payload.get("historical", []) if isinstance(payload, dict) else payload
            for item in historical:
                rows.append(
                    {
                        "ticker": ticker,
                        **item,
                        "source": "fmp_historical_price_eod_full",
                        "source_version": "fmp_historical_price_eod_full",
                    }
                )
        except Exception as exc:
            if ticker in config.yahoo_fallback_tickers:
                try:
                    rows.extend(load_yahoo_price_rows(ticker, config))
                    time.sleep(config.sleep_seconds)
                    continue
                except Exception as yahoo_exc:
                    error = f"FMP failed: {exc}; Yahoo fallback failed: {yahoo_exc}"
            else:
                error = str(exc)
            rows.append(
                {
                    "ticker": ticker,
                    "status": "price_unavailable",
                    "error": error,
                    "source": "fmp_historical_price_eod_full",
                    "source_version": "fmp_historical_price_eod_full",
                }
            )
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def load_yahoo_price_rows(ticker: str, config: ExtractionConfig) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(config.start_date).replace(tzinfo=UTC)
    end = datetime.fromisoformat(config.end_date).replace(tzinfo=UTC) + timedelta(days=1)
    params = urllib.parse.urlencode(
        {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{params}"
    request = Request(
        url,
        headers={
            "User-Agent": config.sec_user_agent
            or "financial-10k-text-agent contact:research@example.com"
        },
    )
    with urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("chart", {}).get("result") or []
    if not result:
        error = payload.get("chart", {}).get("error")
        raise RuntimeError(f"Yahoo chart returned no result for {ticker}: {error}")
    chart = result[0]
    timestamps = chart.get("timestamp") or []
    indicators = chart.get("indicators", {})
    quote = (indicators.get("quote") or [{}])[0]
    adjclose = (indicators.get("adjclose") or [{}])[0].get("adjclose") or []
    rows: list[dict[str, Any]] = []
    for index, timestamp in enumerate(timestamps):
        closeadj = adjclose[index] if index < len(adjclose) else None
        close = _sequence_value(quote.get("close"), index)
        rows.append(
            {
                "ticker": ticker,
                "date": datetime.fromtimestamp(timestamp, UTC).date().isoformat(),
                "open": _sequence_value(quote.get("open"), index),
                "high": _sequence_value(quote.get("high"), index),
                "low": _sequence_value(quote.get("low"), index),
                "close": close,
                "adjClose": closeadj if closeadj is not None else close,
                "volume": _sequence_value(quote.get("volume"), index),
                "source": "yahoo_chart_price_fallback",
                "source_version": "yahoo_chart_v8_fallback",
            }
        )
    if not rows:
        raise RuntimeError(f"Yahoo chart returned no rows for {ticker}")
    return rows


def _sequence_value(values: list[Any] | None, index: int) -> Any:
    if values is None or index >= len(values):
        return None
    return values[index]


def load_fmp_market_caps(config: ExtractionConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for company in config.companies:
        try:
            payload = fetch_fmp_json(
                "/stable/historical-market-capitalization",
                {
                    "symbol": company.ticker,
                    "from": config.start_date,
                    "to": config.end_date,
                },
                config.fmp_api_key,
            )
            historical = (
                payload.get("historical", payload)
                if isinstance(payload, dict)
                else payload
            )
            if isinstance(historical, list):
                for item in historical:
                    rows.append({"ticker": company.ticker, **item})
        except Exception as exc:
            rows.append(
                {
                    "ticker": company.ticker,
                    "status": "unavailable",
                    "error": str(exc),
                    "source": "fmp_historical_market_capitalization",
                }
            )
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def load_fmp_symbol_changes(config: ExtractionConfig) -> pd.DataFrame:
    try:
        payload = fetch_fmp_json("/stable/symbol-change", {}, config.fmp_api_key)
    except Exception as exc:
        return pd.DataFrame([{"status": "failed", "error": str(exc)}])
    rows = payload if isinstance(payload, list) else []
    wanted = {company.ticker for company in config.companies} | {
        company.historical_ticker for company in config.companies
    }
    return pd.DataFrame(
        [
            row
            for row in rows
            if str(row.get("oldSymbol", "")).upper() in wanted
            or str(row.get("newSymbol", "")).upper() in wanted
        ]
    )


def load_fmp_delisted_companies(config: ExtractionConfig) -> pd.DataFrame:
    try:
        payload = fetch_fmp_json(
            "/stable/delisted-companies",
            {"page": "0", "limit": "100"},
            config.fmp_api_key,
        )
    except Exception as exc:
        return pd.DataFrame([{"status": "failed", "error": str(exc)}])
    rows = payload if isinstance(payload, list) else []
    wanted = {company.ticker for company in config.companies}
    return pd.DataFrame([row for row in rows if str(row.get("symbol", "")).upper() in wanted])


def load_listing_status(config: ExtractionConfig) -> pd.DataFrame:
    if config.skip_alpha_crosscheck or not config.alpha_api_key:
        return pd.DataFrame(
            [
                {
                    "ticker": company.ticker,
                    "status": "not_checked",
                    "source": "alpha_vantage_listing_status",
                }
                for company in config.companies
            ]
        )
    payload = fetch_alpha_csv({"function": "LISTING_STATUS"}, config.alpha_api_key)
    wanted = {company.ticker for company in config.companies}
    if payload.empty:
        return pd.DataFrame()
    symbol_column = "symbol" if "symbol" in payload.columns else payload.columns[0]
    return payload[payload[symbol_column].astype(str).str.upper().isin(wanted)].copy()


def build_prices_with_returns(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return empty_prices_frame()
    prices = raw.copy()
    if "date" not in prices:
        return empty_prices_frame()
    prices["ticker"] = prices["ticker"].astype(str).str.upper()
    prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
    prices["closeadj"] = pd.to_numeric(
        prices.get("adjClose", prices.get("closeadj", prices.get("close"))),
        errors="coerce",
    )
    for column in ["open", "high", "low", "close", "volume"]:
        if column not in prices:
            prices[column] = pd.NA
        prices[column] = pd.to_numeric(prices[column], errors="coerce")
    prices = prices.dropna(subset=["date", "ticker", "closeadj"]).sort_values(["ticker", "date"])
    prices["ret"] = prices.groupby("ticker", observed=True)["closeadj"].pct_change()
    prices["simple_return"] = prices["ret"]
    prices["log_ret"] = np.log1p(prices["ret"])
    prices["log_return"] = prices["log_ret"]
    prices["retx"] = prices["ret"]
    prices["dlret"] = pd.NA
    prices["delisting_return"] = pd.NA
    prices["ret_with_dlret"] = prices["ret"]
    prices["dlstcd"] = pd.NA
    prices["permno"] = prices["ticker"]
    prices["permco"] = prices["ticker"]
    prices["prc"] = prices["closeadj"]
    prices["shrout"] = pd.NA
    if "source" not in prices:
        prices["source"] = "fmp_historical_price_eod_full"
    prices["source"] = prices["source"].fillna("fmp_historical_price_eod_full")
    if "source_version" not in prices:
        prices["source_version"] = prices["source"]
    prices["source_version"] = prices["source_version"].fillna(prices["source"])
    return prices[
        [
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "closeadj",
            "volume",
            "ret",
            "simple_return",
            "log_ret",
            "log_return",
            "retx",
            "dlret",
            "delisting_return",
            "ret_with_dlret",
            "dlstcd",
            "prc",
            "shrout",
            "permno",
            "permco",
            "source",
            "source_version",
        ]
    ]


def empty_prices_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "closeadj",
            "volume",
            "ret",
            "simple_return",
            "log_ret",
            "log_return",
            "retx",
            "dlret",
            "delisting_return",
            "ret_with_dlret",
            "dlstcd",
            "prc",
            "shrout",
            "permno",
            "permco",
            "source",
            "source_version",
        ]
    )


def build_security_master(config: ExtractionConfig, profiles: pd.DataFrame) -> pd.DataFrame:
    profile_by_ticker = (
        profiles.set_index(profiles["ticker"].astype(str).str.upper()) if not profiles.empty else {}
    )
    rows = []
    for company in config.companies:
        profile = (
            profile_by_ticker.loc[company.ticker]
            if company.ticker in profile_by_ticker
            else {}
        )
        rows.append(
            {
                "entity_id": f"CIK{normalize_cik(company.cik)}",
                "permno": "",
                "permco": "",
                "gvkey": "",
                "cik": normalize_cik(company.cik),
                "ticker": company.ticker,
                "historical_ticker": company.historical_ticker,
                "company_name": profile.get("companyName", company.company_name)
                if hasattr(profile, "get")
                else company.company_name,
                "name_start_date": config.selection_date,
                "name_end_date": "",
                "exchange": (
                    profile.get("exchangeShortName")
                    if hasattr(profile, "get")
                    else None
                )
                or "Unknown",
                "share_class": "common",
                "security_type": "equity",
                "sic": "",
                "naics": "",
                "gics_sector": profile.get("sector", company.sector)
                if hasattr(profile, "get")
                else company.sector,
                "gics_industry": profile.get("industry", company.industry)
                if hasattr(profile, "get")
                else company.industry,
                "source": "fmp_profile_sec_cik_manual_verified",
                "source_version": "fmp_profile_v3",
                "available_time_utc": f"{config.selection_date}T00:00:00Z",
            }
        )
    return pd.DataFrame(rows)


def build_universe_membership(
    config: ExtractionConfig,
    security_master: pd.DataFrame,
    profiles: pd.DataFrame,
    marketcaps: pd.DataFrame,
    prices: pd.DataFrame,
) -> pd.DataFrame:
    _ = security_master
    marketcap_lookup = market_cap_metadata_at_selection(
        marketcaps=marketcaps,
        profiles=profiles,
        prices=prices,
        selection_date=config.selection_date,
    )
    price_lookup = price_at_selection(prices, config.selection_date)
    rows = []
    for company in config.companies:
        market_cap_metadata = marketcap_lookup.get(company.ticker, {})
        rows.append(
            {
                "entity_id": f"CIK{normalize_cik(company.cik)}",
                "ticker": company.ticker,
                "historical_ticker": company.historical_ticker,
                "cik": normalize_cik(company.cik),
                "company_name": company.company_name,
                "sector": company.sector,
                "industry": company.industry,
                "selection_date": config.selection_date,
                "market_cap_at_selection": market_cap_metadata.get("market_cap_at_selection"),
                "market_cap_source": market_cap_metadata.get("market_cap_source"),
                "market_cap_available_time_utc": market_cap_metadata.get(
                    "market_cap_available_time_utc"
                ),
                "market_cap_quality_flag": market_cap_metadata.get(
                    "market_cap_quality_flag"
                ),
                "entry_date": config.selection_date,
                "exit_date": "",
                "delisting_date": "",
                "mapping_source": "sec_cik_fmp_profile_manual_fb_meta",
                "mapping_available_time_utc": f"{config.selection_date}T00:00:00Z",
                "universe_id": "fixed_10_company_us_10k_fmp_alpha_pilot",
                "price_at_selection": price_lookup.get(company.ticker),
                "shares_outstanding_at_selection": market_cap_metadata.get(
                    "shares_outstanding_at_selection",
                    "",
                ),
                "liquidity_filter_pass": True,
                "source": "fmp_profile_marketcap_sec_cik",
                "source_version": "fmp_alpha_pilot_v1",
            }
        )
    frame = pd.DataFrame(rows)
    frame["_rank_value"] = pd.to_numeric(frame["market_cap_at_selection"], errors="coerce")
    frame = frame.sort_values(
        "_rank_value",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)
    frame["selection_rank"] = range(1, len(frame) + 1)
    return frame.drop(columns=["_rank_value"])


def build_entity_links(config: ExtractionConfig) -> pd.DataFrame:
    rows = []
    for company in config.companies:
        rows.append(
            {
                "entity_id": f"CIK{normalize_cik(company.cik)}",
                "cik": normalize_cik(company.cik),
                "ticker": company.ticker,
                "permno": "",
                "gvkey": "",
                "link_start_date": config.selection_date,
                "link_end_date": "",
                "link_type": (
                    "manual_fb_meta_ticker_change"
                    if company.ticker == "META"
                    else "sec_cik_current_ticker"
                ),
                "link_confidence": 1.0 if company.ticker != "META" else 0.95,
                "source": "sec_submissions_fmp_symbol_change_manual_review",
            }
        )
    return pd.DataFrame(rows)


def market_cap_at_selection(marketcaps: pd.DataFrame, selection_date: str) -> dict[str, float]:
    if marketcaps.empty:
        return {}
    frame = marketcaps.copy()
    if "date" not in frame:
        return {}
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    value_column = "marketCap" if "marketCap" in frame else "marketcap"
    if value_column not in frame:
        return {}
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    selection = pd.Timestamp(selection_date)
    lookup: dict[str, float] = {}
    valid = frame.dropna(subset=["date", value_column])
    for ticker, group in valid.groupby("ticker", observed=True):
        before = group[group["date"] <= selection].sort_values("date")
        row = before.iloc[-1] if not before.empty else group.sort_values("date").iloc[0]
        lookup[ticker] = float(row[value_column])
    return lookup


def market_cap_metadata_at_selection(
    *,
    marketcaps: pd.DataFrame,
    profiles: pd.DataFrame,
    prices: pd.DataFrame,
    selection_date: str,
) -> dict[str, dict[str, Any]]:
    exact_lookup = market_cap_at_selection(marketcaps, selection_date)
    selection_prices = price_at_selection(prices, selection_date)
    latest_prices = latest_price_lookup(prices)
    profile_market_caps = profile_market_cap_lookup(profiles)
    available_time = f"{datetime.now(UTC).isoformat()}"
    lookup: dict[str, dict[str, Any]] = {}
    for ticker, market_cap in exact_lookup.items():
        selection_price = selection_prices.get(ticker)
        shares = market_cap / selection_price if selection_price and selection_price > 0 else ""
        lookup[ticker] = {
            "market_cap_at_selection": market_cap,
            "market_cap_source": "fmp_historical_market_capitalization",
            "market_cap_available_time_utc": available_time,
            "market_cap_quality_flag": "historical_vendor_value",
            "shares_outstanding_at_selection": shares,
        }
    for ticker, current_market_cap in profile_market_caps.items():
        if ticker in lookup:
            continue
        selection_price = selection_prices.get(ticker)
        latest_price = latest_prices.get(ticker)
        if (
            selection_price is None
            or latest_price is None
            or selection_price <= 0
            or latest_price <= 0
            or current_market_cap <= 0
        ):
            continue
        estimated_shares = current_market_cap / latest_price
        lookup[ticker] = {
            "market_cap_at_selection": float(estimated_shares * selection_price),
            "market_cap_source": (
                "estimated_from_fmp_profile_marketcap_and_price_series"
            ),
            "market_cap_available_time_utc": available_time,
            "market_cap_quality_flag": "applied_grade_estimate_not_crsp",
            "shares_outstanding_at_selection": float(estimated_shares),
        }
    return lookup


def profile_market_cap_lookup(profiles: pd.DataFrame) -> dict[str, float]:
    if profiles.empty or "ticker" not in profiles:
        return {}
    value_column = None
    for candidate in ["marketCap", "mktCap", "market_cap"]:
        if candidate in profiles:
            value_column = candidate
            break
    if value_column is None:
        return {}
    frame = profiles.copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    return {
        str(row["ticker"]): float(row[value_column])
        for _, row in frame.dropna(subset=[value_column]).iterrows()
        if float(row[value_column]) > 0
    }


def latest_price_lookup(prices: pd.DataFrame) -> dict[str, float]:
    if prices.empty or "date" not in prices or "closeadj" not in prices:
        return {}
    frame = prices.copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["closeadj"] = pd.to_numeric(frame["closeadj"], errors="coerce")
    lookup: dict[str, float] = {}
    for ticker, group in frame.dropna(subset=["date", "closeadj"]).groupby(
        "ticker",
        observed=True,
    ):
        row = group.sort_values("date").iloc[-1]
        lookup[str(ticker)] = float(row["closeadj"])
    return lookup


def price_at_selection(prices: pd.DataFrame, selection_date: str) -> dict[str, float]:
    if prices.empty:
        return {}
    selection = pd.Timestamp(selection_date)
    lookup: dict[str, float] = {}
    for ticker, group in prices.groupby("ticker", observed=True):
        before = group[group["date"] <= selection].sort_values("date")
        row = before.iloc[-1] if not before.empty else group.sort_values("date").iloc[0]
        lookup[str(ticker)] = float(row["closeadj"])
    return lookup


def extract_sec_filings(
    config: ExtractionConfig,
    raw_filings_dir: Path,
) -> list[DocumentManifestRecord]:
    raw_filings_dir.mkdir(parents=True, exist_ok=True)
    records: list[DocumentManifestRecord] = []
    assert config.sec_user_agent is not None
    for company in config.companies:
        submissions = fetch_sec_json(
            build_submissions_url(company.cik),
            user_agent=config.sec_user_agent,
        )
        annual_rows = collect_all_10k_rows(
            cik=company.cik,
            submissions=submissions,
            user_agent=config.sec_user_agent,
            sleep_seconds=config.sleep_seconds,
        )
        filings = select_annual_10k_filings(
            annual_rows,
            start_year=config.filing_start_year,
            end_year=config.filing_end_year,
        )
        for filing in filings:
            accession = str(filing["accessionNumber"])
            primary_document = str(filing["primaryDocument"])
            url = build_archive_document_url(company.cik, accession, primary_document)
            output_path = (
                raw_filings_dir
                / company.ticker
                / safe_filename(f"{filing['report_year']}_{accession}_{primary_document}")
            )
            if output_path.exists():
                payload = output_path.read_bytes()
            else:
                payload = fetch_bytes(url, user_agent=config.sec_user_agent)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(payload)
                time.sleep(config.sleep_seconds)
            records.append(
                manifest_record_for_filing(
                    company=company,
                    filing=filing,
                    local_path=output_path,
                    document_hash=hashlib.sha256(payload).hexdigest(),
                )
            )
        time.sleep(config.sleep_seconds)
    return records


def collect_all_10k_rows(
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
        archive = fetch_sec_json(f"{SEC_SUBMISSIONS_BASE_URL}/{name}", user_agent=user_agent)
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
        if str(filing.get("form")) != "10-K":
            continue
        report_date = str(filing.get("reportDate") or "")
        if not report_date:
            continue
        report_year = int(report_date[:4])
        if start_year <= report_year <= end_year and report_year not in by_year:
            row = dict(filing)
            row["report_year"] = report_year
            by_year[report_year] = row
    return [by_year[year] for year in sorted(by_year)]


def manifest_record_for_filing(
    *,
    company: CompanySpec,
    filing: dict[str, Any],
    local_path: Path,
    document_hash: str,
) -> DocumentManifestRecord:
    acceptance_utc = parse_acceptance_datetime(str(filing["acceptanceDateTime"]))
    event_resolution = resolve_event_date(
        acceptance_utc,
        exchange="NYSE",
        timezone="America/New_York",
    )
    accession = str(filing["accessionNumber"])
    return DocumentManifestRecord(
        document_id=f"sec:{normalize_cik(company.cik)}:{accession}:{filing['primaryDocument']}",
        entity_id=f"CIK{normalize_cik(company.cik)}",
        ticker=company.ticker,
        cik=normalize_cik(company.cik),
        company_name=company.company_name,
        document_type="10-K",
        fiscal_year=int(filing["report_year"]),
        fiscal_period="FY",
        source_id="SEC_EDGAR",
        source_url_or_path=str(local_path),
        retrieval_time_utc=datetime.now(UTC),
        available_time_utc=acceptance_utc,
        event_time_utc=acceptance_utc,
        event_date=event_resolution.resolved_event_date,
        raw_filing_date=date.fromisoformat(str(filing["filingDate"])),
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
        parser_version="sec-fmp-alpha-pilot-v1",
    )


def parse_acceptance_datetime(value: str) -> datetime:
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return parse_sec_acceptance_datetime(value)


def build_price_quality_report(
    prices: pd.DataFrame,
    *,
    benchmark_ticker: str,
    expected_tickers: list[str] | None = None,
) -> dict[str, Any]:
    if prices.empty:
        return {
            "status": "empty",
            "coverage": 0.0,
            "tickers": [
                {
                    "ticker": ticker,
                    "expected_days": 0,
                    "observed_days": 0,
                    "missing_days": 0,
                    "missing_dates": [],
                    "first_date": None,
                    "last_date": None,
                    "status": "missing_all_prices",
                }
                for ticker in sorted(set(expected_tickers or []) | {benchmark_ticker})
            ],
        }
    benchmark_dates = set(prices.loc[prices["ticker"] == benchmark_ticker, "date"].dt.date)
    reports = []
    total_expected = 0
    total_observed = 0
    ticker_groups = {
        str(ticker): group for ticker, group in prices.groupby("ticker", observed=True)
    }
    all_tickers = sorted(set(ticker_groups) | set(expected_tickers or []) | {benchmark_ticker})
    for ticker in all_tickers:
        group = ticker_groups.get(ticker)
        if group is None or group.empty:
            missing_dates = sorted(date_value.isoformat() for date_value in benchmark_dates)
            total_expected += len(benchmark_dates)
            reports.append(
                {
                    "ticker": ticker,
                    "expected_days": len(benchmark_dates),
                    "observed_days": 0,
                    "missing_days": len(benchmark_dates),
                    "missing_dates": missing_dates[:50],
                    "first_date": None,
                    "last_date": None,
                    "status": "missing_all_prices",
                }
            )
            continue
        observed_dates = set(group["date"].dt.date)
        expected_dates = benchmark_dates if ticker != benchmark_ticker else observed_dates
        missing_dates = sorted(
            date_value.isoformat() for date_value in expected_dates - observed_dates
        )
        total_expected += len(expected_dates)
        total_observed += len(expected_dates) - len(missing_dates)
        reports.append(
            {
                "ticker": ticker,
                "expected_days": len(expected_dates),
                "observed_days": len(expected_dates) - len(missing_dates),
                "missing_days": len(missing_dates),
                "missing_dates": missing_dates[:50],
                "first_date": group["date"].min().date().isoformat(),
                "last_date": group["date"].max().date().isoformat(),
                "status": "ok" if not missing_dates else "missing_some_prices",
            }
        )
    return {
        "status": "ok",
        "benchmark_ticker": benchmark_ticker,
        "coverage": (total_observed / total_expected) if total_expected else 0.0,
        "tickers": reports,
    }


def build_filing_coverage_report(
    config: ExtractionConfig,
    records: list[DocumentManifestRecord],
) -> dict[str, Any]:
    rows = []
    for company in config.companies:
        years = sorted(record.fiscal_year for record in records if record.ticker == company.ticker)
        expected_years = set(range(config.filing_start_year, config.filing_end_year + 1))
        rows.append(
            {
                "ticker": company.ticker,
                "expected_years": sorted(expected_years),
                "observed_years": years,
                "missing_years": sorted(expected_years - set(years)),
                "filing_count": len(years),
            }
        )
    return {"status": "ok", "filings": rows}


def build_data_provenance(
    config: ExtractionConfig,
    price_quality: dict[str, Any],
) -> dict[str, Any]:
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "panel_type": "10-company applied-grade non-WRDS non-Nasdaq pilot",
        "target_tickers": [company.ticker for company in config.companies],
        "replacement_policy": (
            "SONY excluded because it is a 20-F foreign private issuer; "
            "JPM is used instead."
        ),
        "benchmark": BENCHMARK_TICKER,
        "filing_source": "SEC EDGAR submissions API and Archives",
        "primary_market_source": (
            "Financial Modeling Prep historical EOD adjusted close with Yahoo "
            "chart fallback for declared missing tickers"
        ),
        "backup_source": (
            "Alpha Vantage listing status / optional price checks; Yahoo chart "
            "fallback restricted to predeclared missing tickers"
        ),
        "mixed_source_policy": (
            "Yahoo fallback is allowed only for the configured yahoo_fallback_tickers; "
            "the run must be reported as a mixed-source applied run."
        ),
        "yahoo_fallback_tickers": config.yahoo_fallback_tickers,
        "dictionary_source": "Notre Dame SRAF Loughran-McDonald dictionary",
        "price_window": {"start": config.start_date, "end": config.end_date},
        "filing_years": {
            "start": config.filing_start_year,
            "end": config.filing_end_year,
        },
        "boundaries": [
            "Not survivorship-free.",
            "No CRSP delisting returns.",
            "Fixed active-company 10-K pilot panel.",
            "Portfolio evidence should remain secondary to prediction metrics.",
        ],
        "price_quality": price_quality,
    }


def write_license_manifest(config: ExtractionConfig, metadata_dir: Path) -> None:
    manifest = DataLicenseManifestRecord(
        data_stack="sec_fmp_yahoo_alpha_lm_fixed_10_company_pilot",
        market_data_provider="fmp_alpha",
        filing_provider="sec_edgar",
        price_source="mixed_fmp_yahoo_adjusted_close",
        return_source="mixed_fmp_yahoo_closeadj_log_return",
        delisting_return_source="fmp_alpha_listing_status_no_crsp_dlret",
        link_source="sec_cik_fmp_symbol_change_manual_fb_meta",
        data_owner="SEC, Financial Modeling Prep, Alpha Vantage, Notre Dame SRAF",
        data_rights_scope="private local research artifacts only",
        input_files={
            "document_manifest": "data_private/sec/document_manifest.jsonl",
            "prices": "data_private/market/prices_with_returns.csv",
            "security_master": "data_private/metadata/security_master.csv",
            "membership": "data_private/metadata/universe_membership.csv",
            "entity_links": "data_private/metadata/entity_link_history.csv",
            "lm_dictionary": "data_private/dictionaries/lm_dictionary.csv",
        },
        permitted_public_outputs=[
            "compact result summaries",
            "audit summaries",
            "schema and configuration files",
        ],
        license_note=(
            f"{SEC_LICENSE_NOTE} {FMP_LICENSE_NOTE} "
            f"{YAHOO_FALLBACK_LICENSE_NOTE} {ALPHA_LICENSE_NOTE} {LM_LICENSE_NOTE}"
        ),
        raw_data_committed=False,
        allow_public_yahoo_fallback=True,
        created_at_utc=datetime.now(UTC),
    )
    write_json(manifest.model_dump(mode="json"), metadata_dir / "license_manifest.json")
    (metadata_dir / "license_manifest.yaml").write_text(
        yaml.safe_dump(manifest.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def write_dictionary_artifacts(config: ExtractionConfig, dictionaries_dir: Path) -> None:
    note_path = dictionaries_dir / "lm_dictionary_license_note.txt"
    note_path.write_text(
        f"{LM_LICENSE_NOTE}\nSource page: {LM_DICTIONARY_PAGE}\n",
        encoding="utf-8",
    )
    target = dictionaries_dir / "lm_dictionary.csv"
    if config.lm_dictionary_file is not None:
        target.write_bytes(config.lm_dictionary_file.read_bytes())
    elif not target.exists():
        target.write_text(
            "word,negative,positive,uncertainty,litigious,strong_modal,weak_modal,constraining\n",
            encoding="utf-8",
        )


def fetch_fmp_json(path: str, params: dict[str, str], api_key: str | None) -> Any:
    query = urllib.parse.urlencode({**params, "apikey": api_key or ""})
    url = f"{FMP_BASE_URL}{path}?{query}"
    return fetch_json_url(url)


def fetch_alpha_csv(params: dict[str, str], api_key: str) -> pd.DataFrame:
    query = urllib.parse.urlencode({**params, "apikey": api_key})
    url = f"{ALPHA_BASE_URL}?{query}"
    request = Request(url, headers={"User-Agent": "financial-10k-text-agent"})
    with urlopen(request, timeout=60) as response:
        return pd.read_csv(response)


def fetch_json_url(url: str, *, retries: int = 3) -> Any:
    request = Request(
        url,
        headers={"User-Agent": "financial-10k-text-agent", "Accept": "application/json"},
    )
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, IncompleteRead) as exc:
            if isinstance(exc, HTTPError) and exc.code == 402:
                raise
            if attempt >= retries:
                raise
            sleep_for_retry(exc, attempt)
    raise RuntimeError(f"failed to fetch JSON: {url}")


def fetch_bytes(url: str, *, user_agent: str, retries: int = 3) -> bytes:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=120) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, IncompleteRead) as exc:
            if attempt >= retries:
                raise
            sleep_for_retry(exc, attempt)
    raise RuntimeError(f"failed to fetch bytes: {url}")


def sleep_for_retry(exc: Exception, attempt: int) -> None:
    delay = min(30.0, 1.5 * (2**attempt))
    print(f"retrying after request error: {exc}; sleep={delay:.1f}s")
    time.sleep(delay)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def write_jsonl_manifest(records: list[DocumentManifestRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")


if __name__ == "__main__":
    raise SystemExit(main())
