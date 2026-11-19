from datetime import datetime

from backend.services.datetime_parse import is_within_schedule, parse_desired_datetime
from backend.services.datetime_parse import MOSCOW


def test_parse_tomorrow_after():
    now = datetime(2026, 11, 19, 10, 0, tzinfo=MOSCOW)  # Thursday
    dt = parse_desired_datetime("завтра, после 14:00", now=now)
    assert dt is not None
    assert dt.day == 20
    assert dt.hour == 14


def test_parse_iso():
    dt = parse_desired_datetime("2026-11-20 15:30")
    assert dt is not None
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == (2026, 11, 20, 15, 30)


def test_parse_unparseable():
    assert parse_desired_datetime("как получится вечером") is None


def test_schedule_check():
    schedule = [{"days": [0, 1, 2, 3, 4, 5], "open": "09:00", "close": "20:00"}]
    inside = datetime(2026, 11, 20, 12, 0, tzinfo=MOSCOW)  # Friday
    outside = datetime(2026, 11, 22, 12, 0, tzinfo=MOSCOW)  # Sunday
    late = datetime(2026, 11, 20, 20, 30, tzinfo=MOSCOW)
    assert is_within_schedule(inside, schedule)
    assert not is_within_schedule(outside, schedule)
    assert not is_within_schedule(late, schedule)
