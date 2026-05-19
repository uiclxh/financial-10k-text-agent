from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

ReturnType = Literal["log", "simple"]


class PriceDataError(ValueError):
    """Raised when price input cannot support formal label construction."""


@dataclass(frozen=True)
class ReturnWindow:
    ticker: str
    event_date: date
    label_start_date: date
    label_end_date: date
    returns: pd.Series


@dataclass(frozen=True)
class PricePanel:
    frame: pd.DataFrame
    price_field: str = "adj_close"

    def ticker_frame(self, ticker: str) -> pd.DataFrame:
        subset = self.frame[self.frame["ticker"] == ticker].sort_values("date")
        if subset.empty:
            raise PriceDataError(f"No prices available for ticker={ticker}")
        return subset

    def forward_return_window(
        self,
        *,
        ticker: str,
        event_date: date,
        start_offset: int,
        end_offset: int,
        return_type: ReturnType,
    ) -> ReturnWindow:
        if start_offset < 1 or end_offset < start_offset:
            raise PriceDataError(
                "Forward label windows must satisfy 1 <= start_offset <= end_offset"
            )

        ticker_prices = self.ticker_frame(ticker)
        forward_rows = ticker_prices[ticker_prices["date"] > event_date].copy()
        required_count = end_offset
        if len(forward_rows) < required_count:
            raise PriceDataError(
                f"Insufficient forward window for ticker={ticker}: "
                f"need {required_count} trading days after {event_date}, found {len(forward_rows)}"
            )

        window_rows = forward_rows.iloc[start_offset - 1 : end_offset]
        return_column = f"{return_type}_return"
        if window_rows[return_column].isna().any():
            raise PriceDataError(
                f"Missing {return_type} returns for ticker={ticker} over "
                f"{window_rows['date'].iloc[0]} to {window_rows['date'].iloc[-1]}"
            )

        returns = window_rows.set_index("date")[return_column].astype(float)
        return ReturnWindow(
            ticker=ticker,
            event_date=event_date,
            label_start_date=window_rows["date"].iloc[0],
            label_end_date=window_rows["date"].iloc[-1],
            returns=returns,
        )


def load_price_panel_csv(path: str | Path, *, price_field: str = "adj_close") -> PricePanel:
    frame = pd.read_csv(path)
    return build_price_panel(frame, price_field=price_field)


def build_price_panel(frame: pd.DataFrame, *, price_field: str = "adj_close") -> PricePanel:
    required_columns = {"date", "ticker", price_field}
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise PriceDataError(f"Price data missing required columns: {sorted(missing_columns)}")

    prices = frame.loc[:, ["date", "ticker", price_field]].copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.date
    prices["ticker"] = prices["ticker"].astype(str).str.upper().str.strip()
    prices[price_field] = pd.to_numeric(prices[price_field], errors="coerce")

    if prices["ticker"].eq("").any():
        raise PriceDataError("Price data contains empty ticker")
    if prices[price_field].isna().any():
        raise PriceDataError(f"Price data contains non-numeric {price_field}")
    if (prices[price_field] <= 0).any():
        raise PriceDataError(f"Price data contains non-positive {price_field}")
    if prices.duplicated(["ticker", "date"]).any():
        raise PriceDataError("Price data contains duplicate ticker/date rows")

    prices = prices.sort_values(["ticker", "date"]).reset_index(drop=True)
    previous_close = prices.groupby("ticker", observed=True)[price_field].shift(1)
    prices["simple_return"] = prices[price_field] / previous_close - 1.0
    prices["log_return"] = np.log(prices[price_field] / previous_close)
    prices["simple_return"] = prices["simple_return"].astype(float)
    prices["log_return"] = prices["log_return"].astype(float)
    return PricePanel(frame=prices, price_field=price_field)
