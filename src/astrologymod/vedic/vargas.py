# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shodashvarga (divisional chart) longitude transforms."""

from __future__ import annotations

from astrologymod.swiss import _normalize_longitude, sign_index

MOVABLE = (0, 3, 6, 9)
FIXED = (1, 4, 7, 10)
DUAL = (2, 5, 8, 11)


def _sign_and_degree(lon: float) -> tuple[int, float]:
    lon = _normalize_longitude(lon)
    s = sign_index(lon)
    return s, lon - s * 30.0


def _varga_sign_offset(sign: int, part: int, movable_start: int, fixed_start: int, dual_start: int) -> int:
    if sign in MOVABLE:
        return (movable_start + part) % 12
    if sign in FIXED:
        return (fixed_start + part) % 12
    return (dual_start + part) % 12


def _lon_from_part(sign: int, deg: float, parts: int, part_idx: int) -> float:
    part_size = 30.0 / parts
    return sign * 30.0 + (part_idx * part_size) + (deg % part_size) * parts


def d1(lon: float) -> float:
    return _normalize_longitude(lon)


def d2_hora(lon: float) -> float:
    """Hora (D2): Sun/Moon horas."""
    sign, deg = _sign_and_degree(lon)
    if sign % 2 == 0:  # even sign
        h_sign = 3 if deg < 15 else 4  # Cancer / Leo
    else:
        h_sign = 4 if deg < 15 else 3
    part_deg = (deg % 15) * 2
    return h_sign * 30.0 + part_deg


def d3_drekkana(lon: float) -> float:
    """Drekkana (D3)."""
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 10.0)
    if part > 2:
        part = 2
    if sign % 2 == 0:
        offsets = (sign, (sign + 8) % 12, (sign + 4) % 12)
    else:
        offsets = (sign, (sign + 4) % 12, (sign + 8) % 12)
    return offsets[part] * 30.0 + (deg % 10.0) * 3.0


def d4_chaturthamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 7.5)
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 3) % 12
    else:
        start = (sign + 6) % 12
    return (start + part) % 12 * 30.0 + (deg % 7.5) * 4.0


def d7_saptamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / (30.0 / 7.0))
    if part > 6:
        part = 6
    if sign % 2 == 0:
        start = sign
    else:
        start = (sign + 6) % 12
    return (start + part) % 12 * 30.0 + (deg % (30.0 / 7.0)) * 7.0


def d9_navamsa(lon: float) -> float:
    """Navamsa (D9)."""
    sign, deg = _sign_and_degree(lon)
    part = int(deg / (30.0 / 9.0))
    if part > 8:
        part = 8
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 8) % 12
    else:
        start = (sign + 4) % 12
    return _normalize_longitude((start + part) % 12 * 30.0 + (deg % (30.0 / 9.0)) * 9.0)


def d10_dasamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 3.0)
    if part > 9:
        part = 9
    if sign % 2 == 0:
        start = sign
    else:
        start = (sign + 8) % 12
    return (start + part) % 12 * 30.0 + (deg % 3.0) * 10.0


def d12_dwadasamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 2.5)
    return (sign + part) % 12 * 30.0 + (deg % 2.5) * 12.0


def d16_shodasamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 1.875)
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 4) % 12
    else:
        start = (sign + 8) % 12
    return (start + part) % 12 * 30.0 + (deg % 1.875) * 16.0


def d20_vimsamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 1.5)
    if sign in MOVABLE:
        start = 0
    elif sign in FIXED:
        start = 8
    else:
        start = 4
    return (start + part) % 12 * 30.0 + (deg % 1.5) * 20.0


def d24_chaturvimsamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 1.25)
    if sign % 2 == 0:
        start = 4
    else:
        start = 3
    return (start + part) % 12 * 30.0 + (deg % 1.25) * 24.0


def d27_bhamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / (30.0 / 27.0))
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 8) % 12
    else:
        start = (sign + 4) % 12
    return (start + part) % 12 * 30.0 + (deg % (30.0 / 27.0)) * 27.0


def d30_trimsamsa(lon: float) -> float:
    """Trimsamsa (D30) — odd/even sign degree bands."""
    sign, deg = _sign_and_degree(lon)
    if sign % 2 == 1:  # odd
        if deg < 5:
            s = 10  # Saturn -> Capricorn
        elif deg < 10:
            s = 8   # Jupiter -> Sagittarius
        elif deg < 18:
            s = 4   # Mars -> Leo
        elif deg < 25:
            s = 3   # Venus -> Libra
        else:
            s = 2   # Mercury -> Gemini
    else:
        if deg < 5:
            s = 2
        elif deg < 12:
            s = 3
        elif deg < 20:
            s = 4
        elif deg < 25:
            s = 5
        else:
            s = 6
    return s * 30.0 + (deg % 5) * 6.0


def d40_khavedamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 0.75)
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 6) % 12
    else:
        start = (sign + 3) % 12
    return (start + part) % 12 * 30.0 + (deg % 0.75) * 40.0


def d45_akshavedamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / (30.0 / 45.0))
    if sign in MOVABLE:
        start = sign
    elif sign in FIXED:
        start = (sign + 8) % 12
    else:
        start = (sign + 4) % 12
    return (start + part) % 12 * 30.0 + (deg % (30.0 / 45.0)) * 45.0


def d60_shashtiamsa(lon: float) -> float:
    sign, deg = _sign_and_degree(lon)
    part = int(deg / 0.5)
    return (sign + part) % 12 * 30.0 + (deg % 0.5) * 60.0


_VARGA_FUNCS = {
    'D1': d1,
    'D2': d2_hora,
    'D3': d3_drekkana,
    'D4': d4_chaturthamsa,
    'D7': d7_saptamsa,
    'D9': d9_navamsa,
    'D10': d10_dasamsa,
    'D12': d12_dwadasamsa,
    'D16': d16_shodasamsa,
    'D20': d20_vimsamsa,
    'D24': d24_chaturvimsamsa,
    'D27': d27_bhamsa,
    'D30': d30_trimsamsa,
    'D40': d40_khavedamsa,
    'D45': d45_akshavedamsa,
    'D60': d60_shashtiamsa,
}


def varga_longitude(lon: float, code: str) -> float:
    """Compute divisional longitude for ``code`` (e.g. ``D9``)."""
    fn = _VARGA_FUNCS.get(code)
    if fn is None:
        raise ValueError(f'Unknown varga: {code}')
    return _normalize_longitude(fn(lon))


def all_vargas(lon: float) -> dict[str, float]:
    """All supported varga longitudes for one graha."""
    return {code: varga_longitude(lon, code) for code in _VARGA_FUNCS}
