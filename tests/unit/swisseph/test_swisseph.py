# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Swiss Ephemeris binding smoke tests."""
import pytest

pytestmark = pytest.mark.unit


def test_swisseph_version():
    import swisseph as swe
    assert swe.version


def test_julday_and_calc_ut():
    import swisseph as swe
    jd = swe.julday(2000, 1, 1, 12.0)
    assert jd > 2450000
    result = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    # pysweph: (coords_tuple, retflag) or flat lon, lat, dist, speeds...
    if isinstance(result[0], (tuple, list)):
        lon = result[0][0]
    else:
        lon = result[0]
    assert 0 <= lon < 360
