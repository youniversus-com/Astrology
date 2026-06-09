# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate and verify documentation screenshots (headless GTK + Xvfb)."""

import pytest

from helpers.screenshot import (
    assert_png,
    prepare_dialog_screenshot,
    pump_main_loop,
    save_chart_svg_as_png,
    save_widget_as_png,
)
from gui.screenshots.chart_data import apply_fixed_chart

pytestmark = [pytest.mark.gui, pytest.mark.screenshot]

DOC_IMAGES = (
    'natal-wheel-default.png',
    'transit-view.png',
    'main-window.png',
    'event-editor.png',
    'settings-planets.png',
)


def test_capture_documentation_screenshots(app_context, screenshot_dir, update_screenshots):
    """Regenerate all PNGs under docs/screenshots/ (``make update-screenshots``)."""
    if not update_screenshots:
        pytest.skip('Pass --update-screenshots to regenerate documentation PNGs')

    mod, app, win = app_context
    apply_fixed_chart(mod)

    natal_svg = mod.astrology_chart.makeSVG()
    save_chart_svg_as_png(natal_svg, str(screenshot_dir / 'natal-wheel-default.png'))

    win.specialTransit(None)
    pump_main_loop(150)
    transit_svg = mod.astrology_chart.makeSVG()
    save_chart_svg_as_png(transit_svg, str(screenshot_dir / 'transit-view.png'))

    win.specialRadix(None)
    pump_main_loop(100)
    apply_fixed_chart(mod)
    mod.astrology_chart.makeSVG()
    win.updateUI()
    # Xvfb has no window manager; maximize() does not expand the main window.
    win.window.unmaximize()
    win.window.set_default_size(1280, 720)
    win.window.set_size_request(1280, 720)
    win.window.queue_resize()
    pump_main_loop(250)
    save_widget_as_png(win.window, str(screenshot_dir / 'main-window.png'))

    win.eventData(None)
    prepare_dialog_screenshot(win.window2)
    save_widget_as_png(win.window2, str(screenshot_dir / 'event-editor.png'))
    win.window2.close()
    pump_main_loop(50)

    win.settingsPlanets(None)
    prepare_dialog_screenshot(win.win_SP)
    save_widget_as_png(win.win_SP, str(screenshot_dir / 'settings-planets.png'))
    win.win_SP.close()
    pump_main_loop(50)

    for name in DOC_IMAGES:
        assert_png(screenshot_dir / name)


@pytest.mark.parametrize('filename', DOC_IMAGES)
def test_documentation_screenshots_exist(filename, screenshot_dir):
    """Committed documentation PNGs must be present (docs CI gate)."""
    assert_png(screenshot_dir / filename)
