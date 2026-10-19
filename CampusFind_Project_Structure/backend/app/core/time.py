"""Helpers for exposing stored UTC timestamps unambiguously to clients."""

from datetime import datetime, timezone


def utc_isoformat(value: datetime) -> str:
    """Serialize a UTC timestamp with an explicit UTC offset.

    CampusFind historically stores system timestamps as naive UTC values.
    Treat those values as UTC, rather than letting browser clients mistake
    them for local time. Aware values are normalized to UTC as well.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")
