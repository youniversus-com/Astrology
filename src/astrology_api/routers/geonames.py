# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Geonames search endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from astrology_api.bootstrap import api_context
from astrology_api.schemas import GeonameSearchRequest
from astrology_api.services.geonames_service import search_geonames

router = APIRouter(prefix='/geonames', tags=['geonames'])


@router.post('/search')
def geoname_search(request: GeonameSearchRequest) -> list[dict]:
    """Search the offline geonames atlas."""
    with api_context():
        return search_geonames(request)
