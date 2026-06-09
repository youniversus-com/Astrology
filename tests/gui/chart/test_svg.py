# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Chart/SVG integration tests (GTK application context)."""
import os

import pytest

pytestmark = pytest.mark.gui


def test_make_svg(astrology_module, app_context):
    mod, app, win = app_context
    path = mod.astrology_chart.makeSVG()
    assert path
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 100


def test_chart_types(astrology_module, app_context):
    mod, app, win = app_context
    oa = mod.astrology_chart
    oa.makeSVG()
    win.specialRadix(None)
    assert oa.type == 'Radix'
    assert oa.transit is False
    oa.makeSVG()
    win.specialTransit(None)
    assert oa.type == 'Transit'
    svg = oa.makeSVG()
    assert os.path.isfile(svg)
    assert os.path.getsize(svg) > 100


def test_zoom_levels(astrology_module, app_context):
    mod, app, win = app_context
    for idx in (0, 1, 2, 3):
        win.set_zoom_from_menu(idx)
    assert mod.astrology_chart.zoom in (0.8, 1.0, 1.5, 2.0)

