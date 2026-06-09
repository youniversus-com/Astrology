# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""House cusp layout for pysweph (13-element) vs legacy bindings (12-element)."""
import pytest
import swisseph as swe

from astrologymod.swiss import _calc_positions, _normalize_house_cusps

pytestmark = pytest.mark.unit

# Amsterdam, 1990-05-15 12:00 UT — Placidus
_JD = swe.julday(1990, 5, 15, 12.0)
_LAT = 52.37
_LON = 4.89


def test_pysweph_houses_raw_cusp_count():
    sh = swe.houses(_JD, _LAT, _LON, b'P')
    assert len(sh[0]) == 13


def test_normalize_house_cusps_twelve_elements():
    sh = swe.houses(_JD, _LAT, _LON, b'P')
    cusps = _normalize_house_cusps(sh[0])
    assert len(cusps) == 12
    # Astrology: asc=0, dsc=6 (1st and 7th house cusps)
    assert cusps[6] == pytest.approx((cusps[0] + 180.0) % 360.0, abs=0.05)


def test_normalize_house_cusps_passthrough_twelve():
    twelve = [float(i) for i in range(12)]
    assert _normalize_house_cusps(twelve) == twelve


def test_calc_positions_nested_tuple():
    sh = swe.calc_ut(_JD, swe.SUN, swe.FLG_SWIEPH + swe.FLG_SPEED)
    pos = _calc_positions(sh)
    assert isinstance(pos[0], float)
    assert 0 <= pos[0] < 360


def test_normalize_house_cusps_strips_leading_slot():
    raw = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0]
    assert _normalize_house_cusps(raw) == raw[1:13]
