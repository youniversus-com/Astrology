# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Chart SVG generation via the existing AstrologyInstance (GTK required)."""

from __future__ import annotations

import os
from typing import Any

import astrology_app.globals as g

from astrology_api.bootstrap import gtk_available
from astrology_api.schemas import ChartEvent, ChartRequest
from astrology_api.services.ephemeris_service import compute_vedic


def _apply_event(chart: Any, event: ChartEvent) -> None:
    chart.name = event.name
    chart.year = event.year
    chart.month = event.month
    chart.day = event.day
    chart.hour = event.hour
    chart.geolat = event.geolat
    chart.geolon = event.geolon
    chart.altitude = event.altitude
    chart.location = event.location
    chart.timezone = event.timezone
    chart.timezonestr = event.timezonestr
    chart.countrycode = event.countrycode


def _apply_transit(chart: Any, event: ChartEvent) -> None:
    chart.t_year = event.year
    chart.t_month = event.month
    chart.t_day = event.day
    chart.t_hour = event.hour
    chart.t_geolat = event.geolat
    chart.t_geolon = event.geolon
    chart.t_altitude = event.altitude
    chart.transit = True


def generate_chart_svg(request: ChartRequest) -> dict[str, Any]:
    """Return wheel SVG (and optional table SVG) for a chart request."""
    if request.tradition == 'vedic':
        from astrology_api.schemas import VedicRequest

        labels = g.db.getLabel()
        planet_labels = {i: labels.get(f'planet_{i}', str(i)) for i in range(35)}
        snapshot, svg = compute_vedic(
            VedicRequest(
                event=request.event,
                layout=request.vedic_layout,
                varga=request.vedic_varga,
                width=request.width,
                height=request.height,
            ),
            dict(g.db.astrocfg),
            g.db.getSettingsPlanet(),
            planet_labels,
        )
        return {
            'svg': svg,
            'table_svg': None,
            'chart_type': request.chart_type,
            'tradition': 'vedic',
            'meta': {'vedic': snapshot},
        }

    if not gtk_available():
        raise RuntimeError(
            'Western chart SVG requires GTK 4 (PyGObject). '
            'Use tradition=vedic or /api/chart/data for JSON ephemeris.',
        )

    chart = g.astrology_chart
    _apply_event(chart, request.event)
    chart.type = request.chart_type
    chart.transit = request.chart_type == 'Transit'
    if request.chart_type == 'Transit' and request.transit_event:
        _apply_transit(chart, request.transit_event)
    chart.set_chart_viewport(request.width, request.height)

    wheel_path = chart.makeSVG()
    with open(wheel_path, encoding='utf-8') as f:
        wheel_svg = f.read()

    table_svg = None
    if request.include_table:
        table_path = g.cfg.tempfilenametable
        if os.path.isfile(table_path):
            with open(table_path, encoding='utf-8') as f:
                table_svg = f.read()

    return {
        'svg': wheel_svg,
        'table_svg': table_svg,
        'chart_type': chart.type,
        'tradition': 'western',
        'meta': {
            'location': chart.location,
            'name': chart.name,
            'lunar_phase': chart.lunar_phase,
        },
    }
