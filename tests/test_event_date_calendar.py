from __future__ import annotations

from datetime import UTC, datetime

from text_factor_lab.calendar import EVENT_DATE_RESOLVER_VERSION, resolve_event_date


def utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def test_pre_open_filing_resolves_to_same_trading_day() -> None:
    resolution = resolve_event_date(utc(2023, 11, 3, 12, 0))

    assert resolution.resolved_event_date.isoformat() == "2023-11-03"
    assert resolution.event_date_policy == "pre_open"
    assert resolution.is_trading_day is True
    assert resolution.resolver_version == EVENT_DATE_RESOLVER_VERSION


def test_intraday_filing_resolves_to_same_trading_day() -> None:
    resolution = resolve_event_date(utc(2023, 11, 3, 16, 0))

    assert resolution.resolved_event_date.isoformat() == "2023-11-03"
    assert resolution.event_date_policy == "intraday"
    assert resolution.market_open_utc.isoformat() == "2023-11-03T13:30:00+00:00"
    assert resolution.market_close_utc.isoformat() == "2023-11-03T20:00:00+00:00"


def test_after_close_filing_resolves_to_next_trading_day() -> None:
    resolution = resolve_event_date(utc(2023, 11, 3, 20, 1))

    assert resolution.resolved_event_date.isoformat() == "2023-11-06"
    assert resolution.event_date_policy == "after_close"


def test_weekend_filing_resolves_to_next_trading_day() -> None:
    resolution = resolve_event_date(utc(2023, 11, 4, 16, 0))

    assert resolution.resolved_event_date.isoformat() == "2023-11-06"
    assert resolution.event_date_policy == "non_trading_day"
    assert resolution.is_trading_day is False


def test_holiday_filing_resolves_to_next_trading_day() -> None:
    resolution = resolve_event_date(utc(2023, 11, 23, 16, 0))

    assert resolution.resolved_event_date.isoformat() == "2023-11-24"
    assert resolution.event_date_policy == "non_trading_day"
    assert resolution.is_early_close is True


def test_early_close_after_close_resolves_to_next_trading_day() -> None:
    resolution = resolve_event_date(utc(2012, 7, 3, 17, 30))

    assert resolution.raw_event_date.isoformat() == "2012-07-03"
    assert resolution.resolved_event_date.isoformat() == "2012-07-05"
    assert resolution.event_date_policy == "after_close"
