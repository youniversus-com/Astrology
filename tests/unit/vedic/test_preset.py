# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

pytestmark = pytest.mark.unit


def test_effective_astrocfg_vedic():
    from astrologymod.vedic.preset import effective_astrocfg
    cfg = effective_astrocfg({
        'tradition': 'vedic',
        'zodiactype': 'tropical',
        'siderealmode': 'FAGAN_BRADLEY',
        'vedic_ayanamsa': 'LAHIRI',
        'vedic_houses': 'whole_sign',
    })
    assert cfg['zodiactype'] == 'sidereal'
    assert cfg['siderealmode'] == 'LAHIRI'
    assert cfg['houses_system'] == 'W'
