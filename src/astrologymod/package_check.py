# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Detect distro packages shadowing the development tree."""

from __future__ import annotations

import pathlib
import sys


def shadowed_astrology_app_path() -> str | None:
    """Return ``astrology_app.__file__`` if loaded from system dist-packages."""
    try:
        import astrology_app.chart as chart_mod
    except ImportError:
        return None
    path = pathlib.Path(getattr(chart_mod, '__file__', '') or '')
    if not path:
        return None
    resolved = str(path.resolve())
    if 'dist-packages' in resolved or '/usr/lib/' in resolved:
        return resolved
    return None


def warn_if_shadowed() -> None:
    """Print a stderr warning when the wrong ``astrology_app`` is on sys.path."""
    bad = shadowed_astrology_app_path()
    if bad is None:
        return
    print(
        'WARNING: astrology_app is loaded from the system package, not this project:\n'
        '  %s\n'
        '  Use: ./install.sh && source .venv/bin/activate && astrology\n'
        '  Or: sudo apt remove astrology' % bad,
        file=sys.stderr,
    )
