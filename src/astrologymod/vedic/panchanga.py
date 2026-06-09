# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Panchanga: tithi, yoga, karana, vara, nakshatra for a moment."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from astrologymod.swiss import _normalize_longitude
from astrologymod.vedic.constants import (
    KARANA_NAMES,
    TITHI_NAMES,
    VARA_LORDS,
    VARA_NAMES,
    YOGA_NAMES,
)
from astrologymod.vedic.nakshatra import nakshatra_info


@dataclass(frozen=True)
class Panchanga:
    """Five limbs of the Hindu calendar at one instant."""

    tithi: int
    tithi_name: str
    nakshatra: str
    yoga: int
    yoga_name: str
    karana: int
    karana_name: str
    vara: int
    vara_name: str
    vara_lord_id: int


def _elongation(sun_lon: float, moon_lon: float) -> float:
    d = _normalize_longitude(moon_lon - sun_lon)
    return d


def tithi_number(sun_lon: float, moon_lon: float) -> int:
    """Tithi 1-30."""
    elong = _elongation(sun_lon, moon_lon)
    t = int(elong / 12.0) + 1
    if t > 30:
        t = 30
    return t


def yoga_number(sun_lon: float, moon_lon: float) -> int:
    """Yoga 1-27."""
    total = _normalize_longitude(sun_lon + moon_lon)
    y = int(total / (360.0 / 27.0)) + 1
    if y > 27:
        y = 27
    return y


def karana_number(sun_lon: float, moon_lon: float) -> int:
    """Karana 1-11 (simplified cycle)."""
    elong = _elongation(sun_lon, moon_lon)
    k = int(elong / 6.0) + 1
    if k > 11:
        k = ((k - 1) % 11) + 1
    return k


def compute_panchanga(
    sun_lon: float,
    moon_lon: float,
    dt: datetime.datetime,
) -> Panchanga:
    """Full panchanga from sidereal Sun/Moon and local datetime."""
    t = tithi_number(sun_lon, moon_lon)
    t_name = TITHI_NAMES[min(t - 1, 14)]
    y = yoga_number(sun_lon, moon_lon)
    k = karana_number(sun_lon, moon_lon)
    nk = nakshatra_info(moon_lon)
    wd = dt.weekday()  # Monday=0 … Sunday=6
    return Panchanga(
        tithi=t,
        tithi_name=t_name,
        nakshatra=nk.name,
        yoga=y,
        yoga_name=YOGA_NAMES[y - 1],
        karana=k,
        karana_name=KARANA_NAMES[min(k - 1, 10)],
        vara=wd,
        vara_name=VARA_NAMES[wd],
        vara_lord_id=VARA_LORDS[wd],
    )
