# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Vedic (Jyotish) astrology: vargas, dashas, panchanga, yogas, muhurta."""

from astrologymod.vedic.snapshot import VedicChartSnapshot, build_snapshot
from astrologymod.vedic.vargas import varga_longitude, all_vargas

__all__ = [
    'VedicChartSnapshot',
    'build_snapshot',
    'varga_longitude',
    'all_vargas',
]
