from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal

REGULAR_US_EQUITY_CLOSE = time(16, 0)
DEFAULT_MARKET_TIMEZONE = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class MarketSession:
    exchange: str
    session_date: date
    market_open_utc: datetime
    market_close_utc: datetime
    timezone: str
    is_early_close: bool


def _calendar_name(exchange: str) -> str:
    normalized = exchange.strip().upper()
    if normalized in {"NYSE", "XNYS", "US"}:
        return "NYSE"
    return normalized


def get_market_session(
    session_date: date,
    *,
    exchange: str = "NYSE",
    timezone: str = "America/New_York",
) -> MarketSession | None:
    calendar = mcal.get_calendar(_calendar_name(exchange))
    schedule = calendar.schedule(start_date=session_date, end_date=session_date)
    if schedule.empty:
        return None

    row = schedule.iloc[0]
    market_open_utc = row["market_open"].to_pydatetime().astimezone(UTC)
    market_close_utc = row["market_close"].to_pydatetime().astimezone(UTC)
    local_zone = ZoneInfo(timezone)
    local_close = market_close_utc.astimezone(local_zone).time()
    return MarketSession(
        exchange=_calendar_name(exchange),
        session_date=session_date,
        market_open_utc=market_open_utc,
        market_close_utc=market_close_utc,
        timezone=timezone,
        is_early_close=local_close < REGULAR_US_EQUITY_CLOSE,
    )


def next_market_session(
    start_date: date,
    *,
    exchange: str = "NYSE",
    timezone: str = "America/New_York",
    max_search_days: int = 14,
) -> MarketSession:
    calendar = mcal.get_calendar(_calendar_name(exchange))
    end_date = start_date + timedelta(days=max_search_days)
    schedule = calendar.schedule(start_date=start_date, end_date=end_date)
    if schedule.empty:
        raise ValueError(
            f"No {exchange} market session found between {start_date} and {end_date}"
        )

    session_day = schedule.index[0].date()
    session = get_market_session(session_day, exchange=exchange, timezone=timezone)
    if session is None:
        raise ValueError(f"Unable to resolve {exchange} market session for {session_day}")
    return session
