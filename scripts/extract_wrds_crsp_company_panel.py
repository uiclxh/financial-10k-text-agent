from __future__ import annotations

import argparse
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DEFAULT_TICKERS = [
    "MSFT",
    "NFLX",
    "NKE",
    "MCD",
    "META",
    "SBUX",
    "SONY",
    "V",
    "XOM",
    "LLY",
]

CIK_BY_TICKER = {
    "MSFT": "0000789019",
    "NFLX": "0001065280",
    "NKE": "0000320187",
    "MCD": "0000063908",
    "META": "0001326801",
    "FB": "0001326801",
    "SBUX": "0000829224",
    "SONY": "0000313838",
    "V": "0001403161",
    "XOM": "0000034088",
    "LLY": "0000059478",
}

SECTOR_BY_TICKER = {
    "MSFT": ("Information Technology", "Software"),
    "NFLX": ("Communication Services", "Entertainment"),
    "NKE": ("Consumer Discretionary", "Textiles Apparel and Luxury Goods"),
    "MCD": ("Consumer Discretionary", "Hotels Restaurants and Leisure"),
    "META": ("Communication Services", "Interactive Media and Services"),
    "FB": ("Communication Services", "Interactive Media and Services"),
    "SBUX": ("Consumer Discretionary", "Hotels Restaurants and Leisure"),
    "SONY": ("Consumer Discretionary", "Consumer Electronics"),
    "V": ("Financials", "Transaction and Payment Processing Services"),
    "XOM": ("Energy", "Oil Gas and Consumable Fuels"),
    "LLY": ("Health Care", "Pharmaceuticals"),
}


@dataclass(frozen=True)
class ExtractionConfig:
    tickers: list[str]
    start_date: str
    end_date: str
    selection_date: str
    output_root: Path
    names_table: str
    daily_table: str
    delist_table: str
    ccm_table: str
    source_version: str
    dry_run: bool


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a licensed CRSP/WRDS company panel into the private "
            "data_private/ layout expected by text_factor_lab."
        )
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help="Ticker list. Defaults to the requested company panel.",
    )
    parser.add_argument("--start-date", default="2016-01-01")
    parser.add_argument("--end-date", default="2025-12-31")
    parser.add_argument("--selection-date", default="2016-01-01")
    parser.add_argument("--output-root", default="data_private")
    parser.add_argument("--names-table", default="crsp.stocknames")
    parser.add_argument("--daily-table", default="crsp.dsf")
    parser.add_argument("--delist-table", default="crsp.dsedelist")
    parser.add_argument("--ccm-table", default="crsp.ccmxpf_linktable")
    parser.add_argument("--source-version", default="wrds_crsp_legacy_2026")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned extraction without connecting to WRDS.",
    )
    args = parser.parse_args()
    config = ExtractionConfig(
        tickers=normalize_tickers(args.tickers),
        start_date=args.start_date,
        end_date=args.end_date,
        selection_date=args.selection_date,
        output_root=Path(args.output_root),
        names_table=args.names_table,
        daily_table=args.daily_table,
        delist_table=args.delist_table,
        ccm_table=args.ccm_table,
        source_version=args.source_version,
        dry_run=args.dry_run,
    )
    if config.dry_run:
        print_plan(config)
        return 0

    try:
        import wrds
    except ImportError as exc:
        raise SystemExit(
            "Missing optional dependency 'wrds'. Install it with:\n"
            "  python -m pip install wrds\n"
            "Then set WRDS_USERNAME or follow the WRDS login prompt."
        ) from exc

    db = wrds.Connection()
    extract_company_panel(db, config)
    print(f"CRSP/WRDS private extraction completed under {config.output_root}")
    return 0


def normalize_tickers(values: list[str]) -> list[str]:
    tickers = []
    for value in values:
        ticker = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.\-]+", ticker):
            raise ValueError(f"Unsafe ticker value: {value!r}")
        tickers.append(ticker)
    return sorted(set(tickers))


def quoted_tickers(tickers: list[str]) -> str:
    return ", ".join(f"'{ticker}'" for ticker in tickers)


def print_plan(config: ExtractionConfig) -> None:
    print("WRDS/CRSP extraction plan")
    print(f"tickers={', '.join(config.tickers)}")
    print(f"sample={config.start_date}..{config.end_date}")
    print(f"selection_date={config.selection_date}")
    print(f"output_root={config.output_root}")
    print(f"tables={config.names_table}, {config.daily_table}, {config.delist_table}")


