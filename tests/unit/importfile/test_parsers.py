# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Chart import parsers — valid sample files."""
import pytest

from astrologymod import importfile

pytestmark = pytest.mark.unit

SAMPLE_OAC = """<?xml version="1.0"?>
<astrologychart>
  <name>Test Chart</name>
  <datetime>1990-06-15 14:30:00</datetime>
  <location>Amsterdam</location>
  <altitude>0</altitude>
  <latitude>52.37</latitude>
  <longitude>4.89</longitude>
  <countrycode>NL</countrycode>
  <timezone>1.0</timezone>
  <geonameid>2759794</geonameid>
  <extra></extra>
</astrologychart>
"""

SAMPLE_OROBOROS = """<?xml version="1.0"?>
<ASTROLOGY>
  <NAME>Sample</NAME>
  <DATETIME>1985-03-20 12:00:00</DATETIME>
  <LOCATION altitude="10" latitude="48.85" longitude="2.35">Paris</LOCATION>
  <COUNTRY zoneinfo="Europe/Paris">France</COUNTRY>
</ASTROLOGY>
"""

SAMPLE_ASTROLOG32 = """@0102
/qb 6 23 1972  3:00:00 ST -1:00   5:24:00E 43:18:00N
/zi "Zinedine Zidane" "Marseille"
"""


def test_get_yac(tmp_path):
    path = tmp_path / 'chart.yac'
    path.write_text(SAMPLE_OAC, encoding='utf-8')
    charts = importfile.getYAC(str(path))
    assert len(charts) == 1
    assert charts[0]['name'] == 'Test Chart'


def test_get_oroboros(tmp_path):
    path = tmp_path / 'chart.xml'
    path.write_text(SAMPLE_OROBOROS, encoding='utf-8')
    charts = importfile.getOroboros(str(path))
    assert charts[0]['name'] == 'Sample'
    assert charts[0]['zoneinfo'] == 'Europe/Paris'


def test_get_astrolog32(tmp_path):
    path = tmp_path / 'chart.dat'
    path.write_text(SAMPLE_ASTROLOG32, encoding='utf-8')
    charts = importfile.getAstrolog32(str(path))
    assert charts[0]['name'] == 'Zinedine Zidane'
    assert float(charts[0]['latitude']) == pytest.approx(43.3, rel=0.01)
