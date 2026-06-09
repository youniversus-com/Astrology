# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render generated SVG with librsvg (smoke)."""
import os

import pytest

pytestmark = pytest.mark.gui


def test_svg_renders_to_pixbuf(app_context):
    from gi.repository import Rsvg
    mod, app, win = app_context
    path = mod.astrology_chart.makeSVG()
    assert os.path.isfile(path)
    handle = Rsvg.Handle.new_from_file(path)
    pixbuf = handle.get_pixbuf()
    assert pixbuf is not None
    assert pixbuf.get_width() > 0
    assert pixbuf.get_height() > 0


def test_svg_get_dimensions(app_context):
    from gi.repository import Rsvg
    mod, app, win = app_context
    path = mod.astrology_chart.makeSVG()
    handle = Rsvg.Handle.new_from_file(path)
    dim = handle.get_dimensions()
    assert dim.width > 0 and dim.height > 0
