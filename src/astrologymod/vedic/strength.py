# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shadbala (simplified) and Ashtakavarga bindu tables."""

from __future__ import annotations

from dataclasses import dataclass

from astrologymod.vedic.constants import DEBILITATION_SIGN, EXALTATION_SIGN, RASHI_LORDS
from astrologymod.vedic.rashi import whole_sign_house


@dataclass(frozen=True)
class ShadbalaScore:
    """Simplified sixfold strength total (0-100 scale per graha)."""

    planet_id: int
    sthana: float
    dig: float
    kala: float
    cheshta: float
    naisargika: float
    drik: float
    total: float


# Natural strength order (Sun strongest day, etc.) — simplified
NAISARGIKA = {0: 60, 1: 51, 4: 34, 2: 26, 5: 43, 3: 50, 6: 39}

# Ashtakavarga benefic points (transits) — simplified bindu for Sun in sign 0-11
# Full SARVA would be 337; here per-sign contribution stub
ASHTAKAVARGA_BENEFIC = {
    0: (1, 2, 4, 7, 8, 9, 11),
    1: (2, 3, 5, 6, 9, 10, 11),
}


def sthana_bala(planet_id: int, sign: int, house: int, lagna_sign: int) -> float:
    """Positional strength stub."""
    score = 30.0
    if EXALTATION_SIGN.get(planet_id) == sign:
        score += 40
    elif DEBILITATION_SIGN.get(planet_id) == sign:
        score -= 30
    if RASHI_LORDS[sign] == planet_id:
        score += 25
    if house in (1, 4, 7, 10):
        score += 15
    elif house in (5, 9):
        score += 10
    elif house in (6, 8, 12):
        score -= 15
    return max(0.0, min(100.0, score))


def dig_bala(planet_id: int, house: int) -> float:
    """Directional strength (Jupiter/Mercury east, etc.)."""
    strong_houses = {
        0: (10,), 1: (4,), 2: (1,), 3: (4,), 4: (10,),
        5: (1,), 6: (7,),
    }
    if house in strong_houses.get(planet_id, ()):
        return 60.0
    return 30.0


def shadbala_for_graha(
    planet_id: int,
    sign: int,
    house: int,
    lagna_sign: int,
    retrograde: bool,
) -> ShadbalaScore:
    """Approximate Shadbala components."""
    sthana = sthana_bala(planet_id, sign, house, lagna_sign)
    dig = dig_bala(planet_id, house)
    kala = 40.0
    cheshta = 25.0 if retrograde else 45.0
    nais = float(NAISARGIKA.get(planet_id, 30))
    drik = 35.0
    total = (sthana + dig + kala + cheshta + nais + drik) / 6.0
    return ShadbalaScore(
        planet_id=planet_id,
        sthana=sthana,
        dig=dig,
        kala=kala,
        cheshta=cheshta,
        naisargika=nais,
        drik=drik,
        total=total,
    )


def sarvashtakavarga_total(bindus: list[int]) -> int:
    """Sum of bindus (0-8 per sign) across 12 signs."""
    return sum(bindus)


def compute_ashtakavarga_stub(lagna_sign: int, planet_signs: dict[int, int]) -> dict[int, list[int]]:
    """Simplified bindu: 4 points if planet in kendra from lagna, else 2."""
    result: dict[int, list[int]] = {}
    for pid, psign in planet_signs.items():
        if pid > 6:
            continue
        row = []
        for s in range(12):
            h = whole_sign_house(s, lagna_sign)
            row.append(4 if h in (1, 4, 7, 10) else 2)
        result[pid] = row
    return result
