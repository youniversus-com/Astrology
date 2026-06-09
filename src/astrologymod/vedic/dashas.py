# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Vimshottari, Yogini, and Ashtottari dasha timelines."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from astrologymod.vedic.constants import (
    ASHTOTTARI_LORD_IDS,
    ASHTOTTARI_TOTAL,
    ASHTOTTARI_YEARS,
    LORD_LABELS,
    VIMSHOTTARI_LORD_IDS,
    VIMSHOTTARI_TOTAL,
    VIMSHOTTARI_YEARS,
    YOGINI_LORD_IDS,
    YOGINI_TOTAL,
    YOGINI_YEARS,
)
from astrologymod.vedic.nakshatra import vimshottari_balance_years


@dataclass(frozen=True)
class DashaPeriod:
    """One dasha segment."""

    level: str
    lord_id: int
    lord_label: str
    start: datetime.datetime
    end: datetime.datetime


def _build_sequence(
    lord_ids: tuple[int, ...],
    years: tuple[float, ...],
    total: float,
    start_lord: int,
    balance_years: float,
    birth: datetime.datetime,
    levels: tuple[str, ...],
    depth: int,
) -> list[DashaPeriod]:
    """Build mahadasha list from birth."""
    periods: list[DashaPeriod] = []
    idx = lord_ids.index(start_lord) if start_lord in lord_ids else 0
    n = len(lord_ids)
    current = birth
    first = True
    while current.year < birth.year + 120 and len(periods) < 200:
        lord = lord_ids[idx % n]
        yrs = years[idx % n]
        if first:
            yrs = balance_years
            first = False
        end = current + datetime.timedelta(days=yrs * 365.25)
        periods.append(DashaPeriod(
            level=levels[0],
            lord_id=lord,
            lord_label=LORD_LABELS.get(lord, '?'),
            start=current,
            end=end,
        ))
        current = end
        idx += 1
    return periods


def vimshottari_mahadasha(
    moon_lon: float,
    birth: datetime.datetime,
) -> list[DashaPeriod]:
    """Vimshottari Mahadasha periods from birth."""
    lord, balance = vimshottari_balance_years(moon_lon)
    return _build_sequence(
        VIMSHOTTARI_LORD_IDS,
        VIMSHOTTARI_YEARS,
        VIMSHOTTARI_TOTAL,
        lord,
        balance,
        birth,
        ('Mahadasha',),
        1,
    )


def vimshottari_antardasha(
    maha: DashaPeriod,
    moon_lon: float,
) -> list[DashaPeriod]:
    """Antardashas within one mahadasha."""
    lord, _ = vimshottari_balance_years(moon_lon)
    idx = VIMSHOTTARI_LORD_IDS.index(maha.lord_id)
    n = len(VIMSHOTTARI_LORD_IDS)
    total_years = VIMSHOTTARI_YEARS[idx % n]
    maha_years = (maha.end - maha.start).days / 365.25
    periods: list[DashaPeriod] = []
    current = maha.start
    for i in range(n):
        sub_lord = VIMSHOTTARI_LORD_IDS[(idx + i) % n]
        sub_years = VIMSHOTTARI_YEARS[(idx + i) % n]
        span = maha_years * (sub_years / VIMSHOTTARI_TOTAL)
        end = current + datetime.timedelta(days=span * 365.25)
        if end > maha.end:
            end = maha.end
        periods.append(DashaPeriod(
            level='Antardasha',
            lord_id=sub_lord,
            lord_label=LORD_LABELS.get(sub_lord, '?'),
            start=current,
            end=end,
        ))
        current = end
        if current >= maha.end:
            break
    return periods


def yogini_dasha(moon_lon: float, birth: datetime.datetime) -> list[DashaPeriod]:
    """Yogini dasha (36-year cycle) from Moon nakshatra."""
    from astrologymod.vedic.nakshatra import nakshatra_index

    idx = nakshatra_index(moon_lon) % 8
    lord = YOGINI_LORD_IDS[idx]
    span = 360.0 / 27.0
    lon_norm = moon_lon % 360.0
    start_n = idx * span
    fraction = (lon_norm - start_n) / span
    balance = (1.0 - fraction) * YOGINI_YEARS[idx]
    return _build_sequence(
        YOGINI_LORD_IDS,
        YOGINI_YEARS,
        YOGINI_TOTAL,
        lord,
        balance,
        birth,
        ('Yogini',),
        1,
    )


def ashtottari_dasha(moon_lon: float, birth: datetime.datetime) -> list[DashaPeriod]:
    """Ashtottari dasha (108-year cycle)."""
    from astrologymod.vedic.nakshatra import nakshatra_index

    idx = nakshatra_index(moon_lon) % 9
    lord = ASHTOTTARI_LORD_IDS[idx]
    span = 360.0 / 27.0
    lon_norm = moon_lon % 360.0
    start_n = idx * span
    fraction = (lon_norm - start_n) / span
    balance = (1.0 - fraction) * ASHTOTTARI_YEARS[idx]
    return _build_sequence(
        ASHTOTTARI_LORD_IDS,
        ASHTOTTARI_YEARS,
        ASHTOTTARI_TOTAL,
        lord,
        balance,
        birth,
        ('Ashtottari',),
        1,
    )
