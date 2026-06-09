# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rashi (sign) helpers and whole-sign bhavas."""

from __future__ import annotations

from dataclasses import dataclass

from astrologymod.swiss import sign_index, _normalize_longitude
from astrologymod.vedic.constants import LORD_LABELS, RASHI_LORDS, RASHI_NAMES, RASHI_NAMES_EN


@dataclass(frozen=True)
class RashiInfo:
    """Sign placement."""

    index: int
    name: str
    name_en: str
    lord_id: int
    lord_label: str
    degree_in_sign: float


def rashi_info(lon: float) -> RashiInfo:
    """Sign metadata for ecliptic longitude."""
    lon = _normalize_longitude(lon)
    idx = sign_index(lon)
    deg = lon - idx * 30.0
    lord = RASHI_LORDS[idx]
    return RashiInfo(
        index=idx,
        name=RASHI_NAMES[idx],
        name_en=RASHI_NAMES_EN[idx],
        lord_id=lord,
        lord_label=LORD_LABELS.get(lord, '?'),
        degree_in_sign=deg,
    )


def whole_sign_house(planet_sign: int, lagna_sign: int) -> int:
    """Bhava 1-12: whole-sign house from lagna sign."""
    return (planet_sign - lagna_sign) % 12 + 1


def house_lord(house_num: int, lagna_sign: int) -> int:
    """Sign lord of the sign occupying ``house_num`` (1-based)."""
    sign = (lagna_sign + house_num - 1) % 12
    return RASHI_LORDS[sign]
