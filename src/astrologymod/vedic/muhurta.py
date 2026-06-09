# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Muhurta scoring and inauspicious periods (Rahu Kaal, etc.)."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from astrologymod.vedic.panchanga import compute_panchanga
from astrologymod.vedic.sunrise import sunrise_sunset_ut


@dataclass(frozen=True)
class MuhurtaSlot:
    """Rated time window."""

    start: datetime.datetime
    end: datetime.datetime
    score: float
    notes: str


# Rahu Kaal weekday segment (1=Sunday .. 7=Saturday) -> segment index 0-7 of daylight eighths
RAHU_KAAL_SEGMENT = {
    6: 7, 0: 1, 1: 2, 2: 5, 3: 6, 4: 4, 5: 3,  # Python weekday: Mon=0
}


def rahu_kaal_window(
    day: datetime.date,
    sunrise: datetime.datetime,
    sunset: datetime.datetime,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Approximate Rahu Kaal for a day (eighth of daylight)."""
    wd = day.weekday()
    seg = RAHU_KAAL_SEGMENT.get(wd, 1)
    span = (sunset - sunrise) / 8
    start = sunrise + span * (seg - 1)
    end = start + span
    return start, end


def score_day(
    sun_lon: float,
    moon_lon: float,
    dt: datetime.datetime,
    sunrise: datetime.datetime | None = None,
    sunset: datetime.datetime | None = None,
) -> tuple[float, list[str]]:
    """Heuristic 0-100 score and notes for electional use."""
    pan = compute_panchanga(sun_lon, moon_lon, dt)
    score = 50.0
    notes: list[str] = []

    if pan.tithi in (4, 9, 14, 30):
        score -= 10
        notes.append('Challenging tithi')
    if pan.tithi in (2, 3, 5, 7, 10, 11, 12, 13):
        score += 8
        notes.append('Shukla paksha friendly tithi')

    if sunrise and sunset:
        rk_start, rk_end = rahu_kaal_window(dt.date(), sunrise, sunset)
        if rk_start <= dt <= rk_end:
            score -= 25
            notes.append('Rahu Kaal')

    if pan.nakshatra in ('Rohini', 'Pushya', 'Hasta', 'Revati', 'Shravana'):
        score += 10
        notes.append('Auspicious nakshatra')

    return max(0.0, min(100.0, score)), notes


def scan_day_slots(
    sun_lon: float,
    moon_lon: float,
    day: datetime.date,
    slot_minutes: int = 60,
    geolon: float | None = None,
    geolat: float | None = None,
    altitude: float = 0.0,
) -> list[MuhurtaSlot]:
    """Muhurta scores across daylight hours (uses sunrise/sunset when location given)."""
    sunrise = sunset = None
    if geolon is not None and geolat is not None:
        sunrise, sunset = sunrise_sunset_ut(
            day.year, day.month, day.day, geolon, geolat, altitude,
        )
    start_hour, end_hour = 6, 22
    if sunrise and sunset:
        start_hour = max(0, sunrise.hour)
        end_hour = min(23, sunset.hour + 1)

    slots: list[MuhurtaSlot] = []
    for hour in range(start_hour, end_hour):
        start = datetime.datetime(day.year, day.month, day.day, hour, 0)
        end = start + datetime.timedelta(minutes=slot_minutes)
        sc, notes = score_day(sun_lon, moon_lon, start, sunrise, sunset)
        slots.append(MuhurtaSlot(
            start=start,
            end=end,
            score=sc,
            notes='; '.join(notes) if notes else 'Neutral',
        ))
    slots.sort(key=lambda s: s.score, reverse=True)
    return slots
