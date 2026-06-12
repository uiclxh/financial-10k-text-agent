from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from text_factor_lab.data.prices import PriceDataError, build_price_panel, load_price_panel_csv


def test_load_price_panel_csv_calculates_simple_and_log_returns() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    window = panel.forward_return_window(
        ticker="AAPL",
        event_date=date(2023, 11, 2),
        start_offset=1,
        end_offset=3,
        return_type="log",
    )

    assert window.label_start_date == date(2023, 11, 3)
    assert window.label_end_date == date(2023, 11, 7)
    assert len(window.returns) == 3
    assert window.returns.index.tolist() == [
        date(2023, 11, 3),
        date(2023, 11, 6),
        date(2023, 11, 7),
    ]


def test_price_panel_rejects_duplicate_ticker_dates() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")
    duplicate = panel.frame.loc[:, ["date", "ticker", "adj_close"]]
    duplicate = duplicate._append(duplicate.iloc[0], ignore_index=True)

    with pytest.raises(PriceDataError, match="duplicate"):
        build_price_panel(duplicate)


def test_forward_return_window_fails_when_window_is_unavailable() -> None:
    panel = load_price_panel_csv("tests/fixtures/prices_aapl_spy.csv")

    with pytest.raises(PriceDataError, match="Insufficient forward window"):
        panel.forward_return_window(
            ticker="AAPL",
            event_date=date(2023, 11, 2),
            start_offset=1,
            end_offset=20,
            return_type="log",
        )


def test_price_panel_applies_crsp_delisting_return() -> None:
    panel = build_price_panel(
        pd.DataFrame(
            [
                ("2020-01-01", "OLD", "", "", "", "500"),
                ("2020-01-02", "OLD", "0.10", "", "", ""),
                ("2020-01-03", "OLD", "-0.20", "-0.50", "", "500"),
            ],
            columns=["date", "ticker", "ret", "dlret", "delisting_return", "dlstcd"],
        )
    )

    window = panel.forward_return_window(
        ticker="OLD",
        event_date=date(2020, 1, 1),
        start_offset=1,
        end_offset=2,
        return_type="simple",
    )

    assert window.delisting_return_applied is True
    assert window.delisting_code == "500"
    assert window.return_quality_flag == "delisting_return_applied"
    assert window.returns.loc[date(2020, 1, 3)] == pytest.approx(-0.6)
