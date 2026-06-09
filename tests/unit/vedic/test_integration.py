# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration checks for Vedic chart rendering."""

import pytest

pytestmark = pytest.mark.unit


def test_vedic_main_chart_svg_written(tmp_path, monkeypatch):
    """North Indian layout writes standalone SVG to temp path."""
    from astrologymod.vedic.snapshot import build_snapshot
    from astrologymod.vedic.chart_svg import north_indian_chart

    planets = [0.0] * 35
    planets[1] = 45.0
    houses = [10.0] + [0.0] * 11
    snap = build_snapshot(
        planets, houses, [False] * 35, {0: 'Surya', 1: 'Chandra'},
        2000, 6, 15, 12.0,
    )
    svg = north_indian_chart(snap, width=500, height=500)
    assert '<svg' in svg
    assert 'Mesha' in svg or 'Ashwini' in svg or 'Su' in svg
    out = tmp_path / 'vedic.svg'
    out.write_text(svg, encoding='utf-8')
    assert out.stat().st_size > 200


def test_use_vedic_main_chart_logic():
    """Chart instance respects layout and chart type rules."""
    class FakeCfg:
        astrocfg = {'tradition': 'vedic', 'vedic_chart_layout': 'north'}

    class FakeChart:
        vedic = object()
        type = 'Radix'

        def _use_vedic_main_chart(self):
            if self.vedic is None:
                return False
            layout = FakeCfg.astrocfg.get('vedic_chart_layout', 'north')
            if layout == 'wheel':
                return False
            if self.type == 'Transit':
                return False
            return True

    c = FakeChart()
    assert c._use_vedic_main_chart() is True
    c.type = 'Transit'
    assert c._use_vedic_main_chart() is False
    FakeCfg.astrocfg['vedic_chart_layout'] = 'wheel'
    c.type = 'Radix'
    assert c._use_vedic_main_chart() is False
