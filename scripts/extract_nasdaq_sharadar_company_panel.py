from __future__ import annotations

import argparse
import os
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

try:
    from scripts.extract_wrds_crsp_company_panel import (
        CIK_BY_TICKER,
        DEFAULT_TICKERS,
        SECTOR_BY_TICKER,
        date_string,
        write_csv,
    )
except ModuleNotFoundError:
    from extract_wrds_crsp_company_panel import (
        CIK_BY_TICKER,
        DEFAULT_TICKERS,
        SECTOR_BY_TICKER,
        date_string,
        write_csv,
    )

NASDAQ_DATA_LINK_BASE = "https://data.nasdaq.com/api/v3/datatables"


@dataclass(frozen=True)
class SharadarExtractionConfig:
    tickers: list[str]
    start_date: str
    end_date: str
    selection_date: str
    output_root: Path
    api_key: str | None
    dry_run: bool


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Nasdaq Data Link / Sharadar company-panel data into the "
            "private data_private/ layout expected by text_factor_lab."
        )
    )
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--start-date", default="2016-01-01")
    parser.add_argument("--end-date", default="2025-12-31")
    parser.add_argument("--selection-date", default="2016-01-01")
    parser.add_argument("--output-root", default="data_private")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("NASDAQ_DATA_LINK_API_KEY"),
        help="Nasdaq Data Link API key. Defaults to NASDAQ_DATA_LINK_API_KEY.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = SharadarExtractionConfig(
        tickers=normalize_tickers(args.tickers),
        start_date=args.start_date,
        end_date=args.end_date,
        selection_date=args.selection_date,
        output_root=Path(args.output_root),
        api_key=args.api_key,
        dry_run=args.dry_run,
    )
    if config.dry_run:
        print_plan(config)
        return 0
    if not config.api_key:
        raise SystemExit(
            "Missing Nasdaq Data Link API key. Set NASDAQ_DATA_LINK_API_KEY "
            "or pass --api-key."
        )
    extract_company_panel(config)
    print(f"Nasdaq Sharadar private extraction completed under {config.output_root}")
    return 0


def normalize_tickers(values: list[str]) -> list[str]:
    tickers = []
    for value in values:
        ticker = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.\-]+", ticker):
            raise ValueError(f"Unsafe ticker value: {value!r}")
        tickers.append(ticker)
    return sorted(set(tickers))


def print_plan(config: SharadarExtractionConfig) -> None:
    print("Nasdaq Data Link / Sharadar extraction plan")
    print(f"tickers={', '.join(config.tickers)}")
    print(f"sample={config.start_date}..{config.end_date}")
    print(f"selection_date={config.selection_date}")
    print(f"output_root={config.output_root}")
    print("tables=SHARADAR/TICKERS, SHARADAR/SEP, SHARADAR/ACTIONS")


def extract_company_panel(config: SharadarExtractionConfig) -> None:
    sharadar_dir = config.output_root / "sharadar"
    universe_dir = config.output_root / "universe_sharadar"
    sharadar_dir.mkdir(parents=True, exist_ok=True)
    universe_dir.mkdir(parents=True, exist_ok=True)

    tickers = load_sharadar_tickers(config)
    prices_raw = load_sharadar_sep(config)
    actions = load_sharadar_actions(config)
    daily_indicators = load_sharadar_daily(config)
    prices = build_prices_with_returns(prices_raw, tickers, config)
    security_master = build_security_master(tickers, config)
    membership = build_membership(tickers, prices, config, daily_indicators=daily_indicators)
    entity_links = build_entity_links(tickers, config)
    ticker_manifest = build_ticker_manifest(tickers, membership, config)

    write_csv(tickers, sharadar_dir / "tickers_raw.csv")
    write_csv(prices_raw, sharadar_dir / "sep_raw.csv")
    write_csv(actions, sharadar_dir / "actions_raw.csv")
    write_csv(daily_indicators, sharadar_dir / "daily_raw.csv")
    write_csv(prices, sharadar_dir / "prices_with_returns.csv")
    write_csv(security_master, universe_dir / "security_master.csv")
    write_csv(membership, universe_dir / "universe_membership.csv")
    write_csv(entity_links, universe_dir / "entity_link_history.csv")
    write_csv(ticker_manifest, universe_dir / "tickers.csv")


def load_sharadar_tickers(config: SharadarExtractionConfig) -> pd.DataFrame:
    frames = [
        read_table(
            "SHARADAR/TICKERS",
            {"ticker": ticker},
            config.api_key,
        )
        for ticker in config.tickers
    ]
    return pd.concat(frames, ignore_index=True).drop_duplicates("ticker")


def load_sharadar_sep(config: SharadarExtractionConfig) -> pd.DataFrame:
    frames = [
        read_table(
            "SHARADAR/SEP",
            {
                "ticker": ticker,
                "date.gte": config.start_date,
                "date.lte": config.end_date,
            },
            config.api_key,
        )
        for ticker in config.tickers
    ]
    return pd.concat(frames, ignore_index=True)


