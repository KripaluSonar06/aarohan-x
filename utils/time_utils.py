"""
Timezone-aware time utilities. All internal times are stored in IST.
"""
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from config.settings import settings

IST = ZoneInfo(settings.TIMEZONE)

def now_ist() -> datetime:
    """Return current time in IST."""
    return datetime.now(IST)

def is_quiet_hours(dt: datetime | None = None) -> bool:
    """
    Check if given time (default now) falls within quiet hours.
    Quiet hours: 21:00 to 09:00 IST.
    """
    if dt is None:
        dt = now_ist()
    hour = dt.hour
    return (hour >= settings.QUIET_HOURS_START) or (hour < settings.QUIET_HOURS_END)

def format_ist(dt: datetime) -> str:
    """Return ISO string in IST."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST).isoformat()

def next_business_time(dt: datetime | None = None) -> datetime:
    """
    Return next allowed time for customer contact (after quiet hours).
    """
    if dt is None:
        dt = now_ist()
    if is_quiet_hours(dt):
        # Move to 9 AM same day if before 9, else next day
        if dt.hour < settings.QUIET_HOURS_END:
            next_time = dt.replace(hour=settings.QUIET_HOURS_END, minute=0, second=0, microsecond=0)
        else:
            next_time = dt.replace(hour=settings.QUIET_HOURS_END, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_time
    return dt