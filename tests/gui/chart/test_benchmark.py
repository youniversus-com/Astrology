# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional performance smoke for chart generation (advisory, not a hard gate)."""
import pytest

pytestmark = [pytest.mark.gui, pytest.mark.slow]

pytest_benchmark = pytest.importorskip('pytest_benchmark')


def test_make_svg_benchmark(benchmark, app_context):
    mod, app, win = app_context

    def run():
        return mod.astrology_chart.makeSVG()

    path = benchmark(run)
    assert path
