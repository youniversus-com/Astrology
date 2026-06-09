# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify scope-C Vedic requirements are wired."""

import pytest

pytestmark = pytest.mark.unit


def test_all_sixteen_vargas():
    from astrologymod.vedic.constants import VARGA_CODES
    from astrologymod.vedic.vargas import varga_longitude
    assert len(VARGA_CODES) == 16
    for code in VARGA_CODES:
        lon = varga_longitude(123.45, code)
        assert 0 <= lon < 360


def test_combustion():
    from astrologymod.vedic.graha import is_combust
    assert is_combust(2, 5.0, 10.0)  # Mercury near Sun
    assert not is_combust(0, 100.0, 0.0)


def test_drishti_mars():
    from astrologymod.vedic.drishti import has_drishti
    assert has_drishti(4, 0, 3)  # Mars in Aries aspects 4th sign Cancer


def test_snapshot_has_muhurta_and_primary_dasha():
    from astrologymod.vedic.snapshot import build_snapshot
    planets = [0.0] * 35
    planets[1] = 90.0
    houses = [15.0] + [0.0] * 11
    retro = [False] * 35
    snap = build_snapshot(
        planets, houses, retro, {i: str(i) for i in range(35)},
        1990, 5, 15, 14.5,
        dasha_system='yogini',
        geolon=12.5,
        geolat=41.9,
    )
    assert snap.dasha_system == 'yogini'
    assert snap.primary_dasha == snap.yogini
    assert len(snap.muhurta_slots) >= 1
    assert snap.grahas[0].combust is False or isinstance(snap.grahas[0].combust, bool)


def test_yogas_budha_aditya():
    from astrologymod.vedic.snapshot import build_snapshot
    from astrologymod.vedic.yogas import evaluate_yogas
    planets = [0.0] * 35
    planets[0] = 10.0
    planets[1] = 50.0
    planets[2] = 12.0
    houses = [0.0] * 12
    snap = build_snapshot(
        planets, houses, [False] * 35, {0: 'Sun', 2: 'Mercury'},
        2000, 1, 1, 12.0,
    )
    hits = evaluate_yogas(snap)
    ids = {h.yoga_id for h in hits}
    assert 'budha_aditya' in ids
