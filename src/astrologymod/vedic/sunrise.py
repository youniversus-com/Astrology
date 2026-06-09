# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sunrise and sunset via Swiss Ephemeris ``rise_trans``."""

from __future__ import annotations

import datetime

import swisseph as swe

from astrologymod import install_paths
from astrologymod.paths import user_data_dir


def _ephe_path() -> str:
    return install_paths.ephemeris_search_paths(
        __import__('pathlib').Path(user_data_dir()) / 'swiss_ephemeris',
    )


def sunrise_sunset_ut(
    year: int,
    month: int,
    day: int,
    geolon: float,
    geolat: float,
    altitude: float = 0.0,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    """Return (sunrise, sunset) as naive UTC datetimes for a geographic location."""
    swe.set_ephe_path(_ephe_path())
    jd = swe.julday(year, month, day, 0.0)
    geo = (float(geolon), float(geolat), float(altitude))
    sunrise: datetime.datetime | None = None
    sunset: datetime.datetime | None = None
    try:
        res, tret = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geo)
        if res == 0:
            y, m, d, h = swe.revjul(tret[0], swe.GREG_CAL)
            sunrise = datetime.datetime(
                y, m, d, int(h), int(round((h % 1) * 60)),
            )
        res2, tret2 = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geo)
        if res2 == 0:
            y, m, d, h = swe.revjul(tret2[0], swe.GREG_CAL)
            sunset = datetime.datetime(
                y, m, d, int(h), int(round((h % 1) * 60)),
            )
    except swe.Error:
        pass
    return sunrise, sunset
