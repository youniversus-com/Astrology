# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""User settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from astrology_api.bootstrap import api_context
from astrology_api.schemas import SettingsResponse

router = APIRouter(prefix='/settings', tags=['settings'])


@router.get('', response_model=SettingsResponse)
def get_settings() -> SettingsResponse:
    """Return astrocfg, planet/aspect settings, colors, and labels."""
    with api_context() as (_, database, _):
        return SettingsResponse(
            astrocfg=dict(database.astrocfg),
            planets=database.getSettingsPlanet(),
            aspects=database.getSettingsAspect(),
            colors=database.getColors(),
            labels=database.getLabel(),
        )


@router.patch('/astrocfg')
def update_astrocfg(updates: dict[str, str]) -> dict:
    """Update one or more astrocfg keys."""
    with api_context() as (_, database, _):
        for key, value in updates.items():
            database.setAstrocfg(key, value)
        return {'astrocfg': dict(database.astrocfg)}
