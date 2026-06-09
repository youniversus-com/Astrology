# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Home location SQL uses bound parameters."""
import pytest

pytestmark = pytest.mark.unit


def test_settings_location_quote_safe(astrology_db):
    astrology_db.getSettingsLocation()
    malicious = 'x", home_geolat="0'
    astrology_db.setSettingsLocation('1', '2', malicious, 'XX', 'Europe/Test')
    astrology_db.open()
    astrology_db.cursor.execute(
        'SELECT value FROM astrocfg WHERE name=?', ('home_location',))
    row = astrology_db.cursor.fetchone()[0]
    astrology_db.close()
    assert row == malicious
