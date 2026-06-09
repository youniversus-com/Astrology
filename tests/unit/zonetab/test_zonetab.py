# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for astrologymod.zonetab (no GTK)."""

import pytest

from astrologymod import zonetab

pytestmark = pytest.mark.unit


class TestLatLong:
    def test_latlong_southern_coords(self):
        lat, lon = zonetab.latlong('-1247+04514')
        assert abs(lat - (-12.783333)) < 0.001
        assert abs(lon - 45.233333) < 0.001


class TestCoord:
    @pytest.mark.parametrize(
        'sign,digits,expected',
        [
            ('-', '1247', -12.783333333333333),
            ('+', '04514', 45.233333333333334),
            ('-', '690022', -69.00611111111111),
            ('+', '0393524', 39.590000000000003),
        ],
    )
    def test_coord(self, sign, digits, expected):
        assert abs(zonetab.coord(sign, digits) - expected) < 1e-9


class TestDms:
    def test_dms_north(self):
        assert abs(zonetab.dms('N', 30, 11, 40.3) - 30.194527777777779) < 0.001


class TestDistance:
    def test_distance_same_point_is_zero(self):
        assert zonetab.distance(52.0, 5.0, 52.0, 5.0) == pytest.approx(0.0, abs=1e-12)

    def test_distance_symmetry(self):
        a = zonetab.distance(40.0, -74.0, 34.0, -118.0)
        b = zonetab.distance(34.0, -118.0, 40.0, -74.0)
        assert a == pytest.approx(b)


class TestOptimize:
    def test_optimize_picks_minimum(self):
        seq = [('a', 1), ('b', 2), ('c', 0)]
        assert zonetab.optimize(seq, lambda x: x[1])[0] == 'c'


class TestTimezones:
    def test_timezones_from_sample_tab(self, tmp_path):
        tab = tmp_path / 'zone.tab'
        tab.write_text(
            '# comment\n'
            'US\t+394421-1190528\tAmerica/Los_Angeles\n'
            'NL\t+5222+00454\tEurope/Amsterdam\n',
            encoding='utf-8',
        )
        zones = list(zonetab.timezones(str(tab)))
        assert len(zones) == 2
        assert zones[0][2] == 'America/Los_Angeles'
        assert zones[1][0] == 'NL'

    def test_timezones_exclude_filter(self, tmp_path):
        tab = tmp_path / 'zone.tab'
        tab.write_text(
            'US\t+394421-1190528\tAmerica/Indiana/Indianapolis\n'
            'US\t+394421-1190528\tAmerica/Chicago\n',
            encoding='utf-8',
        )
        zones = list(zonetab.timezones(str(tab), exclude=['Indiana']))
        assert len(zones) == 1
        assert zones[0][2] == 'America/Chicago'
