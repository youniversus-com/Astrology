# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Geonames search against the bundled offline database."""

from __future__ import annotations

import astrology_app.globals as g

from astrology_api.schemas import GeonameSearchRequest


def search_geonames(request: GeonameSearchRequest) -> list[dict[str, str | float | int]]:
    """Search cities in the bundled geonames SQL database."""
    query = request.query.strip()
    if not query:
        return []

    pattern = f'%{query}%'
    if request.country:
        sql = (
            'SELECT name, latitude, longitude, geonameid, country, admin1, timezone '
            'FROM geonames WHERE country=? AND name LIKE ? '
            'ORDER BY name ASC LIMIT ?'
        )
        params = (request.country.upper(), pattern, request.limit)
    else:
        sql = (
            'SELECT name, latitude, longitude, geonameid, country, admin1, timezone '
            'FROM geonames WHERE name LIKE ? '
            'ORDER BY name ASC LIMIT ?'
        )
        params = (pattern, request.limit)

    g.db.gquery(sql, params)
    rows: list[dict[str, str | float | int]] = []
    for row in g.db.gcursor:
        rows.append({
            'name': row['name'],
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'geonameid': int(row['geonameid']),
            'country': row['country'],
            'admin1': row['admin1'] or '',
            'timezone': row['timezone'] or 'UTC',
        })
    g.db.gclose()
    return rows
