from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.extract_fmp_alpha_10_company_panel import (
    BENCHMARK_TICKER,
    DEFAULT_30_COMPANIES,
    DEFAULT_50_COMPANIES,
    DEFAULT_COMPANIES,
    PANEL_PRESETS,
    ExtractionConfig,
    build_price_quality_report,
    build_prices_with_returns,
    build_security_master,
    fiscal_year_from_report_date,
    normalize_tickers,
    normalize_yahoo_fallback_tickers,
)


def test_default_panel_replaces_sony_with_jpm() -> None:
    tickers = {company.ticker for company in DEFAULT_COMPANIES}

    assert "JPM" in tickers
    assert "SONY" not in tickers


def test_30_company_panel_extends_current_10_company_panel() -> None:
    ten = {company.ticker for company in DEFAULT_COMPANIES}
    thirty = {company.ticker for company in DEFAULT_30_COMPANIES}

    assert len(DEFAULT_COMPANIES) == 10
    assert len(DEFAULT_30_COMPANIES) == 30
    assert ten.issubset(thirty)
    assert {"ORCL", "ADBE", "CRM", "CSCO", "IBM"}.issubset(thirty)
    assert {"BAC", "GS", "MS", "WFC", "AXP"}.issubset(thirty)
    assert {"PFE", "MRK", "ABBV", "JNJ", "ABT"}.issubset(thirty)
    assert {"COST", "KO", "PEP", "HD", "CMCSA"}.issubset(thirty)
    assert PANEL_PRESETS["30_company_sp500_sector_seed"] == DEFAULT_30_COMPANIES


def test_50_company_panel_adds_balancing_sectors() -> None:
    thirty = {company.ticker for company in DEFAULT_30_COMPANIES}
    fifty = {company.ticker for company in DEFAULT_50_COMPANIES}

    assert len(DEFAULT_50_COMPANIES) == 50
    assert thirty.issubset(fifty)
    assert {"CVX", "COP", "EOG", "OXY"}.issubset(fifty)
    assert {"UNP", "CAT", "HON", "GE", "UPS"}.issubset(fifty)
    assert {"NEE", "DUK", "SO", "AEP"}.issubset(fifty)
    assert {"APD", "SHW", "FCX", "NEM"}.issubset(fifty)
    assert {"PLD", "AMT"}.issubset(fifty)
    assert "MA" in fifty
    assert PANEL_PRESETS["50_company_sp500_sector_seed"] == DEFAULT_50_COMPANIES


def test_50_company_panel_flags_ge_restructuring_review() -> None:
    ge = next(company for company in DEFAULT_50_COMPANIES if company.ticker == "GE")

    assert ge.price_ticker == "GE"
    assert "continuous CIK/ticker linkage" in ge.research_notes
    assert "major corporate restructuring" in ge.research_notes


def test_security_master_documents_common_equity_price_ticker_policy() -> None:
    config = ExtractionConfig(
        panel_name="50_company_sp500_sector_seed",
        companies=DEFAULT_50_COMPANIES,
        start_date="2015-12-01",
        end_date="2026-04-30",
        filing_start_year=2016,
        filing_end_year=2025,
        selection_date="2016-01-01",
        output_root=Path("data_private"),
        fmp_api_key=None,
        alpha_api_key=None,
        sec_user_agent=None,
        lm_dictionary_file=None,
        dry_run=True,
        skip_sec=True,
        skip_alpha_crosscheck=True,
        yahoo_fallback_tickers=[],
        sleep_seconds=0,
    )

    security_master = build_security_master(config, pd.DataFrame())
    financial_tickers = {"BAC", "JPM", "MS", "WFC", "AXP", "MA"}
    financial_rows = security_master[security_master["ticker"].isin(financial_tickers)]

    assert not financial_rows.empty
    assert financial_rows["common_equity_price_ticker"].eq(financial_rows["ticker"]).all()
    assert security_master["price_ticker_policy"].str.contains("common equity ticker").all()
    assert (
        security_master.loc[security_master["ticker"] == "GE", "research_notes"]
        .iloc[0]
        .startswith("GE is retained")
    )


