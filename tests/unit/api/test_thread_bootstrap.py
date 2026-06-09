# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""API bootstrap must work from worker threads (FastAPI thread pool)."""

import threading

import pytest

pytestmark = pytest.mark.unit


def test_ensure_bootstrapped_from_worker_thread(astrology_db):
    from astrology_api.bootstrap import api_context

    errors: list[str] = []

    def worker() -> None:
        try:
            with api_context() as (_, database, _):
                database.getLabel()
                database.getDatabase()
        except Exception as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, errors
