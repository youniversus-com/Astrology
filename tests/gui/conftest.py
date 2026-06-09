# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK / headless display fixtures for GUI integration tests."""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers.ephemeris import ensure_bundled_ephemeris  # noqa: E402
from helpers.loader import load_astrology_module, sync_runtime_globals  # noqa: E402

_APP_ID_COUNTER = 0


@pytest.fixture(scope='session')
def xvfb_display():
    """Ensure Xvfb display :99 is available for headless GTK tests."""
    display_num = ':99'
    os.environ['DISPLAY'] = display_num
    proc = None
    try:
        from gi import require_version
        require_version('Gdk', '4.0')
        from gi.repository import Gdk
        if Gdk.Display.open(display_num) is None:
            raise OSError('display not ready')
    except Exception:
        proc = subprocess.Popen(
            ['Xvfb', display_num, '-screen', '0', '1280x720x24'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.0)
    yield display_num
    if proc is not None:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture(scope='session')
def gtk_env(xvfb_display):
    os.environ.setdefault('GDK_BACKEND', 'x11')
    os.environ['ASTROLOGY_TEST'] = '1'
    from gi import require_version
    require_version('Gtk', '4.0')
    require_version('Gdk', '4.0')
    require_version('Rsvg', '2.0')
    from gi.repository import Gdk, Gtk
    display = Gdk.Display.get_default()
    if display is None:
        display = Gdk.Display.open(os.environ.get('DISPLAY', ':99'))
    if display is None:
        raise RuntimeError('GTK tests need Xvfb (sudo apt install xvfb)')
    if not Gtk.is_initialized():
        Gtk.init()
    yield


@pytest.fixture
def astrology_module(gtk_env, test_home):
    return load_astrology_module()


@pytest.fixture
def app_context(astrology_module, test_home, gtk_env):
    """Boot ``Gtk.Application`` and ``AstrologyMainWindow`` once per test."""
    from gi.repository import GLib

    ensure_bundled_ephemeris()
    mod = astrology_module

    def pump(ms=50):
        ctx = GLib.MainContext.default()
        end = time.time() + ms / 1000.0
        while time.time() < end:
            while ctx.pending():
                ctx.iteration(False)

    global _APP_ID_COUNTER
    _APP_ID_COUNTER += 1
    app = mod.AstrologyApplication(
        application_id='org.astrology.Test%d' % _APP_ID_COUNTER)
    if not app.get_is_registered():
        app.register()

    mod.cfg = mod.AstrologyCfg()
    sync_runtime_globals(mod)
    mod.db = mod.AstrologySqlite()
    sync_runtime_globals(mod)
    mod.db.setSettingsLocation(
        '52.12', '6.22', 'Amsterdam', 'NL', 'Europe/Amsterdam')
    mod.astrology_chart = mod.AstrologyInstance()
    sync_runtime_globals(mod)
    win = mod.AstrologyMainWindow(application=app)
    app._win = win
    mod.mainwin = win
    sync_runtime_globals(mod)
    win.window.present()
    pump(150)
    assert win.window.get_visible()

    yield mod, app, win

    try:
        win.window.close()
    except Exception:
        pass
    pump(50)
