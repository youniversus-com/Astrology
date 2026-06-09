# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Load the main astrology application module."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PKG_SRC = PROJECT_ROOT / 'src'
ASTROLOGY_DIR = PKG_SRC


def sync_runtime_globals(mod):
    """Mirror module-level singletons onto ``astrology_app.globals``."""
    import astrology_app.globals as g

    for name in ('cfg', 'db', 'astrology_chart', 'mainwin'):
        value = getattr(mod, name, None)
        if value is not None:
            setattr(g, name, value)
            setattr(mod, name, value)


def load_astrology_module():
    if str(ASTROLOGY_DIR) not in sys.path:
        sys.path.insert(0, str(ASTROLOGY_DIR))
    import astrology_app.application as application

    return application
