# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Golden-file tests for chart SVG output."""
import os

import pytest

from helpers.svg_normalize import normalize_svg, svg_digest

pytestmark = [pytest.mark.golden, pytest.mark.gui]

BASELINE = os.path.join(os.path.dirname(__file__), 'baselines', 'radix_amsterdam_1990.sha256')
FIXED_CHART = {
    'name': 'Golden Test',
    'year': 1990,
    'month': 6,
    'day': 15,
    'hour_h': 14,
    'hour_m': 30,
    'hour_s': 0,
    'geolat': 52.3702,
    'geolon': 4.8952,
    'location': 'Amsterdam',
    'countrycode': 'NL',
    'timezonestr': 'Europe/Amsterdam',
    'timezone': 1.0,
}


def _apply_fixed_chart(mod):
    oa = mod.astrology_chart
    oa.name = FIXED_CHART['name']
    oa.type = 'Radix'
    oa.year = FIXED_CHART['year']
    oa.month = FIXED_CHART['month']
    oa.day = FIXED_CHART['day']
    oa.hour = oa.decHourJoin(
        FIXED_CHART['hour_h'], FIXED_CHART['hour_m'], FIXED_CHART['hour_s'])
    oa.geolat = FIXED_CHART['geolat']
    oa.geolon = FIXED_CHART['geolon']
    oa.location = FIXED_CHART['location']
    oa.countrycode = FIXED_CHART['countrycode']
    oa.timezonestr = FIXED_CHART['timezonestr']
    oa.timezone = FIXED_CHART['timezone']
    oa.utcToLocal()


def test_radix_svg_structure(app_context):
    mod, app, win = app_context
    _apply_fixed_chart(mod)
    path = mod.astrology_chart.makeSVG()
    text = open(path, encoding='utf-8', errors='replace').read()
    assert text.lstrip().startswith('<?xml') or '<svg' in text.lower()
    assert len(text) > 500


def test_radix_svg_golden_digest(app_context, update_golden):
    mod, app, win = app_context
    _apply_fixed_chart(mod)
    path = mod.astrology_chart.makeSVG()
    text = open(path, encoding='utf-8', errors='replace').read()
    digest = svg_digest(text)
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    if update_golden:
        with open(BASELINE, 'w', encoding='utf-8') as f:
            f.write(digest + '\n')
        pytest.skip('Golden baseline updated')
    assert os.path.isfile(BASELINE), (
        'Missing baseline %s — run: make update-golden' % BASELINE)
    expected = open(BASELINE, encoding='utf-8').read().strip()
    assert digest == expected


def test_radix_svg_normalized_stable_substrings(app_context):
    mod, app, win = app_context
    _apply_fixed_chart(mod)
    path = mod.astrology_chart.makeSVG()
    norm = normalize_svg(open(path, encoding='utf-8', errors='replace').read())
    assert 'svg' in norm.lower()
    assert 'Golden Test' in norm or 'NORMALIZED' in norm
