# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pydantic request/response models for the astrology API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ChartType = Literal[
    'Radix', 'Transit', 'Synastry', 'Composite', 'Combine',
    'Solar', 'SecondaryProgression',
]

Tradition = Literal['western', 'vedic']


class ChartEvent(BaseModel):
    """Birth or event data for a single chart."""

    name: str = 'Chart'
    year: int
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: float = Field(ge=0.0, lt=24.0, description='Decimal hour in UTC')
    geolat: float = Field(ge=-90.0, le=90.0)
    geolon: float = Field(ge=-180.0, le=180.0)
    altitude: float = 0.0
    location: str = ''
    timezone: float = 0.0
    timezonestr: str = 'UTC'
    countrycode: str = ''


class ChartRequest(BaseModel):
    """Compute a chart wheel and optional data table."""

    event: ChartEvent
    chart_type: ChartType = 'Radix'
    transit_event: ChartEvent | None = None
    width: int = Field(default=900, ge=200, le=4000)
    height: int = Field(default=640, ge=200, le=4000)
    tradition: Tradition = 'western'
    vedic_layout: Literal['north', 'south', 'wheel'] = 'north'
    vedic_varga: str = 'D1'
    include_table: bool = False


class ChartDataRequest(BaseModel):
    """Ephemeris positions and aspects without SVG rendering."""

    event: ChartEvent
    chart_type: ChartType = 'Radix'
    transit_event: ChartEvent | None = None


class VedicRequest(BaseModel):
    """Vedic snapshot and chart SVG."""

    event: ChartEvent
    layout: Literal['north', 'south', 'wheel'] = 'north'
    varga: str = 'D1'
    width: int = Field(default=800, ge=200, le=4000)
    height: int = Field(default=800, ge=200, le=4000)


class GeonameSearchRequest(BaseModel):
    """Search bundled geonames database."""

    query: str = Field(min_length=1)
    country: str = ''
    limit: int = Field(default=25, ge=1, le=100)


class SavedChart(BaseModel):
    """Chart stored in the people database."""

    id: int | None = None
    name: str
    year: str
    month: str
    day: str
    hour: str
    geolat: str
    geolon: str
    altitude: str = '0'
    location: str = ''
    timezone: str = '0'
    timezonestr: str = 'UTC'
    countrycode: str = ''
    geonameid: int | None = None
    notes: str = ''


class SettingsResponse(BaseModel):
    """User settings from astrodb."""

    astrocfg: dict[str, str]
    planets: list[dict[str, Any]]
    aspects: list[dict[str, Any]]
    colors: dict[str, str]
    labels: dict[str, str]


class ChartResponse(BaseModel):
    """SVG chart output."""

    svg: str
    table_svg: str | None = None
    chart_type: str
    tradition: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ChartDataResponse(BaseModel):
    """Structured ephemeris data."""

    planets_sign: list[int]
    planets_degree: list[float]
    planets_degree_ut: list[float]
    planets_retrograde: list[bool]
    houses_degree_ut: list[float]
    houses_sign: list[int]
    lunar_phase: dict[str, float | int]
    chart_type: str
    meta: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Service health."""

    status: str
    version: str
    gtk_available: bool
    tradition: str = 'shared'
