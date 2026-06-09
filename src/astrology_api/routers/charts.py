# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Chart computation and saved-chart endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from astrology_api.bootstrap import api_context
from astrology_api.schemas import (
    ChartDataRequest,
    ChartDataResponse,
    ChartRequest,
    ChartResponse,
    SavedChart,
    VedicRequest,
)
from astrology_api.services.chart_service import generate_chart_svg
from astrology_api.services.db_service import delete_chart as remove_chart
from astrology_api.services.db_service import save_chart as persist_chart
from astrology_api.services.ephemeris_service import compute_ephemeris, compute_vedic

router = APIRouter(prefix='/charts', tags=['charts'])


@router.post('/compute', response_model=ChartResponse)
def compute_chart(request: ChartRequest) -> ChartResponse:
    """Generate chart wheel SVG (western or vedic)."""
    with api_context():
        try:
            result = generate_chart_svg(request)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChartResponse(**result)


@router.post('/data', response_model=ChartDataResponse)
def chart_data(request: ChartDataRequest) -> ChartDataResponse:
    """Return ephemeris positions and houses as JSON (no GTK)."""
    with api_context() as (_, database, _):
        data = compute_ephemeris(
            request, dict(database.astrocfg), database.getSettingsPlanet(),
        )
    return ChartDataResponse(**data)


@router.post('/vedic')
def vedic_chart(request: VedicRequest) -> dict:
    """Vedic snapshot JSON plus chart SVG."""
    with api_context() as (_, database, _):
        labels = database.getLabel()
        planet_labels = {i: labels.get(f'planet_{i}', str(i)) for i in range(35)}
        snapshot, svg = compute_vedic(
            request,
            dict(database.astrocfg),
            database.getSettingsPlanet(),
            planet_labels,
        )
    return {'snapshot': snapshot, 'svg': svg}


@router.get('/saved')
def list_saved_charts() -> list[dict]:
    """List charts stored in the people database."""
    with api_context() as (_, database, _):
        return database.getDatabase()


@router.post('/saved')
def save_chart(chart: SavedChart) -> dict:
    """Save a chart to the people database."""
    with api_context():
        persist_chart(chart)
    return {'status': 'ok'}


@router.delete('/saved/{chart_id}')
def delete_chart(chart_id: int) -> dict:
    """Delete a saved chart by id."""
    with api_context():
        remove_chart(chart_id)
    return {'status': 'ok'}
