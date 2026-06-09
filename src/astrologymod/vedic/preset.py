# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply Vedic tradition defaults to ephemeris configuration."""

from __future__ import annotations

from typing import Mapping


def effective_astrocfg(astrocfg: Mapping[str, str]) -> dict[str, str]:
    """Return astrocfg copy with Vedic sidereal/house overrides applied."""
    cfg = dict(astrocfg)
    if cfg.get('tradition') != 'vedic':
        return cfg
    cfg['zodiactype'] = 'sidereal'
    ayan = cfg.get('vedic_ayanamsa') or cfg.get('siderealmode') or 'LAHIRI'
    cfg['vedic_ayanamsa'] = ayan
    if ayan == 'FAGAN_BRADLEY':
        ayan = 'LAHIRI'
    cfg['siderealmode'] = ayan
    houses = cfg.get('vedic_houses', 'whole_sign')
    if houses == 'whole_sign':
        cfg['houses_system'] = 'W'
    elif houses == 'equal':
        cfg['houses_system'] = 'A'
    else:
        cfg['houses_system'] = 'W'
    return cfg


def apply_vedic_defaults(astrocfg: dict[str, str]) -> None:
    """Set astrocfg keys for a new Vedic user preset."""
    astrocfg['tradition'] = 'vedic'
    astrocfg['zodiactype'] = 'sidereal'
    astrocfg['siderealmode'] = 'LAHIRI'
    astrocfg['vedic_ayanamsa'] = 'LAHIRI'
    astrocfg['vedic_houses'] = 'whole_sign'
    astrocfg['vedic_chart_layout'] = 'north'
    astrocfg['vedic_dasha_system'] = 'vimshottari'
    astrocfg['houses_system'] = 'W'
