# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for essential dignities (Swiss Ephemeris planet ids)."""
import pytest
import swisseph as swe

from astrologymod.dignities import getdignities

pytestmark = pytest.mark.unit


def test_getdignities_returns_nine_values():
    digs = getdignities(234.27, False, 'termse')
    assert len(digs) == 9
    assert all(isinstance(p, int) for p in digs)


def test_getdignities_day_vs_night_triplicity_order():
    lon = 45.0  # Taurus
    day = getdignities(lon, True, 'PTERMS')
    night = getdignities(lon, False, 'PTERMS')
    # Triplicity rulers 1 and 2 swap between day and night charts.
    assert day[2] != night[2] or day[3] != night[3]
    assert day[4] == night[4]  # participating ruler unchanged


def test_getdignities_ruler_in_sign():
    # 15° Leo (~135°): traditional ruler is Sun.
    digs = getdignities(135.0, True, 'PTERMS')
    assert digs[0] == swe.SUN


def test_getdignities_terms_slot_is_planet_id():
    digs = getdignities(234.27, False, 'termse')
    assert digs[5] in range(10)  # swe.SUN..swe.PLUTO range used by swisseph
