# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Monthly aspect timeline table generation."""
import os

import pytest

pytestmark = pytest.mark.gui


def test_monthly_timeline_writes_svg(app_context):
    mod, app, win = app_context
    win.tMTentry = {'Y': '1990', 'M': '6'}
    win.tableMonthlyTimelineShow()
    path = mod.cfg.tempfilenametable
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 10_000
    with open(path, encoding='utf-8') as f:
        body = f.read()
    assert 'Timeline' in body
    assert '<rect' in body
