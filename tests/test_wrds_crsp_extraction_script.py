from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

from scripts.extract_wrds_crsp_company_panel import (
    ExtractionConfig,
    build_membership,
    build_prices_with_dlret,
    load_ccm_links,
)


def config(tmp_path: Path) -> ExtractionConfig:
    return ExtractionConfig(
        tickers=["AAA", "BBB"],
        start_date="2016-01-01",
        end_date="2025-12-31",
        selection_date="2016-01-01",
        output_root=tmp_path,
        names_table="crsp.stocknames",
        daily_table="crsp.dsf",
        delist_table="crsp.dsedelist",
        ccm_table="crsp.ccmxpf_linktable",
        source_version="test",
        dry_run=False,
    )


def test_prices_with_dlret_compute_adjusted_return() -> None:
    daily = pd.DataFrame(
        [
            {
                "permno": 1,
                "permco": 10,
                "date": pd.Timestamp("2020-01-02"),
                "ticker": "AAA",
                "ret": -0.2,
                "retx": -0.1,
                "prc": 10.0,
                "shrout": 100.0,
                "volume": 1000,
                "exchcd": 1,
                "shrcd": 10,
                "siccd": "1000",
                "source_version": "test",
            }
        ]
    )
    delist = pd.DataFrame(
        [
            {
                "permno": 1,
                "dlstdt": pd.Timestamp("2020-01-02"),
                "dlret": -0.5,
                "dlstcd": "500",
                "delisting_reason": "",
                "source_version": "test",
            }
        ]
    )

    prices = build_prices_with_dlret(daily, delist)

    assert prices["ret_with_dlret"].iloc[0] == -0.6
    assert prices["delisting_return"].iloc[0] == -0.5


def test_membership_uses_usd_market_cap_and_ranks_by_market_cap(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    names = pd.DataFrame(
        [
            {
                "permno": 1,
                "permco": 10,
                "ticker": "AAA",
                "comnam": "AAA Inc.",
                "namedt": pd.Timestamp("2010-01-01"),
                "nameendt": pd.NaT,
                "exchcd": 1,
                "shrcd": 10,
                "siccd": "1000",
            },
            {
                "permno": 2,
                "permco": 20,
                "ticker": "BBB",
                "comnam": "BBB Inc.",
                "namedt": pd.Timestamp("2010-01-01"),
                "nameendt": pd.NaT,
                "exchcd": 1,
                "shrcd": 10,
                "siccd": "1000",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"permno": 1, "date": pd.Timestamp("2016-01-01"), "prc": 10.0, "shrout": 100.0},
            {"permno": 2, "date": pd.Timestamp("2016-01-01"), "prc": 5.0, "shrout": 1000.0},
        ]
    )

    membership = build_membership(names, prices, pd.DataFrame(), cfg)

    assert list(membership["ticker"]) == ["BBB", "AAA"]
    assert list(membership["selection_rank"]) == [1, 2]
    assert membership.loc[membership["ticker"] == "AAA", "market_cap_at_selection"].iloc[0] == (
        10.0 * 100.0 * 1000.0
    )
    assert membership.loc[membership["ticker"] == "AAA", "shares_outstanding_at_selection"].iloc[
        0
    ] == 100.0 * 1000.0


def test_ccm_load_failure_emits_warning(tmp_path: Path) -> None:
    class BrokenDB:
        def raw_sql(self, *args, **kwargs):
            raise RuntimeError("permission denied")

    names = pd.DataFrame({"permno": [1]})

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        links = load_ccm_links(BrokenDB(), config(tmp_path), names)

    assert links.empty
    assert any("Failed to load CCM links" in str(item.message) for item in caught)
