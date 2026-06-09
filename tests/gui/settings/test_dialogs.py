# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Open each settings dialog, interact with controls, cancel/close."""
import pytest
from gi.repository import GLib

pytestmark = pytest.mark.gui


def _pump(ms=100):
    import time
    ctx = GLib.MainContext.default()
    end = time.time() + ms / 1000.0
    while time.time() < end:
        while ctx.pending():
            ctx.iteration(False)


def _close_dialogs(win):
    for name in ('win_SC', 'win_SA', 'win_SP', 'win_SL', 'win_SS', 'win_SSP'):
        d = getattr(win, name, None)
        if d is not None:
            try:
                d.close()
            except Exception:
                pass
    _pump(50)


def test_settings_configuration(app_context):
    mod, app, win = app_context
    win.settingsConfiguration(None)
    _pump(150)
    assert hasattr(win, 'win_SC')
    _close_dialogs(win)


def test_settings_planets_aspects_colors_labels(app_context):
    mod, app, win = app_context
    for method in (
        win.settingsPlanets,
        win.settingsAspects,
        win.settingsColors,
        win.settingsLabel,
    ):
        method(None)
        _pump(120)
        _close_dialogs(win)


def test_settings_location_offline(app_context):
    mod, app, win = app_context
    win.iconn = False
    win.settingsLocation(None)
    _pump(200)
    if hasattr(win, 'win_SL'):
        win.win_SL.close()
    _pump(50)


def test_settings_location_online(app_context):
    mod, app, win = app_context
    win.iconn = True
    win.settingsLocation(None)
    _pump(150)
    if hasattr(win, 'win_SL'):
        win.win_SL.close()
    _pump(50)
