# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Runtime singletons set during GTK application activation."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AppContext:
    """Typed container for live application singletons."""

    cfg: Any = None
    db: Any = None
    astrology_chart: Any = None
    mainwin: Any = None


ctx = AppContext()

# Legacy module-level aliases (prefer ``ctx`` in new code).
cfg = None
db = None
astrology_chart = None
mainwin = None


def bind_context(configuration, database, chart, window=None) -> AppContext:
    """Assign singletons on both ``ctx`` and legacy module globals."""
    global cfg, db, astrology_chart, mainwin
    ctx.cfg = configuration
    ctx.db = database
    ctx.astrology_chart = chart
    ctx.mainwin = window
    cfg = configuration
    db = database
    astrology_chart = chart
    mainwin = window
    return ctx
