# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK application entry, bootstrap, and main loop.

Provides :class:`AstrologyApplication` and the ``main()`` entry point used by
the ``astrology`` console script. On activation the application constructs
configuration, SQLite databases, chart state, and the primary window once.
"""

import sys
import warnings

from gi import require_version

require_version('Gtk', '4.0')
from gi.repository import Gtk

from astrologymod import gtkcompat as g4

from astrologymod.branding import APP_ID
from astrologymod.package_check import warn_if_shadowed

import astrology_app.globals as g
from astrology_app.chart import AstrologyInstance
from astrology_app.config import AstrologyCfg
from astrology_app.constants import DEBUG, VERSION
from astrology_app.db import AstrologySqlite
from astrology_app.debug import dprint
from astrology_app.i18n import LANGUAGES, LANGUAGES_LABEL, TRANSLATION
from astrology_app.paths import APP_DIR, DATADIR
from astrology_app.ui.main_window import AstrologyMainWindow

# Re-export module-level names used by tests and legacy imports.
cfg = g.cfg
db = g.db
astrology_chart = g.astrology_chart
mainwin = g.mainwin


class AstrologyApplication(Gtk.Application):
    """GTK application shell; builds cfg/db/astrology_chart/mainwin on activate."""

    def __init__(self, application_id=APP_ID):
        super().__init__(application_id=application_id)

    def do_activate(self):
        """Initialize singletons and show the main window (once per app)."""
        global cfg, db, astrology_chart, mainwin
        try:
            if not hasattr(self, '_win'):
                configuration = AstrologyCfg()
                # cfg must exist before db/chart __init__ (they read g.cfg / g.db).
                g.cfg = configuration
                g.ctx.cfg = configuration
                database = AstrologySqlite()
                g.db = database
                g.ctx.db = database
                chart = AstrologyInstance()
                g.astrology_chart = chart
                g.ctx.astrology_chart = chart
                self._win = AstrologyMainWindow(application=self)
                g.bind_context(configuration, database, chart, self._win)
                cfg = g.cfg
                db = g.db
                astrology_chart = g.astrology_chart
                mainwin = g.mainwin
            self._win.window.present()
        except Exception:
            import traceback
            traceback.print_exc()
            dlg = Gtk.AlertDialog(
                message='Astrology failed to start',
                detail=traceback.format_exc(),
            )
            parent = None
            if hasattr(self, '_win') and getattr(self._win, 'window', None):
                parent = self._win.window
            dlg.show(parent)
            raise


def main():
    """Create the GTK application and enter the main loop."""
    warn_if_shadowed()
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    if g4.ensure_display() is None:
        print(
            'Astrology needs a graphical session.\n'
            '  - Log in to your desktop (not plain SSH), or\n'
            '  - Set DISPLAY (e.g. export DISPLAY=:0), or\n'
            '  - For headless testing: sudo apt install xvfb && xvfb-run -a astrology',
            file=sys.stderr,
        )
        return 1
    try:
        app = AstrologyApplication()
        status = app.run(sys.argv)
    except Exception:
        import traceback
        traceback.print_exc()
        return 1
    return status if isinstance(status, int) else 0
