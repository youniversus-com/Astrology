# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application — shared backend for web and desktop clients."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from astrology_api.bootstrap import gtk_available
from astrology_api.routers import charts, geonames, settings
from astrology_api.schemas import HealthResponse
from astrology_app.constants import VERSION


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title='YoUniverse Astrology API',
        description=(
            'Shared HTTP backend for the YoUniverse web and desktop applications. '
            'Chart math is powered by astrologymod (Swiss Ephemeris).'
        ),
        version=VERSION,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.get('/api/health', response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status='ok',
            version=VERSION,
            gtk_available=gtk_available(),
        )

    app.include_router(charts.router, prefix='/api')
    app.include_router(settings.router, prefix='/api')
    app.include_router(geonames.router, prefix='/api')

    return app


app = create_app()


def main() -> None:
    """Run the API with uvicorn."""
    import os

    import uvicorn

    host = os.environ.get('ASTROLOGY_API_HOST', '127.0.0.1')
    port = int(os.environ.get('ASTROLOGY_API_PORT', '8765'))
    uvicorn.run(
        'astrology_api.main:app',
        host=host,
        port=port,
        reload=False,
    )


if __name__ == '__main__':
    main()
