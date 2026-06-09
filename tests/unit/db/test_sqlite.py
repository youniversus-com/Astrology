# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""SQLite configuration and settings (isolated HOME)."""
import pytest

pytestmark = pytest.mark.unit


def test_astrocfg_version_present(astrology_db):
    assert 'version' in astrology_db.astrocfg
    assert astrology_db.astrocfg['version']


def test_settings_location_roundtrip(astrology_db):
    astrology_db.getSettingsLocation()  # ensure home_* keys exist in astrocfg
    astrology_db.setSettingsLocation('52.12', '6.22', 'Amsterdam', 'NL', 'Europe/Amsterdam')
    astrology_db.open()
    rows = {}
    for key in (
        'home_location', 'home_geolat', 'home_geolon',
        'home_countrycode', 'home_timezonestr',
    ):
        astrology_db.cursor.execute(
            'SELECT value FROM astrocfg WHERE name=?', (key,))
        rows[key] = astrology_db.cursor.fetchone()[0]
    astrology_db.close()
    assert rows['home_location'] == 'Amsterdam'
    assert rows['home_geolat'] == '52.12'
    assert rows['home_geolon'] == '6.22'
    assert rows['home_countrycode'] == 'NL'
    assert rows['home_timezonestr'] == 'Europe/Amsterdam'


def test_get_astrocfg_keys(astrology_db):
    assert astrology_db.getAstrocfg('houses_system') in ('P', 'K', 'R', 'C', 'E', 'W', 'X', 'M', 'H', 'T', 'B', 'V', 'O')