def load_sharadar_actions(config: SharadarExtractionConfig) -> pd.DataFrame:
    frames = []
    for ticker in config.tickers:
        try:
            frames.append(
                read_table(
                    "SHARADAR/ACTIONS",
                    {
                        "ticker": ticker,
                        "date.gte": config.start_date,
                        "date.lte": config.end_date,
                    },
                    config.api_key,
                )
            )
        except Exception:
            frames.append(pd.DataFrame({"ticker": [ticker]}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_sharadar_daily(config: SharadarExtractionConfig) -> pd.DataFrame:
    frames = []
    for ticker in config.tickers:
        try:
            frames.append(
                read_table(
                    "SHARADAR/DAILY",
                    {
                        "ticker": ticker,
                        "date.gte": config.start_date,
                        "date.lte": config.end_date,
                    },
                    config.api_key,
                )
            )
        except Exception:
            frames.append(pd.DataFrame({"ticker": [ticker]}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def read_table(table: str, params: dict[str, str], api_key: str | None) -> pd.DataFrame:
    query = {**params, "api_key": api_key}
    encoded = urllib.parse.urlencode(query)
    url = f"{NASDAQ_DATA_LINK_BASE}/{table}.csv?{encoded}"
    return pd.read_csv(url)


def build_prices_with_returns(
    sep: pd.DataFrame,
    tickers: pd.DataFrame,
    config: SharadarExtractionConfig,
) -> pd.DataFrame:
    prices = sep.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices["ticker"] = prices["ticker"].astype(str).str.upper()
    close_column = "close" if "close" in prices.columns else "adj_close"
    prices[close_column] = pd.to_numeric(prices[close_column], errors="coerce")
    prices = prices.sort_values(["ticker", "date"])
    prices["ret"] = prices.groupby("ticker", observed=True)[close_column].pct_change()
    prices["retx"] = prices["ret"]
    prices["dlret"] = pd.NA
    prices["delisting_return"] = pd.NA
    prices["ret_with_dlret"] = prices["ret"]
    prices["dlstcd"] = pd.NA
    tickers_by_ticker = tickers.set_index(tickers["ticker"].astype(str).str.upper())
    for ticker, meta in tickers_by_ticker.iterrows():
        if str(meta.get("isdelisted", "")).upper() not in {"Y", "TRUE", "1"}:
            continue
        last_price_date = pd.to_datetime(meta.get("lastpricedate"), errors="coerce")
        if pd.isna(last_price_date):
            continue
        mask = (prices["ticker"] == ticker) & (prices["date"] == last_price_date)
        prices.loc[mask, "dlstcd"] = "SHARADAR_DELISTED_NO_DLRET"
    prices["permno"] = prices["ticker"]
    prices["permco"] = prices["ticker"]
    prices["source_version"] = "nasdaq_sharadar"
    prices["prc"] = prices[close_column]
    prices["shrout"] = pd.NA
    if "volume" not in prices.columns:
        prices["volume"] = pd.NA
    columns = [
        "date",
        "ticker",
        "ret",
        "retx",
        "dlret",
        "delisting_return",
        "ret_with_dlret",
        "dlstcd",
        "prc",
        "shrout",
        "volume",
        "permno",
        "permco",
        "source_version",
    ]
    return prices[columns]


def build_security_master(tickers: pd.DataFrame, config: SharadarExtractionConfig) -> pd.DataFrame:
    rows = []
    for row in tickers.itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        sector = getattr(row, "sector", None) or SECTOR_BY_TICKER.get(ticker, ("Unknown", ""))[0]
        industry = (
            getattr(row, "industry", None) or SECTOR_BY_TICKER.get(ticker, ("", "Unknown"))[1]
        )
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "permno": "",
                "permco": "",
                "gvkey": "",
                "cik": cik,
                "ticker": ticker,
                "historical_ticker": ticker,
                "company_name": getattr(row, "name", ticker),
                "name_start_date": date_string(getattr(row, "firstpricedate", "")),
                "name_end_date": "",
                "exchange": getattr(row, "exchange", "Unknown"),
                "share_class": getattr(row, "category", "Unknown"),
                "security_type": "equity_or_adr",
                "sic": getattr(row, "siccode", "") or "",
                "naics": "",
                "gics_sector": sector,
                "gics_industry": industry,
                "source": "nasdaq_sharadar",
                "source_version": "nasdaq_sharadar",
                "available_time_utc": f"{config.selection_date}T00:00:00Z",
            }
        )
    return pd.DataFrame(rows)


def build_membership(
    tickers: pd.DataFrame,
    prices: pd.DataFrame,
    config: SharadarExtractionConfig,
    daily_indicators: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows = []
    selection = pd.Timestamp(config.selection_date)
    market_caps = build_market_cap_lookup(daily_indicators, selection)
    scale_ranks = {
        str(row.ticker).upper(): market_cap_scale_rank(getattr(row, "scalemarketcap", None))
        for row in tickers.itertuples(index=False)
    }
    for row in tickers.itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        ticker_prices = prices[prices["ticker"] == ticker].sort_values("date")
        before_selection = ticker_prices[ticker_prices["date"] <= selection]
        selection_row = (
            before_selection.iloc[-1]
            if not before_selection.empty
            else (ticker_prices.iloc[0] if not ticker_prices.empty else None)
        )
        price_at_selection = (
            abs(float(selection_row["prc"])) if selection_row is not None else None
        )
        market_cap = market_caps.get(ticker)
        delisting_date = (
            getattr(row, "lastpricedate", "")
            if str(getattr(row, "isdelisted", "")).upper() in {"Y", "TRUE", "1"}
            else ""
        )
        first_price_date = pd.to_datetime(
            getattr(row, "firstpricedate", config.selection_date),
            errors="coerce",
        )
        entry_date = selection if pd.isna(first_price_date) else max(first_price_date, selection)
        rows.append(
            {
                "universe_id": "nasdaq_sharadar_company_panel_2016_2025",
                "entity_id": f"CIK{cik}",
                "ticker": ticker,
                "selection_date": config.selection_date,
                "entry_date": date_string(entry_date) or config.selection_date,
                "exit_date": date_string(getattr(row, "lastpricedate", config.end_date))
                or config.end_date,
                "delisting_date": date_string(delisting_date),
                "selection_rank": None,
                "market_cap_at_selection": market_cap,
                "price_at_selection": price_at_selection,
                "shares_outstanding_at_selection": "",
                "liquidity_filter_pass": True,
                "source": "nasdaq_sharadar",
                "source_version": "nasdaq_sharadar",
            }
        )
    membership = pd.DataFrame(rows)
    if membership.empty:
        return membership
    membership["_scale_rank"] = membership["ticker"].map(scale_ranks).fillna(0).astype(int)
    membership = membership.sort_values(
        ["market_cap_at_selection", "_scale_rank", "ticker"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)
    membership["selection_rank"] = range(1, len(membership) + 1)
    return membership.drop(columns=["_scale_rank"])


def build_market_cap_lookup(
    daily_indicators: pd.DataFrame | None,
    selection: pd.Timestamp,
) -> dict[str, float]:
    if daily_indicators is None or daily_indicators.empty or "marketcap" not in daily_indicators:
        return {}
    frame = daily_indicators.copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["marketcap"] = pd.to_numeric(frame["marketcap"], errors="coerce")
    frame = frame.dropna(subset=["date", "marketcap"]).sort_values(["ticker", "date"])
    values: dict[str, float] = {}
    for ticker, group in frame.groupby("ticker", observed=True):
        before_selection = group[group["date"] <= selection]
        row = before_selection.iloc[-1] if not before_selection.empty else group.iloc[0]
        values[ticker] = float(row["marketcap"]) * 1_000_000.0
    return values


def market_cap_scale_rank(value: object) -> int:
    if value is None or pd.isna(value):
        return 0
    match = re.match(r"\s*(\d+)", str(value))
    return int(match.group(1)) if match else 0


def build_entity_links(tickers: pd.DataFrame, config: SharadarExtractionConfig) -> pd.DataFrame:
    rows = []
    for row in tickers.itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "cik": cik,
                "ticker": ticker,
                "permno": "",
                "gvkey": "",
                "link_start_date": date_string(getattr(row, "firstpricedate", ""))
                or config.selection_date,
                "link_end_date": date_string(getattr(row, "lastpricedate", "")),
                "link_type": "ticker_cik_sharadar_metadata",
                "link_confidence": 0.9 if cik != "0000000000" else 0.5,
                "source": "nasdaq_sharadar_tickers",
            }
        )
    return pd.DataFrame(rows)


def build_ticker_manifest(
    tickers: pd.DataFrame,
    membership: pd.DataFrame,
    config: SharadarExtractionConfig,
) -> pd.DataFrame:
    rows = []
    ticker_meta = tickers.set_index(tickers["ticker"].astype(str).str.upper())
    for row in membership.sort_values("selection_rank").itertuples(index=False):
        ticker = str(row.ticker).upper()
        meta = ticker_meta.loc[ticker]
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        sector, industry = SECTOR_BY_TICKER.get(ticker, ("Unknown", "Unknown"))
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "ticker": ticker,
                "historical_ticker": ticker,
                "cik": cik,
                "company_name": meta.get("name", ticker),
                "sector": meta.get("sector", sector) or sector,
                "industry": meta.get("industry", industry) or industry,
                "selection_date": config.selection_date,
                "market_cap_at_selection": row.market_cap_at_selection,
                "entry_date": row.entry_date,
                "exit_date": row.exit_date,
                "delisting_date": row.delisting_date,
                "mapping_source": "nasdaq_sharadar_tickers",
                "mapping_available_time_utc": f"{config.selection_date}T00:00:00Z",
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    raise SystemExit(main())
