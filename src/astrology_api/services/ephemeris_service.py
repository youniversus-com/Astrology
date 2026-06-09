# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless ephemeris and Vedic computation (no GTK)."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from astrologymod import swiss as ephemeris
from astrologymod.vedic import build_snapshot
from astrologymod.vedic.chart_svg import render_vedic_chart_svg_on_canvas
from astrologymod.vedic.preset import effective_astrocfg

from astrology_api.schemas import ChartDataRequest, ChartEvent, VedicRequest


ZODIAC = [
    'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
]


def _event_tuple(event: ChartEvent) -> tuple[int, int, int, float, float, float, float]:
    return (
        event.year, event.month, event.day, event.hour,
        event.geolon, event.geolat, event.altitude,
    )


def _to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    if hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool)):
        return {k: _to_jsonable(v) for k, v in vars(obj).items()}
    return obj


def compute_ephemeris(
    request: ChartDataRequest,
    astrocfg: dict[str, str],
    planets_cfg: list[dict],
) -> dict[str, Any]:
    """Return ephemeris arrays for one chart (and transit overlay when requested)."""
    astro_cfg = effective_astrocfg(astrocfg)
    year, month, day, hour, geolon, geolat, alt = _event_tuple(request.event)
    module = ephemeris.ephData(
        year, month, day, hour, geolon, geolat, alt,
        planets_cfg, ZODIAC, astro_cfg,
    )
    result: dict[str, Any] = {
        'planets_sign': list(module.planets_sign),
        'planets_degree': list(module.planets_degree),
        'planets_degree_ut': list(module.planets_degree_ut),
        'planets_retrograde': list(module.planets_retrograde),
        'houses_degree_ut': list(module.houses_degree_ut),
        'houses_sign': list(module.houses_sign),
        'lunar_phase': module.lunar_phase,
        'chart_type': request.chart_type,
        'meta': {
            'location': request.event.location,
            'name': request.event.name,
        },
    }
    if request.chart_type == 'Transit' and request.transit_event:
        ty, tm, td, th, tlon, tlat, talt = _event_tuple(request.transit_event)
        transit = ephemeris.ephData(
            ty, tm, td, th, tlon, tlat, talt,
            planets_cfg, ZODIAC, astro_cfg,
        )
        result['transit'] = {
            'planets_sign': list(transit.planets_sign),
            'planets_degree': list(transit.planets_degree),
            'planets_degree_ut': list(transit.planets_degree_ut),
            'planets_retrograde': list(transit.planets_retrograde),
            'houses_degree_ut': list(transit.houses_degree_ut),
            'houses_sign': list(transit.houses_sign),
        }
    return result


def compute_vedic(
    request: VedicRequest,
    astrocfg: dict[str, str],
    planets_cfg: list[dict],
    planet_labels: dict[int, str],
) -> tuple[dict[str, Any], str]:
    """Build Vedic snapshot JSON and SVG string."""
    astro_cfg = effective_astrocfg(astrocfg)
    year, month, day, hour, geolon, geolat, alt = _event_tuple(request.event)
    module = ephemeris.ephData(
        year, month, day, hour, geolon, geolat, alt,
        planets_cfg, ZODIAC, astro_cfg,
    )
    dasha = astrocfg.get('vedic_dasha_system', 'vimshottari')
    snapshot = build_snapshot(
        module.planets_degree_ut,
        module.houses_degree_ut,
        module.planets_retrograde,
        planet_labels,
        year, month, day, hour,
        dasha_system=dasha,
        geolon=geolon,
        geolat=geolat,
        altitude=alt,
        ayanamsa_mode=astro_cfg.get('vedic_ayanamsa', 'LAHIRI'),
    )
    svg = render_vedic_chart_svg_on_canvas(
        snapshot, request.layout, request.width, request.height,
        varga=request.varga,
    )
    return _to_jsonable(snapshot), svg
