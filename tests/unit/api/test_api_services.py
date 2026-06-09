# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""API service smoke tests (no HTTP server)."""

import pytest

pytestmark = pytest.mark.unit


def test_geonames_search(astrology_db):
    from astrology_api.bootstrap import api_context
    from astrology_api.schemas import GeonameSearchRequest
    from astrology_api.services.geonames_service import search_geonames

    with api_context():
        rows = search_geonames(GeonameSearchRequest(query='Paris', limit=5))
    assert rows
    assert 'latitude' in rows[0]
