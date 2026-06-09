# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Timezone helpers using the stdlib ``zoneinfo`` module (Python 3.9+)."""

from __future__ import annotations

from datetime import datetime, timedelta


def localize_naive(naive: datetime, tz_name: str) -> datetime:
    """Attach an IANA timezone to a naive local datetime."""
    from zoneinfo import ZoneInfo

    return naive.replace(tzinfo=ZoneInfo(tz_name))


def utc_offset_hours(dt: datetime) -> float:
    """Return UTC offset in hours (legacy ``offsetToTz`` compatibility)."""
    offset = dt.utcoffset()
    if offset is None:
        return 0.0
    return offset.total_seconds() / 3600.0


def naive_utc(dt: datetime) -> datetime:
    """Convert a timezone-aware datetime to naive UTC."""
    offset = dt.utcoffset()
    if offset is None:
        return dt
    return dt.replace(tzinfo=None) - offset


def utc_offset_timedelta(hours: float) -> timedelta:
    """Build a ``timedelta`` from a legacy UTC offset stored in hours."""
    return timedelta(seconds=float(hours) * 3600.0)
