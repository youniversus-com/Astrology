# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Property-based tests for time conversion helpers."""
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

hypothesis = pytest.importorskip('hypothesis')
from hypothesis import given, strategies as st


@pytest.fixture(scope='module')
def oa_class():
    from astrology_app.chart import AstrologyInstance
    return AstrologyInstance


@given(st.floats(min_value=0.0, max_value=23.999, allow_nan=False, allow_infinity=False))
def test_dec_hour_join_roundtrip(oa_class, value):
    inst = oa_class.__new__(oa_class)
    h, m, s = inst.decHour(value)
    back = inst.decHourJoin(h, m, s)
    assert back == pytest.approx(value, abs=0.02)
