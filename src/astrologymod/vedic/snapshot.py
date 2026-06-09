# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Aggregate Vedic chart snapshot from ephemeris output."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from astrologymod.swiss import sign_index
from astrologymod.vedic.constants import DEFAULT_GRAHA_INDICES, VARGA_CODES
from astrologymod.vedic.graha import is_combust, vedic_label
from astrologymod.vedic.muhurta import MuhurtaSlot, scan_day_slots
from astrologymod.vedic.drishti import has_drishti
from astrologymod.vedic.dashas import (
    DashaPeriod,
    ashtottari_dasha,
    vimshottari_antardasha,
    vimshottari_mahadasha,
    yogini_dasha,
)
from astrologymod.vedic.drishti import drishti_target_signs
from astrologymod.vedic.nakshatra import nakshatra_info
from astrologymod.vedic.panchanga import Panchanga, compute_panchanga
from astrologymod.vedic.rashi import RashiInfo, rashi_info, whole_sign_house
from astrologymod.vedic.strength import compute_ashtakavarga_stub, shadbala_for_graha
from astrologymod.vedic.vargas import all_vargas, varga_longitude
from astrologymod.vedic.yogas import YogaHit, evaluate_yogas


@dataclass
class GrahaPlacement:
    """One graha in the natal Vedic snapshot."""

    index: int
    label: str
    longitude: float
    rashi: RashiInfo
    nakshatra: Any
    house: int
    retrograde: bool
    combust: bool = False
    vargas: dict[str, float] = field(default_factory=dict)
    drishti_to: set[int] = field(default_factory=set)
    drishti_from: list[str] = field(default_factory=list)


@dataclass
class VedicChartSnapshot:
    """Full Jyotish analysis for one chart moment."""

    lagna_longitude: float
    lagna_sign: int
    lagna_rashi: RashiInfo
    grahas: list[GrahaPlacement]
    panchanga: Panchanga
    vimshottari: list[DashaPeriod]
    vimshottari_antar: list[DashaPeriod]
    yogini: list[DashaPeriod]
    ashtottari: list[DashaPeriod]
    yogas: list[YogaHit]
    shadbala: list[Any]
    ashtakavarga: dict[int, list[int]]
    varga_chart: dict[str, dict[int, float]]
    dasha_system: str = 'vimshottari'
    primary_dasha: list[DashaPeriod] = field(default_factory=list)
    muhurta_slots: list[MuhurtaSlot] = field(default_factory=list)
    ayanamsa_mode: str = 'LAHIRI'


def _birth_datetime(
    year: int, month: int, day: int, hour: float,
) -> datetime.datetime:
    """Convert decimal UTC hour to a naive datetime (handles second rollover)."""
    base = datetime.datetime(year, month, day)
    return base + datetime.timedelta(seconds=hour * 3600.0)


def build_snapshot(
    planets_degree_ut: Sequence[float],
    houses_degree_ut: Sequence[float],
    planets_retrograde: Sequence[bool],
    planet_labels: Mapping[int, str],
    year: int,
    month: int,
    day: int,
    hour: float,
    graha_indices: Sequence[int] | None = None,
    dasha_system: str = 'vimshottari',
    geolon: float | None = None,
    geolat: float | None = None,
    altitude: float = 0.0,
    ayanamsa_mode: str = 'LAHIRI',
    varga_display: str = 'D1,D9,D10',
) -> VedicChartSnapshot:
    """Build Vedic snapshot from ``ephData`` arrays."""
    indices = tuple(graha_indices or DEFAULT_GRAHA_INDICES)
    asc = float(houses_degree_ut[0])
    lagna_sign = sign_index(asc)
    lagna_rashi = rashi_info(asc)
    birth = _birth_datetime(year, month, day, hour)

    grahas: list[GrahaPlacement] = []
    planet_signs: dict[int, int] = {}

    sun_lon = float(planets_degree_ut[0])

    for i in indices:
        if i >= len(planets_degree_ut):
            continue
        lon = float(planets_degree_ut[i])
        ri = rashi_info(lon)
        nk = nakshatra_info(lon)
        house = whole_sign_house(ri.index, lagna_sign)
        retro = bool(planets_retrograde[i]) if i < len(planets_retrograde) else False
        planet_signs[i] = ri.index
        drishti = drishti_target_signs(i, ri.index) if i <= 6 else set()
        grahas.append(GrahaPlacement(
            index=i,
            label=vedic_label(i, planet_labels.get(i, str(i))),
            longitude=lon,
            rashi=ri,
            nakshatra=nk,
            house=house,
            retrograde=retro,
            combust=is_combust(i, lon, sun_lon),
            vargas=all_vargas(lon),
            drishti_to=drishti,
        ))

    moon_lon = float(planets_degree_ut[1])

    for g in grahas:
        received: list[str] = []
        for other in grahas:
            if other.index > 6 and other.index not in (10, 29):
                continue
            if other.index == g.index:
                continue
            if has_drishti(other.index, other.rashi.index, g.rashi.index):
                received.append(other.label)
        g.drishti_from = received
    pan = compute_panchanga(sun_lon, moon_lon, birth)

    vim = vimshottari_mahadasha(moon_lon, birth)
    antar: list[DashaPeriod] = []
    if vim:
        antar = vimshottari_antardasha(vim[0], moon_lon)

    varga_chart: dict[str, dict[int, float]] = {}
    for code in VARGA_CODES:
        varga_chart[code] = {}
        for g in grahas:
            if code == 'D1':
                varga_chart[code][g.index] = g.longitude
            else:
                varga_chart[code][g.index] = varga_longitude(g.longitude, code)

    shadbala = [
        shadbala_for_graha(g.index, g.rashi.index, g.house, lagna_sign, g.retrograde)
        for g in grahas if g.index <= 6
    ]
    av = compute_ashtakavarga_stub(lagna_sign, planet_signs)

    yogini = yogini_dasha(moon_lon, birth)
    ashtottari = ashtottari_dasha(moon_lon, birth)
    primary = vim
    if dasha_system == 'yogini':
        primary = yogini
    elif dasha_system == 'ashtottari':
        primary = ashtottari

    muhurta = scan_day_slots(
        sun_lon, moon_lon, birth.date(),
        geolon=geolon, geolat=geolat, altitude=altitude,
    )

    snap = VedicChartSnapshot(
        lagna_longitude=asc,
        lagna_sign=lagna_sign,
        lagna_rashi=lagna_rashi,
        grahas=grahas,
        panchanga=pan,
        vimshottari=vim,
        vimshottari_antar=antar,
        yogini=yogini,
        ashtottari=ashtottari,
        yogas=[],
        shadbala=shadbala,
        ashtakavarga=av,
        varga_chart=varga_chart,
        dasha_system=dasha_system,
        primary_dasha=primary,
        muhurta_slots=muhurta,
        ayanamsa_mode=ayanamsa_mode,
    )
    snap.yogas = evaluate_yogas(snap)
    return snap
