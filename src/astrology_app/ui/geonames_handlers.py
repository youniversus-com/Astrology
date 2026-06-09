# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Geonames offline picker change handlers and city search."""

from astrologymod import gtkcompat as g4
from astrologymod.validation import normalize_iso2

import astrology_app.globals as g
from astrology_app.i18n import TRANSLATION

def _(msg):
	return TRANSLATION['default'].gettext(msg)


class GeonamesHandlersMixin:
    """Mixin: cascade geonames DropDowns and offline city search."""

    @staticmethod
    def _geonames_pick_row(search_map, rows, code, fallback_index=0):
        """Return the row tuple for ``code``, or the first row when code is missing."""
        if rows:
            if code is not None and code in search_map:
                return rows[search_map[code]]
            return rows[fallback_index]
        return None

    def _geonames_load_countries(self, continent_code):
        """Fill the country DropDown for ``continent_code``."""
        sql = 'SELECT * FROM countryinfo WHERE continent=? ORDER BY name ASC'
        g.db.gquery(sql, (continent_code,))
        list_rows = []
        activecountry = 0
        self.searchcountry = {}
        for i, db_row in enumerate(g.db.gcursor):
            self.searchcountry[db_row['isoalpha2']] = i
            if self.GEON_nearest['country'] == db_row['isoalpha2']:
                activecountry = i
                self.GEON_nearest['country'] = None
            list_rows.append((db_row['name'], db_row['isoalpha2']))
        g.db.gclose()
        g4.picker_set_rows(self.countrybox, list_rows, activecountry)
        return list_rows

    def _geonames_load_provinces(self, country_code, country_name):
        """Fill the province DropDown for ``country_code``."""
        sql = 'SELECT * FROM admin1codes WHERE country=? ORDER BY admin1 ASC'
        g.db.gquery(sql, (country_code,))
        list_rows = []
        activeprov = 0
        self.searchprov = {}
        for i, db_row in enumerate(g.db.gcursor):
            self.searchprov[db_row['admin1']] = i
            if self.GEON_nearest['admin1'] == db_row['admin1']:
                activeprov = i
                self.GEON_nearest['admin1'] = None
            list_rows.append(
                (db_row['province'], db_row['country'], db_row['admin1'], country_name))
        g.db.gclose()
        g4.picker_set_rows(self.provbox, list_rows, activeprov)
        return list_rows

    def _geonames_load_cities(self, country_code, admin1_code, country_name, province_name):
        """Fill the city DropDown for ``country_code`` / ``admin1_code``."""
        sql = (
            'SELECT * FROM geonames WHERE country=? AND admin1=? ORDER BY name ASC'
        )
        g.db.gquery(sql, (country_code, admin1_code))
        list_rows = []
        activecity = 0
        self.searchcity = {}
        for i, db_row in enumerate(g.db.gcursor):
            self.searchcity[str(db_row['geonameid'])] = i
            nearest_id = self.GEON_nearest.get('geonameid')
            if nearest_id is not None and str(nearest_id) == str(db_row['geonameid']):
                activecity = i
                self.GEON_nearest['geonameid'] = None
            list_rows.append((
                db_row['name'],
                str(db_row['latitude']),
                str(db_row['longitude']),
                country_name,
                province_name,
                db_row['country'],
                str(db_row['geonameid']),
                db_row['timezone'],
            ))
        g.db.gclose()
        g4.picker_set_rows(self.citybox, list_rows, activecity)
        return list_rows

    def seed_offline_geonames_pickers(self, continent_code):
        """Populate country, province, and city pickers without relying on Gtk selection."""
        self._geonames_load_countries(continent_code)
        country_row = self._geonames_pick_row(
            self.searchcountry,
            g4.picker_get_rows(self.countrybox),
            self.GEON_nearest.get('country'),
        )
        if country_row is None:
            return
        self._geonames_load_provinces(country_row[1], country_row[0])
        prov_row = self._geonames_pick_row(
            self.searchprov,
            g4.picker_get_rows(self.provbox),
            self.GEON_nearest.get('admin1'),
        )
        if prov_row is None:
            return
        self._geonames_load_cities(prov_row[1], prov_row[2], prov_row[3], prov_row[0])
        self.eventDataChangedCitybox(self.citybox)

    def citySearch(self, widget):
        city = self.citysearch.get_text()
        isoalpha2 = None
        if ',' in city:
            split = city.split(',')
            for x in range(len(split)):
                sql = (
                    'SELECT * FROM countryinfo WHERE '
                    '(isoalpha2 LIKE ? OR name LIKE ?) LIMIT 1'
                )
                y = split[x].strip()
                g.db.gquery(sql, (y, y))
                result = g.db.gcursor.fetchone()
                if result is not None:
                    isoalpha2 = normalize_iso2(result['isoalpha2'])
                    city = city.replace(
                        split[x] + ',', '').replace(',' + split[x], '').strip()
                    break

        normal = city
        fuzzy = '%' + city + '%'
        country_args = ()
        country_clause = ''
        if isoalpha2:
            country_clause = ' AND country=?'
            country_args = (isoalpha2,)

        sql = (
            'SELECT * FROM geonames WHERE '
            '(name LIKE ? OR asciiname LIKE ?)' + country_clause + ' LIMIT 1'
        )
        g.db.gquery(sql, (normal, normal) + country_args)
        result = g.db.gcursor.fetchone()

        if result is None:
            g.db.gquery(sql, (fuzzy, fuzzy) + country_args)
            result = g.db.gcursor.fetchone()

        if result is None:
            sql_alt = (
                'SELECT * FROM geonames WHERE (alternatenames LIKE ?)'
                + country_clause + ' LIMIT 1'
            )
            g.db.gquery(sql_alt, (fuzzy,) + country_args)
            result = g.db.gcursor.fetchone()

        if result is not None:
            sql = 'SELECT continent FROM countryinfo WHERE isoalpha2=? LIMIT 1'
            g.db.gquery(sql, (result['country'],))
            cont_row = g.db.gcursor.fetchone()
            g.db.gclose()
            g4.picker_set_selected(
                self.contbox,
                self.searchcontinent[cont_row[0]],
            )
            g4.picker_set_selected(
                self.countrybox, self.searchcountry[result['country']])
            g4.picker_set_selected(
                self.provbox, self.searchprov[result['admin1']])
            g4.picker_set_selected(
                self.citybox, self.searchcity[str(result['geonameid'])])

    def eventDataChangedContbox(self, combobox):
        row = g4.picker_selected_row(combobox)
        if row is None:
            rows = g4.picker_get_rows(combobox)
            if not rows:
                return
            idx = g4.picker_selected_index(combobox)
            row = rows[idx] if 0 <= idx < len(rows) else rows[0]
        self._geonames_load_countries(row[1])

    def eventDataChangedCountrybox(self, combobox):
        row = g4.picker_selected_row(combobox)
        if row is None:
            rows = g4.picker_get_rows(combobox)
            if not rows:
                return
            row = rows[0]
        self._geonames_load_provinces(row[1], row[0])

    def eventDataChangedProvbox(self, combobox):
        row = g4.picker_selected_row(combobox)
        if row is None:
            rows = g4.picker_get_rows(combobox)
            if not rows:
                return
            row = rows[0]
        self._geonames_load_cities(row[1], row[2], row[3], row[0])

    def eventDataChangedCitybox(self, combobox):
        row = g4.picker_selected_row(combobox)
        if row is None:
            return
        self.GEON_lat = row[1]
        self.GEON_lon = row[2]
        self.GEON_loc = '%s, %s, %s' % (row[0], row[4], row[3])
        self.GEON_cc = row[5]
        self.GEON_id = row[6]
        self.GEON_tzstr = row[7]
        if self.settingsLocationMode:
            self.LLoc.set_text(_('Location') + ': %s' % (self.GEON_loc))
            self.LLat.set_text(_('Latitude') + ': %s' % (self.GEON_lat))
            self.LLon.set_text(_('Longitude') + ': %s' % (self.GEON_lon))
        else:
            self.entry2.set_text(
                ' %s: %s\n %s: %s\n %s: %s'
                % (
                    _('Latitude'), self.GEON_lat,
                    _('Longitude'), self.GEON_lon,
                    _('Location'), self.GEON_loc,
                )
            )
