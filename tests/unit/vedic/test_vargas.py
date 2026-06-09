# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

pytestmark = pytest.mark.unit


def test_navamsa_in_range():
    from astrologymod.vedic.vargas import d9_navamsa
    from astrologymod.swiss import sign_index
    lon = 15.0  # mid Aries
    nav = d9_navamsa(lon)
    assert 0 <= nav < 360
    assert 0 <= sign_index(nav) < 12


def test_all_vargas_keys():
    from astrologymod.vedic.vargas import all_vargas
    v = all_vargas(120.5)
    assert 'D1' in v and 'D9' in v and 'D60' in v
    assert v['D1'] == pytest.approx(120.5, abs=0.01)


def test_varga_longitude_d10():
    from astrologymod.vedic.vargas import varga_longitude
    out = varga_longitude(0.0, 'D10')
    assert 0 <= out < 360
