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
    delisting_return_applied: bool = False
    delisting_code: str | None = None
    return_quality_flag: str = "complete"


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
        delisting_mask = (
            window_rows["delisting_return_applied"].astype(bool)
            if "delisting_return_applied" in window_rows.columns
            else pd.Series(False, index=window_rows.index)
        )
        delisting_rows = window_rows[delisting_mask]
        missing_delisting_rows = (
            window_rows[window_rows["missing_delisting_return"].astype(bool)]
            if "missing_delisting_return" in window_rows.columns
            else window_rows.iloc[0:0]
        )
        return ReturnWindow(
            ticker=ticker,
            event_date=event_date,
            label_start_date=window_rows["date"].iloc[0],
            label_end_date=window_rows["date"].iloc[-1],
            returns=returns,
            delisting_return_applied=not delisting_rows.empty,
            delisting_code=(
                str(delisting_rows["delisting_code"].dropna().iloc[-1])
                if not delisting_rows.empty
                and "delisting_code" in delisting_rows
                and not delisting_rows["delisting_code"].dropna().empty
                else None
            ),
            return_quality_flag=(
                "missing_delisting_return"
                if not missing_delisting_rows.empty
                else "delisting_return_applied"
                if not delisting_rows.empty
                else "complete"
            ),
        )


def load_price_panel_csv(path: str | Path, *, price_field: str = "adj_close") -> PricePanel:
    frame = pd.read_csv(path)
    return build_price_panel(frame, price_field=price_field)


def build_price_panel(frame: pd.DataFrame, *, price_field: str = "adj_close") -> PricePanel:
    required_columns = {"date", "ticker"}
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise PriceDataError(f"Price data missing required columns: {sorted(missing_columns)}")

    columns = ["date", "ticker"]
    for column in [
        price_field,
        "simple_return",
        "log_return",
        "ret",
        "retx",
        "dlret",
        "delisting_return",
        "dlstcd",
        "delisting_code",
    ]:
        if column in frame.columns and column not in columns:
            columns.append(column)
    prices = frame.loc[:, columns].copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.date
    prices["ticker"] = prices["ticker"].astype(str).str.upper().str.strip()

    if prices["ticker"].eq("").any():
        raise PriceDataError("Price data contains empty ticker")
    if prices.duplicated(["ticker", "date"]).any():
        raise PriceDataError("Price data contains duplicate ticker/date rows")

    prices = prices.sort_values(["ticker", "date"]).reset_index(drop=True)
    prices = _attach_base_returns(prices, price_field)
    prices = _apply_delisting_returns(prices)
    prices["simple_return"] = prices["simple_return"].astype(float)
    prices["log_return"] = prices["log_return"].astype(float)
    return PricePanel(frame=prices, price_field=price_field)


def _attach_base_returns(prices: pd.DataFrame, price_field: str) -> pd.DataFrame:
    prices = prices.copy()
    if "simple_return" in prices.columns:
        prices["simple_return"] = pd.to_numeric(prices["simple_return"], errors="coerce")
    elif "ret" in prices.columns:
        prices["simple_return"] = pd.to_numeric(prices["ret"], errors="coerce")
    elif price_field in prices.columns:
        prices[price_field] = pd.to_numeric(prices[price_field], errors="coerce")
        if prices[price_field].isna().any():
            raise PriceDataError(f"Price data contains non-numeric {price_field}")
        if (prices[price_field] <= 0).any():
            raise PriceDataError(f"Price data contains non-positive {price_field}")
        previous_close = prices.groupby("ticker", observed=True)[price_field].shift(1)
        prices["simple_return"] = prices[price_field] / previous_close - 1.0
    else:
        raise PriceDataError(
            "Price data must contain price_field, simple_return, or CRSP ret column"
        )

    if "log_return" in prices.columns:
        prices["log_return"] = pd.to_numeric(prices["log_return"], errors="coerce")
    else:
        prices["log_return"] = np.log1p(prices["simple_return"])
    return prices


def _apply_delisting_returns(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    delisting_column = None
    for candidate in ("dlret", "delisting_return"):
        if candidate in prices.columns:
            delisting_column = candidate
            break
    if delisting_column is None:
        prices["delisting_return_applied"] = False
        prices["delisting_code"] = None
        prices["return_quality_flag"] = "complete"
        return prices

    delisting_return = pd.to_numeric(prices[delisting_column], errors="coerce")
    has_delisting_return = delisting_return.notna()
    code_column = "dlstcd" if "dlstcd" in prices.columns else "delisting_code"
    if code_column in prices.columns:
        delisting_code = prices[code_column].replace("", pd.NA)
        has_delisting_code = delisting_code.notna()
    else:
        delisting_code = pd.Series(pd.NA, index=prices.index, dtype="object")
        has_delisting_code = pd.Series(False, index=prices.index)
    missing_delisting_return = has_delisting_code & ~has_delisting_return
    base_return = prices["simple_return"]
    total_return = base_return.copy()
    total_return.loc[has_delisting_return & base_return.notna()] = (
        (1.0 + base_return.loc[has_delisting_return & base_return.notna()])
        * (1.0 + delisting_return.loc[has_delisting_return & base_return.notna()])
        - 1.0
    )
    total_return.loc[has_delisting_return & base_return.isna()] = delisting_return.loc[
        has_delisting_return & base_return.isna()
    ]
    prices["simple_return"] = total_return
    prices["log_return"] = np.where(
        prices["simple_return"] > -1.0,
        np.log1p(prices["simple_return"]),
        np.nan,
    )
    prices["delisting_return_applied"] = has_delisting_return
    prices["delisting_code"] = delisting_code.astype(str).where(delisting_code.notna(), None)
    prices["missing_delisting_return"] = missing_delisting_return
    prices["return_quality_flag"] = np.select(
        [has_delisting_return, missing_delisting_return],
        ["delisting_return_applied", "missing_delisting_return"],
        default="complete",
    )
    return prices
