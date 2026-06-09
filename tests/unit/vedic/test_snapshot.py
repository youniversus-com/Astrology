# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import datetime

import pytest

pytestmark = pytest.mark.unit


def test_birth_datetime_handles_second_rollover():
    from astrologymod.vedic.snapshot import _birth_datetime

    dt = _birth_datetime(2026, 6, 5, 11.9999999999)
    assert dt.second < 60
    assert dt.minute < 60


def test_build_snapshot_minimal():
    from astrologymod.vedic.snapshot import build_snapshot
    planets = [0.0] * 35
    planets[1] = 45.0
    houses = [0.0] * 12
    houses[0] = 10.0
    retro = [False] * 35
    labels = {i: str(i) for i in range(35)}
    snap = build_snapshot(
        planets, houses, retro, labels,
        2000, 1, 1, 12.0,
    )
    assert snap.lagna_sign == 0
    assert len(snap.grahas) >= 7
    assert snap.panchanga.tithi >= 1
    assert len(snap.vimshottari) >= 1


def test_panchanga_yoga_range():
    from astrologymod.vedic.panchanga import compute_panchanga
    pan = compute_panchanga(0.0, 90.0, datetime.datetime(2020, 6, 15, 12))
    assert 1 <= pan.yoga <= 27
