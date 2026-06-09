# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

pytestmark = pytest.mark.unit


def test_nakshatra_ashwini_start():
    from astrologymod.vedic.nakshatra import nakshatra_info
    info = nakshatra_info(0.0)
    assert info.name == 'Ashwini'
    assert info.pada == 1


def test_nakshatra_pada_boundary():
    from astrologymod.vedic.nakshatra import nakshatra_info, NAKSHATRA_SPAN, PADA_SPAN
    lon = NAKSHATRA_SPAN * 2 + PADA_SPAN * 1.5
    info = nakshatra_info(lon)
    assert info.index == 2
    assert info.pada == 2


def test_vimshottari_balance():
    from astrologymod.vedic.nakshatra import vimshottari_balance_years
    lord, yrs = vimshottari_balance_years(0.0)
    assert lord == 9  # Ketu
    assert 0 < yrs <= 7
