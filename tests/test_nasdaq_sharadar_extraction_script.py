from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.extract_nasdaq_sharadar_company_panel import (
    SharadarExtractionConfig,
    build_membership,
    build_prices_with_returns,
)


def config(tmp_path: Path) -> SharadarExtractionConfig:
    return SharadarExtractionConfig(
        tickers=["AAA", "BBB"],
        start_date="2016-01-01",
        end_date="2025-12-31",
        selection_date="2016-01-01",
        output_root=tmp_path,
        api_key="test",
        dry_run=False,
    )


def tickers_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "name": "AAA Inc.",
                "exchange": "NASDAQ",
                "category": "Domestic Common Stock",
                "isdelisted": "N",
                "firstpricedate": "2010-01-01",
                "lastpricedate": "2025-12-31",
                "scalemarketcap": 100,
                "sector": "Technology",
                "industry": "Software",
            },
            {
                "ticker": "BBB",
                "name": "BBB Inc.",
                "exchange": "NYSE",
                "category": "Domestic Common Stock",
                "isdelisted": "Y",
                "firstpricedate": "2010-01-01",
                "lastpricedate": "2020-01-03",
                "scalemarketcap": 200,
                "sector": "Industrials",
                "industry": "Machinery",
            },
        ]
    )


def test_sharadar_prices_compute_returns_and_mark_delisted_last_price(
    tmp_path: Path,
) -> None:
    sep = pd.DataFrame(
        [
            {"ticker": "BBB", "date": "2020-01-02", "close": 10.0, "volume": 100},
            {"ticker": "BBB", "date": "2020-01-03", "close": 8.0, "volume": 100},
        ]
    )

    prices = build_prices_with_returns(sep, tickers_frame(), config(tmp_path))

    assert prices["ret"].iloc[1] == pytest.approx(-0.2)
    assert prices["ret_with_dlret"].iloc[1] == pytest.approx(-0.2)
    assert prices["dlstcd"].iloc[1] == "SHARADAR_DELISTED_NO_DLRET"


def test_sharadar_membership_ranks_by_daily_market_cap(tmp_path: Path) -> None:
    prices = pd.DataFrame(
        [
            {"ticker": "AAA", "date": pd.Timestamp("2016-01-01"), "prc": 10.0},
            {"ticker": "BBB", "date": pd.Timestamp("2016-01-01"), "prc": 20.0},
        ]
    )

    daily = pd.DataFrame(
        [
            {"ticker": "AAA", "date": "2016-01-01", "marketcap": 100},
            {"ticker": "BBB", "date": "2016-01-01", "marketcap": 200},
        ]
    )

    membership = build_membership(
        tickers_frame(),
        prices,
        config(tmp_path),
        daily_indicators=daily,
    )

    assert list(membership["ticker"]) == ["BBB", "AAA"]
    assert list(membership["selection_rank"]) == [1, 2]
    assert set(membership["entry_date"]) == {"2016-01-01"}
    assert membership.loc[membership["ticker"] == "BBB", "market_cap_at_selection"].iloc[
        0
    ] == 200_000_000
    assert membership.loc[membership["ticker"] == "BBB", "delisting_date"].iloc[
        0
    ] == "2020-01-03"