def test_fiscal_year_from_early_january_report_date_rolls_back() -> None:
    assert fiscal_year_from_report_date("2021-01-03") == 2020
    assert fiscal_year_from_report_date("2022-01-02") == 2021
    assert fiscal_year_from_report_date("2019-12-29") == 2019


def test_normalize_tickers_rejects_non_panel_ticker() -> None:
    assert normalize_tickers(["msft", "JPM"]) == ["JPM", "MSFT"]
    assert normalize_tickers(["orcl", "JPM"], DEFAULT_30_COMPANIES) == ["JPM", "ORCL"]
    assert normalize_tickers(["ma", "NEE"], DEFAULT_50_COMPANIES) == ["MA", "NEE"]

    try:
        normalize_tickers(["SONY"])
    except ValueError as exc:
        assert "Unsupported ticker" in str(exc)
    else:
        raise AssertionError("SONY should be rejected from the fixed 10-K panel")


def test_normalize_yahoo_fallback_tickers_must_be_requested() -> None:
    assert normalize_yahoo_fallback_tickers(["mcd", "LLY"], ["MSFT", "MCD", "LLY"]) == [
        "LLY",
        "MCD",
    ]

    try:
        normalize_yahoo_fallback_tickers(["MCD"], ["MSFT"])
    except ValueError as exc:
        assert "Yahoo fallback ticker must be in requested fixed panel" in str(exc)
    else:
        raise AssertionError("Fallback tickers outside requested panel should be rejected")


def test_fmp_price_builder_uses_adjusted_close_returns() -> None:
    raw = pd.DataFrame(
        [
            {"ticker": "MSFT", "date": "2020-01-02", "close": 100, "adjClose": 50},
            {"ticker": "MSFT", "date": "2020-01-03", "close": 110, "adjClose": 55},
            {
                "ticker": "MCD",
                "date": "2020-01-02",
                "close": 200,
                "adjClose": 200,
                "source": "yahoo_chart_price_fallback",
            },
            {"ticker": BENCHMARK_TICKER, "date": "2020-01-02", "close": 200, "adjClose": 200},
            {"ticker": BENCHMARK_TICKER, "date": "2020-01-03", "close": 202, "adjClose": 202},
        ]
    )

    prices = build_prices_with_returns(raw)
    msft_second = prices[
        (prices["ticker"] == "MSFT") & (prices["date"] == pd.Timestamp("2020-01-03"))
    ]

    assert float(msft_second.iloc[0]["closeadj"]) == 55
    assert round(float(msft_second.iloc[0]["ret"]), 6) == 0.1
    assert (
        prices.loc[prices["ticker"] == "MSFT", "source"]
        .eq("fmp_historical_price_eod_full")
        .all()
    )
    assert (
        prices.loc[prices["ticker"] == "MCD", "source"]
        .eq("yahoo_chart_price_fallback")
        .all()
    )


def test_price_quality_uses_spy_trading_dates_as_expected_calendar() -> None:
    raw = pd.DataFrame(
        [
            {"ticker": "MSFT", "date": "2020-01-02", "close": 100, "adjClose": 100},
            {"ticker": BENCHMARK_TICKER, "date": "2020-01-02", "close": 200, "adjClose": 200},
            {"ticker": BENCHMARK_TICKER, "date": "2020-01-03", "close": 202, "adjClose": 202},
        ]
    )
    prices = build_prices_with_returns(raw)

    report = build_price_quality_report(
        prices,
        benchmark_ticker=BENCHMARK_TICKER,
        expected_tickers=["MSFT", "MCD"],
    )
    msft_report = next(row for row in report["tickers"] if row["ticker"] == "MSFT")
    mcd_report = next(row for row in report["tickers"] if row["ticker"] == "MCD")

    assert msft_report["expected_days"] == 2
    assert msft_report["observed_days"] == 1
    assert msft_report["missing_dates"] == ["2020-01-03"]
    assert mcd_report["status"] == "missing_all_prices"
    assert mcd_report["observed_days"] == 0
