# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Vedic yoga rule engine (JSON-driven + built-in rules)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from astrologymod.vedic.constants import EXALTATION_SIGN, LORD_LABELS
from astrologymod.vedic.drishti import has_drishti
from astrologymod.vedic.rashi import whole_sign_house
from astrologymod.swiss import sign_index


@dataclass(frozen=True)
class YogaHit:
    """Detected yoga."""

    yoga_id: str
    name: str
    description: str
    strength: float


def _yogas_json_path() -> Path:
    from astrologymod import install_paths
    found = install_paths.find_data_file('vedic/yogas.json')
    if found is not None:
        return Path(found)
    return Path(__file__).resolve().parents[2] / 'data' / 'vedic' / 'yogas.json'


def load_yoga_rules() -> list[dict[str, Any]]:
    """Load optional JSON yoga definitions."""
    path = _yogas_json_path()
    if not path.is_file():
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('yogas', [])


def _planet_signs(snapshot: Any) -> dict[int, int]:
    return {g.index: g.rashi.index for g in snapshot.grahas}


def _gaja_kesari(snapshot: Any) -> YogaHit | None:
    """Jupiter in kendra from Moon."""
    signs = _planet_signs(snapshot)
    moon_s = signs.get(1)
    jup_s = signs.get(5)
    if moon_s is None or jup_s is None:
        return None
    diff = (jup_s - moon_s) % 12
    if diff in (0, 3, 6, 9):
        return YogaHit('gaja_kesari', 'Gaja Kesari', 'Jupiter in kendra from Moon', 0.8)
    return None


def _pancha_mahapurusha(snapshot: Any) -> list[YogaHit]:
    hits: list[YogaHit] = []
    names = {
        4: ('Ruchaka', 'Mars'),
        3: ('Bhadra', 'Mercury'),
        0: ('Sasha', 'Saturn'),
        5: ('Hamsa', 'Jupiter'),
        2: ('Malavya', 'Venus'),
    }
    for g in snapshot.grahas:
        if g.index not in names:
            continue
        yname, plabel = names[g.index]
        if g.rashi.index in (0, 3, 6, 9) and g.rashi.degree_in_sign >= 0:
            if EXALTATION_SIGN.get(g.index) == g.rashi.index or g.rashi.index in (0, 3, 6, 9):
                hits.append(YogaHit(
                    f'mahapurusha_{g.index}',
                    f'Pancha Mahapurusha ({yname})',
                    f'{plabel} in kendra in own or exaltation sign',
                    0.7,
                ))
    return hits


def _eval_json_rule(rule: dict[str, Any], snapshot: Any) -> YogaHit | None:
    """Evaluate simple JSON conditions."""
    conds = rule.get('conditions', [])
    signs = _planet_signs(snapshot)
    lagna = snapshot.lagna_sign
    for c in conds:
        ctype = c.get('type')
        if ctype == 'planet_in_house':
            pid = c['planet']
            house = c['house']
            ps = signs.get(pid)
            if ps is None:
                return None
            if whole_sign_house(ps, lagna) != house:
                return None
        elif ctype == 'planet_in_sign':
            if signs.get(c['planet']) != c['sign']:
                return None
        elif ctype == 'planet_same_sign_as':
            base = signs.get(c['planet'])
            other = signs.get(c['other'])
            if base is None or other is None or base != other:
                return None
        elif ctype == 'lagna_lord_in_house':
            from astrologymod.vedic.constants import RASHI_LORDS
            lord = RASHI_LORDS[lagna]
            ps = signs.get(lord)
            if ps is None or whole_sign_house(ps, lagna) != c['house']:
                return None
        elif ctype == 'kendra_lord_in_kendra':
            from astrologymod.vedic.constants import RASHI_LORDS
            kendra_signs = {(lagna + o) % 12 for o in (0, 3, 6, 9)}
            placed = 0
            for h in (1, 4, 7, 10):
                sign = (lagna + h - 1) % 12
                lord = RASHI_LORDS[sign]
                if signs.get(lord) in kendra_signs:
                    placed += 1
            if placed < 2:
                return None
    return YogaHit(
        rule['id'],
        rule.get('name', rule['id']),
        rule.get('description', ''),
        float(rule.get('strength', 0.5)),
    )


def evaluate_yogas(snapshot: Any) -> list[YogaHit]:
    """Run built-in and JSON yoga rules."""
    hits: list[YogaHit] = []
    gk = _gaja_kesari(snapshot)
    if gk:
        hits.append(gk)
    hits.extend(_pancha_mahapurusha(snapshot))

    for g in snapshot.grahas:
        if g.index == 5 and g.rashi.index == snapshot.lagna_sign:
            hits.append(YogaHit('lagna_jupiter', 'Lagna Jupiter', 'Jupiter in ascendant sign', 0.6))

    signs = _planet_signs(snapshot)
    if signs.get(0) == signs.get(1):
        hits.append(YogaHit('sun_moon_conj', 'Sun-Moon conjunction', 'New Moon yoga', 0.4))

    for rule in load_yoga_rules():
        hit = _eval_json_rule(rule, snapshot)
        if hit:
            hits.append(hit)

    return hits
