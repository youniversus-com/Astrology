# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zodiac symbol SVG matches OpenAstro.org placement."""

from unittest.mock import MagicMock

import astrology_app.globals as g
from astrology_app.chart import AstrologyInstance, _ZODIAC_GLYPH_MARKER


def _chart_stub():
	g.db = MagicMock()
	g.db.astrocfg = {'houses_system': 'P', 'chartview': 'european'}
	chart = AstrologyInstance.__new__(AstrologyInstance)
	chart.type = 'Radix'
	chart.c1 = 56
	chart.houses_degree_ut = [0.0] * 27
	chart.houses_degree_ut[6] = 0.0
	chart.zodiac = [
		'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
		'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
	]
	return chart


def test_zodiac_slice_uses_openastro_translate_and_use():
	chart = _chart_stub()
	out = chart.zodiacSlice(3, 240, 'fill:red', 'cancer')
	assert 'translate(-16,-16)' in out
	assert 'scale(0.9)' in out
	assert '<use x="' in out
	assert 'y="' in out
	assert 'xlink:href="#cancer"' in out


def test_make_zodiac_includes_placement_marker():
	chart = _chart_stub()
	chart.colors = {'zodiac_bg_%s' % i: '#000' for i in range(12)}
	out = chart.makeZodiac(240)
	assert 'zodiac-glyphs:' + _ZODIAC_GLYPH_MARKER in out