def extract_company_panel(db, config: ExtractionConfig) -> None:
    private_root = config.output_root
    crsp_dir = private_root / "crsp"
    universe_dir = private_root / "universe"
    crsp_dir.mkdir(parents=True, exist_ok=True)
    universe_dir.mkdir(parents=True, exist_ok=True)

    names = load_stock_names(db, config)
    if names.empty:
        raise RuntimeError("No CRSP stock name rows matched the requested tickers/date range.")
    daily = load_daily_returns(db, config, names)
    delist = load_delisting_returns(db, config, names)
    ccm_links = load_ccm_links(db, config, names)

    prices = build_prices_with_dlret(daily, delist)
    security_master = build_security_master(names, ccm_links, config)
    membership = build_membership(names, prices, delist, config)
    entity_links = build_entity_links(names, ccm_links, config)
    tickers = build_ticker_manifest(names, membership, config)

    write_csv(daily, crsp_dir / "daily_returns.csv")
    write_csv(delist, crsp_dir / "delisting_returns.csv")
    write_csv(prices, crsp_dir / "prices_with_dlret.csv")
    write_csv(security_master, universe_dir / "security_master.csv")
    write_csv(membership, universe_dir / "universe_membership.csv")
    write_csv(entity_links, universe_dir / "entity_link_history.csv")
    write_csv(tickers, universe_dir / "tickers.csv")


def load_stock_names(db, config: ExtractionConfig) -> pd.DataFrame:
    sql = f"""
        select distinct
            permno, permco, ticker, comnam, namedt, nameendt, exchcd, shrcd, siccd
        from {config.names_table}
        where upper(ticker) in ({quoted_tickers(config.tickers)})
          and namedt <= %(end_date)s
          and coalesce(nameendt, '9999-12-31'::date) >= %(start_date)s
    """
    return db.raw_sql(
        sql,
        params={"start_date": config.start_date, "end_date": config.end_date},
        date_cols=["namedt", "nameendt"],
    )


def load_daily_returns(db, config: ExtractionConfig, names: pd.DataFrame) -> pd.DataFrame:
    permnos = ", ".join(str(int(permno)) for permno in sorted(names["permno"].unique()))
    sql = f"""
        select
            d.permno,
            d.date,
            d.ret,
            d.retx,
            d.prc,
            d.shrout,
            d.vol as volume
        from {config.daily_table} as d
        where d.permno in ({permnos})
          and d.date between %(start_date)s and %(end_date)s
    """
    daily = db.raw_sql(
        sql,
        params={"start_date": config.start_date, "end_date": config.end_date},
        date_cols=["date"],
    )
    names_for_join = names[
        ["permno", "permco", "ticker", "namedt", "nameendt", "exchcd", "shrcd", "siccd"]
    ].copy()
    daily = daily.merge(names_for_join, on="permno", how="left")
    daily = daily[
        (daily["date"] >= daily["namedt"])
        & (daily["date"] <= daily["nameendt"].fillna(pd.Timestamp("2099-12-31")))
    ].copy()
    daily["source_version"] = config.source_version
    columns = [
        "permno",
        "permco",
        "date",
        "ticker",
        "ret",
        "retx",
        "prc",
        "shrout",
        "volume",
        "exchcd",
        "shrcd",
        "siccd",
        "source_version",
    ]
    return daily[columns].drop_duplicates(["permno", "date", "ticker"])


def load_delisting_returns(db, config: ExtractionConfig, names: pd.DataFrame) -> pd.DataFrame:
    permnos = ", ".join(str(int(permno)) for permno in sorted(names["permno"].unique()))
    sql = f"""
        select permno, dlstdt, dlret, dlstcd
        from {config.delist_table}
        where permno in ({permnos})
          and dlstdt between %(start_date)s and %(end_date)s
    """
    delist = db.raw_sql(
        sql,
        params={"start_date": config.start_date, "end_date": config.end_date},
        date_cols=["dlstdt"],
    )
    if delist.empty:
        return pd.DataFrame(
            columns=["permno", "dlstdt", "dlret", "dlstcd", "delisting_reason", "source_version"]
        )
    delist["delisting_reason"] = ""
    delist["source_version"] = config.source_version
    return delist[["permno", "dlstdt", "dlret", "dlstcd", "delisting_reason", "source_version"]]


