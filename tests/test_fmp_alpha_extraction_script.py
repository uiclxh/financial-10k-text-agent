from __future__ import annotations

import pandas as pd

from scripts.extract_fmp_alpha_10_company_panel import (
    BENCHMARK_TICKER,
    DEFAULT_COMPANIES,
    build_price_quality_report,
    build_prices_with_returns,
    normalize_tickers,
    normalize_yahoo_fallback_tickers,
)


def test_default_panel_replaces_sony_with_jpm() -> None:
    tickers = {company.ticker for company in DEFAULT_COMPANIES}

    assert "JPM" in tickers
    assert "SONY" not in tickers


def test_normalize_tickers_rejects_non_panel_ticker() -> None:
    assert normalize_tickers(["msft", "JPM"]) == ["JPM", "MSFT"]

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
