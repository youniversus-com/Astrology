# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Ecliptic longitude must map to a single zodiac sign at 30° boundaries."""
import pytest

from astrologymod.swiss import sign_index

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('lon,expected', [
    (0.0, 0),
    (29.99, 0),
    (30.0, 1),
    (30.01, 1),
    (359.99, 11),
])
def test_zodiac_sign_cusp_assignment(lon, expected):
    assert sign_index(lon) == expected
