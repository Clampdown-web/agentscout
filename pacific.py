"""America/Los_Angeles clock for every builder stamp.

Displayed dates, sitemap lastmod, and catalog timestamps use this zone.
A fixed offset is wrong for half the year, and the runner's local clock is not Pacific.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")


def now():
    return datetime.now(PT)


def today():
    return now().date()


def iso(when=None):
    """Offset timestamp, for example 2026-11-19T08:00:21-08:00."""
    return (when or now()).isoformat(timespec="seconds")
