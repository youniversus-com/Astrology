# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline geonames picker seeding."""

import gi

gi.require_version('Gtk', '4.0')

from astrology_app.config import AstrologyCfg
from astrology_app.db import AstrologySqlite
from astrology_app.ui.geonames_handlers import GeonamesHandlersMixin
from astrology_app.ui.geonames_picker import attach_offline_picker
import astrology_app.globals as g
from astrologymod import gtkcompat as g4


class _Win(GeonamesHandlersMixin):
    GEON_nearest = {}
    settingsLocationMode = True
    LLoc = type('L', (), {'set_text': lambda *a: None})()
    LLat = type('L', (), {'set_text': lambda *a: None})()
    LLon = type('L', (), {'set_text': lambda *a: None})()


def test_attach_offline_picker_fills_all_four_dropdowns():
    g.cfg = AstrologyCfg()
    g.db = AstrologySqlite()
    try:
        win = _Win()
        win.GEON_nearest = g.db.gnearest(52.12, 6.22)
        from gi.repository import Gtk

        box = Gtk.Box()
        attach_offline_picker(
            win, box, 52.12, 6.22, g.db,
            win.eventDataChangedContbox,
            win.eventDataChangedCountrybox,
            win.eventDataChangedProvbox,
            win.eventDataChangedCitybox,
        )
        assert len(g4.picker_get_rows(win.contbox)) > 0
        assert len(g4.picker_get_rows(win.countrybox)) > 0
        assert len(g4.picker_get_rows(win.provbox)) > 0
        assert len(g4.picker_get_rows(win.citybox)) > 0
        assert g4.picker_selected_row(win.contbox) is not None
        assert g4.picker_selected_row(win.countrybox) is not None
        assert g4.picker_selected_row(win.provbox) is not None
        assert g4.picker_selected_row(win.citybox) is not None
    finally:
        try:
            g.db.close()
        except Exception:
            pass
