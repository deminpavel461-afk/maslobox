from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")

_RELATIVE = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
}


def parse_desired_datetime(raw: str | None, *, now: datetime | None = None) -> datetime | None:
    """Best-effort parse of free-form RU datetime. Returns aware datetime or None."""
    if raw is None:
        return None
    text = raw.strip().lower()
    if not text:
        return None

    now = now or datetime.now(tz=MOSCOW)
    if now.tzinfo is None:
        now = now.replace(tzinfo=MOSCOW)
    else:
        now = now.astimezone(MOSCOW)

    # ISO / common numeric formats
    for fmt in (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d.%m.%y %H:%M",
    ):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=MOSCOW)
            return dt
        except ValueError:
            pass

    # date only
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(text, fmt).replace(hour=12, minute=0, tzinfo=MOSCOW)
            return dt
        except ValueError:
            pass

    time_match = re.search(r"(?:в\s+|после\s+|к\s+)?(\d{1,2})[:.\-](\d{2})", text)
    hour = minute = None
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        if hour > 23 or minute > 59:
            return None
    else:
        after_hour = re.search(r"после\s+(\d{1,2})", text)
        if after_hour:
            hour = int(after_hour.group(1))
            minute = 0
            if hour > 23:
                return None

    day_offset = None
    for word, offset in _RELATIVE.items():
        if word in text:
            day_offset = offset
            break

    weekday_map = {
        "понедельник": 0,
        "вторник": 1,
        "среду": 2,
        "среда": 2,
        "четверг": 3,
        "пятницу": 4,
        "пятница": 4,
        "субботу": 5,
        "суббота": 5,
        "воскресенье": 6,
    }
    target_weekday = None
    for word, wd in weekday_map.items():
        if word in text:
            target_weekday = wd
            break

    if day_offset is None and target_weekday is not None:
        delta = (target_weekday - now.weekday()) % 7
        day_offset = delta if delta > 0 else 7

    if day_offset is None and hour is None:
        return None

    base = now + timedelta(days=day_offset or 0)
    if hour is None:
        hour, minute = 12, 0
    return base.replace(hour=hour, minute=minute or 0, second=0, microsecond=0)


def is_within_schedule(dt: datetime, schedule: list[dict]) -> bool:
    """Check if datetime falls into point working hours. schedule days: 0=Mon..6=Sun."""
    local = dt.astimezone(MOSCOW) if dt.tzinfo else dt.replace(tzinfo=MOSCOW)
    weekday = local.weekday()
    minutes = local.hour * 60 + local.minute

    for slot in schedule:
        days = slot.get("days") or []
        if weekday not in days:
            continue
        open_h, open_m = _parse_hhmm(slot["open"])
        close_h, close_m = _parse_hhmm(slot["close"])
        open_min = open_h * 60 + open_m
        close_min = close_h * 60 + close_m
        if open_min <= minutes < close_min:
            return True
    return False


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)
