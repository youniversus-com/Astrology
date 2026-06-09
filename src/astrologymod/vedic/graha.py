# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Graha labels, combustion, and status helpers."""

from __future__ import annotations

from astrologymod.vedic.constants import COMBUST_ORB, LORD_LABELS

VEDIC_LABELS: dict[int, str] = {
    0: 'Surya',
    1: 'Chandra',
    2: 'Budha',
    3: 'Shukra',
    4: 'Mangal',
    5: 'Guru',
    6: 'Shani',
    10: 'Rahu',
    29: 'Ketu',
}

# Extra Swiss Ephemeris sidereal modes for Jyotish (beyond Western UI list)
VEDIC_AYANAMSA_MODES = (
    'LAHIRI',
    'RAMAN',
    'KRISHNAMURTI',
    'SURYASIDDHANTA',
    'SURYASIDDHANTA_MSUN',
    'ARYABHATA',
    'SS_CITRA',
    'TRUE_CITRA',
    'YUKTESHWAR',
    'JN_BHASIN',
)


def vedic_label(planet_id: int, fallback: str = '') -> str:
    """Sanskrit-style graha name."""
    return VEDIC_LABELS.get(planet_id, fallback or LORD_LABELS.get(planet_id, str(planet_id)))


def is_combust(planet_id: int, planet_lon: float, sun_lon: float) -> bool:
    """True if graha is within combustion orb of the Sun."""
    if planet_id not in COMBUST_ORB or planet_id == 0:
        return False
    diff = abs((planet_lon - sun_lon + 180) % 360 - 180)
    return diff <= COMBUST_ORB[planet_id]


def parse_varga_display(cfg_value: str) -> tuple[str, ...]:
    """Parse ``vedic_varga_display`` astrocfg string."""
    codes = tuple(c.strip().upper() for c in cfg_value.split(',') if c.strip())
    return codes if codes else ('D1', 'D9', 'D10')