def load_ccm_links(db, config: ExtractionConfig, names: pd.DataFrame) -> pd.DataFrame:
    permnos = ", ".join(str(int(permno)) for permno in sorted(names["permno"].unique()))
    sql = f"""
        select gvkey, lpermno as permno, lpermco as permco, linkdt, linkenddt,
               linktype, linkprim
        from {config.ccm_table}
        where lpermno in ({permnos})
          and linkdt <= %(end_date)s
          and coalesce(linkenddt, '9999-12-31'::date) >= %(start_date)s
    """
    try:
        return db.raw_sql(
            sql,
            params={"start_date": config.start_date, "end_date": config.end_date},
            date_cols=["linkdt", "linkenddt"],
        )
    except Exception as exc:
        warnings.warn(
            f"Failed to load CCM links from {config.ccm_table}: {exc}. "
            "GVKEY values will be empty and link_confidence will be downgraded.",
            RuntimeWarning,
            stacklevel=2,
        )
        return pd.DataFrame(
            columns=["gvkey", "permno", "permco", "linkdt", "linkenddt", "linktype", "linkprim"]
        )


def build_prices_with_dlret(daily: pd.DataFrame, delist: pd.DataFrame) -> pd.DataFrame:
    prices = daily.copy()
    if not delist.empty:
        prices = prices.merge(
            delist[["permno", "dlstdt", "dlret", "dlstcd"]],
            left_on=["permno", "date"],
            right_on=["permno", "dlstdt"],
            how="left",
        )
    else:
        prices["dlret"] = pd.NA
        prices["dlstcd"] = pd.NA
    ret = pd.to_numeric(prices["ret"], errors="coerce")
    dlret = pd.to_numeric(prices["dlret"], errors="coerce")
    ret_with_dlret = (1.0 + ret.fillna(0.0)) * (1.0 + dlret.fillna(0.0)) - 1.0
    ret_with_dlret.loc[ret.isna() & dlret.isna()] = pd.NA
    prices["delisting_return"] = prices["dlret"]
    prices["ret_with_dlret"] = ret_with_dlret
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
    return prices[columns].sort_values(["ticker", "date"])


def build_security_master(
    names: pd.DataFrame,
    ccm_links: pd.DataFrame,
    config: ExtractionConfig,
) -> pd.DataFrame:
    rows = []
    ccm_by_permno = latest_ccm_by_permno(ccm_links)
    for row in names.sort_values(["ticker", "namedt"]).itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        sector, industry = SECTOR_BY_TICKER.get(ticker, ("Unknown", "Unknown"))
        gvkey = ccm_by_permno.get(int(row.permno), {}).get("gvkey", "")
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "permno": row.permno,
                "permco": row.permco,
                "gvkey": gvkey,
                "cik": cik,
                "ticker": ticker,
                "historical_ticker": ticker,
                "company_name": row.comnam,
                "name_start_date": date_string(row.namedt),
                "name_end_date": date_string(row.nameendt),
                "exchange": exchange_name(row.exchcd),
                "share_class": share_class(row.shrcd),
                "security_type": "equity_or_adr",
                "sic": row.siccd or "",
                "naics": "",
                "gics_sector": sector,
                "gics_industry": industry,
                "source": "crsp_wrds",
                "source_version": config.source_version,
                "available_time_utc": f"{config.selection_date}T00:00:00Z",
            }
        )
    return pd.DataFrame(rows)


