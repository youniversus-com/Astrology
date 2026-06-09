# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin helpers for people-database CRUD via the API."""

from __future__ import annotations

import astrology_app.globals as g

from astrology_api.schemas import SavedChart


def save_chart(chart: SavedChart) -> None:
    """Insert or update a chart in peopledb."""
    database = g.db
    database.open()
    row = chart.model_dump()
    chart_id = row.pop('id', None)
    fields = (
        'name', 'year', 'month', 'day', 'hour', 'geolon', 'geolat',
        'altitude', 'location', 'timezone', 'notes', 'countrycode',
        'geonameid', 'timezonestr',
    )
    values = tuple(str(row.get(f, '') or '') for f in fields)
    if chart_id:
        sql = (
            'UPDATE event_natal SET name=?, year=?, month=?, day=?, hour=?, '
            'geolon=?, geolat=?, altitude=?, location=?, timezone=?, notes=?, '
            'countrycode=?, geonameid=?, timezonestr=? WHERE id=?'
        )
        database.pcursor.execute(sql, values + (chart_id,))
    else:
        sql = (
            'INSERT INTO event_natal (name, year, month, day, hour, geolon, geolat, '
            'altitude, location, timezone, notes, image, countrycode, geonameid, '
            'timezonestr, extra) VALUES (?,?,?,?,?,?,?,?,?,?,?,"","",?,?,"")'
        )
        database.pcursor.execute(sql, values)
    database.plink.commit()
    database.close()


def delete_chart(chart_id: int) -> None:
    """Remove a chart from peopledb."""
    database = g.db
    database.open()
    database.pcursor.execute('DELETE FROM event_natal WHERE id=?', (chart_id,))
    database.plink.commit()
    database.close()
