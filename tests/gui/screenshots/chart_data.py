# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixed chart data for reproducible documentation screenshots."""

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


def apply_fixed_chart(mod):
    """Load a deterministic radix chart into the active session."""
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
