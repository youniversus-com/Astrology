# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline geonames continent/country/province/city picker widgets (GTK 4 DropDown)."""

from astrologymod import gtkcompat as g4


def attach_offline_picker(window, hbox, geolat, geolon, db, on_cont_changed,
                          on_country_changed, on_prov_changed, on_city_changed):
    """Build four DropDown pickers on ``hbox`` and wire selection handlers.

    Sets ``window.GEON_nearest``, dropdown widgets, and ``window.searchcontinent``.
    """
    window.GEON_nearest = db.gnearest(geolat, geolon)
    window.contbox = g4.new_code_dropdown()
    g4.box_pack(hbox, window.contbox, True, True, 0)

    db.gquery('SELECT * FROM continent ORDER BY name ASC')
    cont_rows = []
    activecont = 0
    window.searchcontinent = {}
    for i, row in enumerate(db.gcursor):
        window.searchcontinent[row['code']] = i
        if row['code'] == window.GEON_nearest['continent']:
            activecont = i
            window.GEON_nearest['continent'] = None
        cont_rows.append((row['name'], row['code']))
    db.gclose()
    g4.picker_set_rows(window.contbox, cont_rows, activecont)

    window.countrybox = g4.new_code_dropdown()
    g4.picker_connect_changed(window.countrybox, on_country_changed)
    g4.box_pack(hbox, window.countrybox, True, True, 0)

    window.provbox = g4.new_code_dropdown()
    g4.picker_connect_changed(window.provbox, on_prov_changed)
    g4.box_pack(hbox, window.provbox, True, True, 0)

    window.citybox = g4.new_code_dropdown()
    g4.picker_connect_changed(window.citybox, on_city_changed)
    g4.box_pack(hbox, window.citybox, True, True, 0)

    g4.picker_connect_changed(window.contbox, on_cont_changed)

    continent_code = cont_rows[activecont][1] if cont_rows else None
    if continent_code and hasattr(window, 'seed_offline_geonames_pickers'):
        window.seed_offline_geonames_pickers(continent_code)
    else:
        g4.cascade_geonames_pickers(
            window.contbox,
            window.countrybox,
            window.provbox,
            window.citybox,
            on_cont_changed,
            on_country_changed,
            on_prov_changed,
            on_city_changed,
        )
