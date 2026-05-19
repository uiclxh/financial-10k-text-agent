from __future__ import annotations

from datetime import date

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
