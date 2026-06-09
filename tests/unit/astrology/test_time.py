# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for time helpers on AstrologyInstance (no main window)."""
import datetime

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(scope='module')
def astrology_class():
    from astrology_app.chart import AstrologyInstance
    return AstrologyInstance


@pytest.fixture
def oa(astrology_class):
    """Bare instance without running __init__ (avoids DB/GTK bootstrap)."""
    return astrology_class.__new__(astrology_class)


def test_dec_hour(oa):
    assert oa.decHour(3.5) == [3, 30, 0]
    assert oa.decHour(0.0) == [0, 0, 0]


def test_dec_hour_join_roundtrip(oa):
    assert oa.decHourJoin(3, 30, 0) == 3.5
    assert oa.decHourJoin(0, 0, 0) == 0.0


def test_offset_to_tz(oa):
    assert oa.offsetToTz(datetime.timedelta(hours=1)) == 1.0
    assert oa.offsetToTz(datetime.timedelta(hours=-5, minutes=-30)) == -5.5
