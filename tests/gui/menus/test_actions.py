# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise main window menu actions and dialogs (GTK 4)."""
import pytest

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk

pytestmark = pytest.mark.gui


def _pump(ms=80):
    ctx = GLib.MainContext.default()
    import time
    end = time.time() + ms / 1000.0
    while time.time() < end:
        while ctx.pending():
            ctx.iteration(False)


# All menu-driven handlers on AstrologyMainWindow (widget arg ignored).
MENU_ACTIONS = [
    'eventDataNew',
    'doImport',
    'doExport',
    'aboutInfo',
    'openDatabase',
    'openDatabaseFamous',
    'settingsPlanets',
    'settingsAspects',
    'settingsColors',
    'settingsLabel',
    'settingsLocation',
    'settingsConfiguration',
    'specialRadix',
    'specialTransit',
    'specialSolar',
    'specialSecondaryProgression',
    'tableMonthlyTimeline',
    'tableCuspAspects',
    'extraExportDB',
    'extraImportDB',
    'set_zoom_from_menu',
]


@pytest.mark.parametrize('method_name', MENU_ACTIONS)
def test_menu_handler_no_crash(method_name, app_context):
    mod, app, win = app_context
    win.iconn = True
    handler = getattr(win, method_name)
    if method_name == 'set_zoom_from_menu':
        handler(1)
    else:
        handler(None)
    _pump(150)
    _close_extra_windows(win)


def test_chart_type_actions(app_context):
    mod, app, win = app_context
    win.iconn = True
    win.specialRadix(None)
    _pump(50)
    win.specialTransit(None)
    _pump(50)
    win.specialSolar(None)
    _pump(100)
    if hasattr(win, 'win_SS') and win.win_SS:
        win.win_SS.close()
    _pump(50)
    win.specialSecondaryProgression(None)
    _pump(100)
    if hasattr(win, 'win_SSP') and win.win_SSP:
        win.win_SSP.close()
    _pump(50)


def test_event_editor_flow(app_context):
    mod, app, win = app_context
    win.iconn = True
    win.eventData(None)
    _pump(200)
    assert win.window2.get_visible()
    win.eventDataApply(None)
    _pump(100)
    win.window2.close()
    _pump(50)


def test_update_ui_twice(app_context):
    """Regression: duplicate GAction registration."""
    mod, app, win = app_context
    win.updateUI()
    _pump(50)
    win.updateUI()
    _pump(50)


def test_import_export_dialogs(app_context):
    mod, app, win = app_context
    for fn in (win.doImport, win.doExport, win.extraExportDB, win.extraImportDB):
        fn(None)
        _pump(80)


def _close_extra_windows(win):
    for attr in dir(win):
        if not attr.startswith('win_') and attr != 'window' and attr != 'window2':
            continue
        if not attr.startswith('win_'):
            continue
        w = getattr(win, attr, None)
        if w is None:
            continue
        try:
            if isinstance(w, Gtk.Window) and w.get_visible():
                w.close()
        except Exception:
            pass
    if getattr(win, 'window2', None):
        try:
            if win.window2.get_visible():
                win.window2.close()
        except Exception:
            pass
    _pump(40)
