# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Initialize astrology singletons without starting the GTK application."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import astrology_app.globals as g

if TYPE_CHECKING:
    from astrology_app.chart import AstrologyInstance
    from astrology_app.config import AstrologyCfg
    from astrology_app.db import AstrologySqlite

# FastAPI runs sync endpoints in a thread pool. SQLite connections are per-thread,
# while astrology_app uses module globals — serialize requests and bind per-thread state.
_thread_local = threading.local()
_api_lock = threading.Lock()


def _session() -> tuple[AstrologyCfg, AstrologySqlite, AstrologyInstance]:
    """Return this worker thread's cfg/db/chart (caller must hold ``_api_lock``)."""
    if not getattr(_thread_local, 'ready', False):
        from astrology_app.chart import AstrologyInstance
        from astrology_app.config import AstrologyCfg
        from astrology_app.db import AstrologySqlite

        configuration = AstrologyCfg()
        g.cfg = configuration
        g.ctx.cfg = configuration

        database = AstrologySqlite()
        g.db = database
        g.ctx.db = database

        chart = AstrologyInstance()
        g.astrology_chart = chart
        g.ctx.astrology_chart = chart
        g.bind_context(configuration, database, chart, None)

        _thread_local.cfg = configuration
        _thread_local.db = database
        _thread_local.chart = chart
        _thread_local.ready = True

    g.bind_context(
        _thread_local.cfg, _thread_local.db, _thread_local.chart, None,
    )
    return _thread_local.cfg, _thread_local.db, _thread_local.chart


@contextmanager
def api_context() -> Iterator[tuple[AstrologyCfg, AstrologySqlite, AstrologyInstance]]:
    """Bind this thread's astrology state for one API operation."""
    with _api_lock:
        yield _session()


def ensure_bootstrapped() -> tuple[AstrologyCfg, AstrologySqlite, AstrologyInstance]:
    """Compatibility helper; prefer :func:`api_context` for full request scope."""
    with _api_lock:
        return _session()


def gtk_available() -> bool:
    """Return True when PyGObject GTK imports succeed."""
    try:
        from gi import require_version

        require_version('Gtk', '4.0')
        from gi.repository import Gtk  # noqa: F401

        return True
    except Exception:
        return False
