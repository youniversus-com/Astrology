# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Nakshatra and pada from sidereal longitude."""

from __future__ import annotations

from dataclasses import dataclass

from astrologymod.vedic.constants import (
    NAKSHATRA_LORDS,
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN,
    PADA_SPAN,
    VIMSHOTTARI_LORD_IDS,
    VIMSHOTTARI_YEARS,
)
from astrologymod.swiss import _normalize_longitude


@dataclass(frozen=True)
class NakshatraInfo:
    """One lunar mansion placement."""

    index: int
    name: str
    lord_id: int
    lord_label: str
    pada: int
    degree_in_nakshatra: float


def nakshatra_index(lon: float) -> int:
    """0-based nakshatra index for sidereal longitude."""
    lon = _normalize_longitude(lon)
    return int(lon / NAKSHATRA_SPAN) % 27


def nakshatra_info(lon: float) -> NakshatraInfo:
    """Full nakshatra metadata for a longitude."""
    from astrologymod.vedic.constants import LORD_LABELS

    lon = _normalize_longitude(lon)
    idx = nakshatra_index(lon)
    start = idx * NAKSHATRA_SPAN
    deg_in = lon - start
    pada = int(deg_in / PADA_SPAN) + 1
    if pada > 4:
        pada = 4
    lord_cycle = VIMSHOTTARI_LORD_IDS[idx % 9]
    return NakshatraInfo(
        index=idx,
        name=NAKSHATRA_NAMES[idx],
        lord_id=lord_cycle,
        lord_label=LORD_LABELS.get(lord_cycle, '?'),
        pada=pada,
        degree_in_nakshatra=deg_in,
    )


def vimshottari_balance_years(moon_lon: float) -> tuple[int, float]:
    """Return (starting lord id, years remaining in first mahadasha)."""
    lon = _normalize_longitude(moon_lon)
    idx = nakshatra_index(lon)
    start = idx * NAKSHATRA_SPAN
    fraction = (lon - start) / NAKSHATRA_SPAN
    lord = VIMSHOTTARI_LORD_IDS[idx % 9]
    total = VIMSHOTTARI_YEARS[idx % 9]
    remaining = (1.0 - fraction) * total
    return lord, remaining
