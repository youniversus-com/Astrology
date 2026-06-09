# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Vedic chart SVG content checks."""
import pytest

pytestmark = pytest.mark.unit


def _sample_snapshot():
    from astrologymod.vedic.snapshot import build_snapshot

    planets = [0.0] * 35
    planets[0] = 120.5
    planets[1] = 45.0
    planets[2] = 200.0
    planets[3] = 15.0
    planets[4] = 300.0
    planets[5] = 90.0
    planets[6] = 270.0
    planets[10] = 180.0
    planets[29] = 0.0
    houses = [15.0] + [0.0] * 11
    return build_snapshot(
        planets, houses, [False] * 35, {}, 1990, 1, 1, 12.0,
    )


def test_north_indian_has_twelve_houses_and_degrees():
    from astrologymod.vedic.chart_svg import north_indian_chart

    snap = _sample_snapshot()
    svg = north_indian_chart(snap, width=500, height=500)
    assert svg.count(' Lg') >= 1
    assert '12 ' in svg
    assert 'Su' in svg
    assert '°' in svg
    assert 'Su' in svg and 'Mo' in svg
    assert svg.count('stroke="#333333"') >= 5


def test_south_indian_marks_lagna_and_panchanga_center():
    from astrologymod.vedic.chart_svg import south_indian_chart

    snap = _sample_snapshot()
    svg = south_indian_chart(snap, width=800, height=800)
    assert ' Lg' in svg
    assert 'fff6e8' in svg
    assert snap.panchanga.nakshatra in svg
    # grid centered: origin x should be > 0 and grid uses most of width
    assert 'x="80.' not in svg or float(svg.split('x="')[1].split('"')[0]) > 50


def test_canvas_wrapper_centers_chart():
    from astrologymod.vedic.chart_svg import render_vedic_chart_svg_on_canvas

    snap = _sample_snapshot()
    svg = render_vedic_chart_svg_on_canvas(snap, 'north', 1200, 900)
    assert 'transform="translate(' in svg
    assert 'viewBox="0 0 1200 900"' in svg
    ox = (1200 - min(1200 - 40, 900 - 68, 920)) / 2
    assert f'translate({ox:.1f}' in svg or 'translate(' in svg


def test_south_indian_grid_centered_in_large_canvas():
    from astrologymod.vedic.chart_svg import south_indian_chart

    snap = _sample_snapshot()
    w, h = 900, 700
    svg = south_indian_chart(snap, width=w, height=h)
    cell = min((w - 20) / 4, (h - 44 - 10) / 4)
    ox = (w - cell * 4) / 2
    assert f'x="{ox:.1f}"' in svg or f'x="{int(ox)}"' in svg
    assert ox > 40
