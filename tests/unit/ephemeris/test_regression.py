# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Swiss Ephemeris regression: known dates vs expected ecliptic longitudes."""
import pytest
import swisseph as swe

pytestmark = pytest.mark.unit


def _sun_lon(jd):
    result = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    if isinstance(result[0], (tuple, list)):
        return result[0][0]
    return result[0]


def _moon_lon(jd):
    result = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    if isinstance(result[0], (tuple, list)):
        return result[0][0]
    return result[0]


def test_j2000_noon_sun_longitude():
    # 2000-01-01 12:00 UT — Swiss Ephemeris reference ~280.37° tropical
    jd = swe.julday(2000, 1, 1, 12.0)
    assert _sun_lon(jd) == pytest.approx(280.366, abs=0.02)


def test_j2000_noon_moon_longitude():
    jd = swe.julday(2000, 1, 1, 12.0)
    assert _moon_lon(jd) == pytest.approx(223.324, abs=0.05)


def test_ephemeris_path_set():
    jd = swe.julday(1990, 6, 15, 12.0)
    lon = _sun_lon(jd)
    assert 0 <= lon < 360
