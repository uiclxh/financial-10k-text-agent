from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from text_factor_lab.calendar.market_calendar import (
    MarketSession,
    get_market_session,
    next_market_session,
)
from text_factor_lab.schemas.base import is_timezone_aware

EVENT_DATE_RESOLVER_VERSION = "market-calendar-event-date-v1"
EventDatePolicy = Literal["pre_open", "intraday", "after_close", "non_trading_day"]


@dataclass(frozen=True)
class EventDateResolution:
    event_time_utc: datetime
    exchange: str
    timezone: str
    raw_event_date: date
    resolved_event_date: date
    market_open_utc: datetime
    market_close_utc: datetime
    is_trading_day: bool
    is_early_close: bool
    event_date_policy: EventDatePolicy
    resolver_version: str


def resolve_event_date(
    event_time_utc: datetime,
    *,
    exchange: str = "NYSE",
    timezone: str = "America/New_York",
    after_close_policy: Literal["next_trading_day"] = "next_trading_day",
    pre_open_policy: Literal["same_trading_day"] = "same_trading_day",
    intraday_policy: Literal["same_trading_day"] = "same_trading_day",
) -> EventDateResolution:
    del after_close_policy, pre_open_policy, intraday_policy
    if not is_timezone_aware(event_time_utc):
        raise ValueError("event_time_utc must be timezone-aware")

    event_time_utc = event_time_utc.astimezone(UTC)
    local_zone = ZoneInfo(timezone)
    raw_event_date = event_time_utc.astimezone(local_zone).date()
    raw_session = get_market_session(raw_event_date, exchange=exchange, timezone=timezone)

    if raw_session is None:
        resolved_session = next_market_session(
            raw_event_date,
            exchange=exchange,
            timezone=timezone,
        )
        return _resolution(
            event_time_utc=event_time_utc,
            exchange=exchange,
            timezone=timezone,
            raw_event_date=raw_event_date,
            resolved_session=resolved_session,
            is_trading_day=False,
            event_date_policy="non_trading_day",
        )

    if event_time_utc < raw_session.market_open_utc:
        return _resolution(
            event_time_utc=event_time_utc,
            exchange=exchange,
            timezone=timezone,
            raw_event_date=raw_event_date,
            resolved_session=raw_session,
            is_trading_day=True,
            event_date_policy="pre_open",
        )

    if event_time_utc <= raw_session.market_close_utc:
        return _resolution(
            event_time_utc=event_time_utc,
            exchange=exchange,
            timezone=timezone,
            raw_event_date=raw_event_date,
            resolved_session=raw_session,
            is_trading_day=True,
            event_date_policy="intraday",
        )

    resolved_session = next_market_session(
        raw_event_date + timedelta(days=1),
        exchange=exchange,
        timezone=timezone,
    )
    return _resolution(
        event_time_utc=event_time_utc,
        exchange=exchange,
        timezone=timezone,
        raw_event_date=raw_event_date,
        resolved_session=resolved_session,
        is_trading_day=True,
        event_date_policy="after_close",
    )


def _resolution(
    *,
    event_time_utc: datetime,
    exchange: str,
    timezone: str,
    raw_event_date: date,
    resolved_session: MarketSession,
    is_trading_day: bool,
    event_date_policy: EventDatePolicy,
) -> EventDateResolution:
    return EventDateResolution(
        event_time_utc=event_time_utc,
        exchange=exchange,
        timezone=timezone,
        raw_event_date=raw_event_date,
        resolved_event_date=resolved_session.session_date,
        market_open_utc=resolved_session.market_open_utc,
        market_close_utc=resolved_session.market_close_utc,
        is_trading_day=is_trading_day,
        is_early_close=resolved_session.is_early_close,
        event_date_policy=event_date_policy,
        resolver_version=EVENT_DATE_RESOLVER_VERSION,
    )