def build_membership(
    names: pd.DataFrame,
    prices: pd.DataFrame,
    delist: pd.DataFrame,
    config: ExtractionConfig,
) -> pd.DataFrame:
    rows = []
    delist_by_permno = (
        delist.set_index("permno")["dlstdt"].to_dict() if not delist.empty else {}
    )
    selection = pd.Timestamp(config.selection_date)
    for row in names.sort_values(["ticker", "namedt"]).itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        permno_prices = prices[prices["permno"] == row.permno].sort_values("date")
        before_selection = permno_prices[permno_prices["date"] <= selection]
        selection_row = (
            before_selection.iloc[-1]
            if not before_selection.empty
            else (permno_prices.iloc[0] if not permno_prices.empty else None)
        )
        price_at_selection = abs(float(selection_row["prc"])) if selection_row is not None else None
        shrout_thousand_shares = (
            float(selection_row["shrout"]) if selection_row is not None else None
        )
        shares_outstanding = (
            shrout_thousand_shares * 1000.0
            if shrout_thousand_shares is not None
            else None
        )
        market_cap = (
            price_at_selection * shares_outstanding
            if price_at_selection and shares_outstanding
            else None
        )
        entry = max(pd.Timestamp(row.namedt), selection)
        exit_date = row.nameendt if pd.notna(row.nameendt) else pd.Timestamp(config.end_date)
        delisting_date = delist_by_permno.get(row.permno)
        rows.append(
            {
                "universe_id": "licensed_company_panel_2016_2025",
                "entity_id": f"CIK{cik}",
                "ticker": ticker,
                "selection_date": config.selection_date,
                "entry_date": date_string(entry),
                "exit_date": date_string(exit_date),
                "delisting_date": date_string(delisting_date),
                "selection_rank": None,
                "market_cap_at_selection": market_cap,
                "price_at_selection": price_at_selection,
                "shares_outstanding_at_selection": shares_outstanding,
                "liquidity_filter_pass": True,
                "source": "crsp_wrds",
                "source_version": config.source_version,
            }
        )
    membership = pd.DataFrame(rows)
    if membership.empty:
        return membership
    membership = membership.sort_values(
        ["market_cap_at_selection", "ticker", "entry_date"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)
    membership["selection_rank"] = range(1, len(membership) + 1)
    return membership


def build_entity_links(
    names: pd.DataFrame,
    ccm_links: pd.DataFrame,
    config: ExtractionConfig,
) -> pd.DataFrame:
    ccm_by_permno = latest_ccm_by_permno(ccm_links)
    rows = []
    for row in names.sort_values(["ticker", "namedt"]).itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        ccm = ccm_by_permno.get(int(row.permno), {})
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "cik": cik,
                "ticker": ticker,
                "permno": row.permno,
                "gvkey": ccm.get("gvkey", ""),
                "link_start_date": date_string(row.namedt),
                "link_end_date": date_string(row.nameendt),
                "link_type": ccm.get("linktype", "ticker_permno_interval"),
                "link_confidence": 1.0 if ccm else 0.9,
                "source": "crsp_wrds_ccm_or_stocknames",
            }
        )
    return pd.DataFrame(rows)


def build_ticker_manifest(
    names: pd.DataFrame,
    membership: pd.DataFrame,
    config: ExtractionConfig,
) -> pd.DataFrame:
    rows = []
    membership_by_ticker = membership.sort_values("selection_rank").drop_duplicates("ticker")
    for row in membership_by_ticker.itertuples(index=False):
        ticker = str(row.ticker).upper()
        cik = CIK_BY_TICKER.get(ticker, "0000000000")
        sector, industry = SECTOR_BY_TICKER.get(ticker, ("Unknown", "Unknown"))
        company_name = (
            names[names["ticker"].str.upper() == ticker]
            .sort_values("namedt")
            .iloc[-1]["comnam"]
        )
        rows.append(
            {
                "entity_id": f"CIK{cik}",
                "ticker": ticker,
                "historical_ticker": ticker,
                "cik": cik,
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                "selection_date": config.selection_date,
                "market_cap_at_selection": row.market_cap_at_selection,
                "entry_date": row.entry_date,
                "exit_date": row.exit_date,
                "delisting_date": row.delisting_date,
                "mapping_source": "crsp_wrds_ccm_or_stocknames",
                "mapping_available_time_utc": f"{config.selection_date}T00:00:00Z",
            }
        )
    return pd.DataFrame(rows)


def latest_ccm_by_permno(ccm_links: pd.DataFrame) -> dict[int, dict[str, object]]:
    if ccm_links.empty:
        return {}
    ordered = ccm_links.sort_values(["permno", "linkdt"]).drop_duplicates("permno", keep="last")
    return {int(row.permno): row._asdict() for row in ordered.itertuples(index=False)}


def exchange_name(exchcd: object) -> str:
    mapping = {1: "NYSE", 2: "AMEX", 3: "NASDAQ"}
    try:
        return mapping.get(int(exchcd), str(exchcd))
    except (TypeError, ValueError):
        return "Unknown"


def share_class(shrcd: object) -> str:
    mapping = {10: "common", 11: "common", 12: "adr_or_foreign_common"}
    try:
        return mapping.get(int(shrcd), str(shrcd))
    except (TypeError, ValueError):
        return "Unknown"


def date_string(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str) and value == "":
        return ""
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


if __name__ == "__main__":
    raise SystemExit(main())
