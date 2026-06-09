# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Set home location dialog."""

import datetime

from gi.repository import Gtk

from astrologymod import geoname, gtkcompat as g4
from astrologymod.timezone_utils import localize_naive, naive_utc

import astrology_app.globals as g
from astrology_app.debug import dprint
from astrology_app.i18n import TRANSLATION

def _(msg):
	return TRANSLATION['default'].gettext(msg)
from astrology_app.ui.geonames_picker import attach_offline_picker


class LocationDialogMixin:
    """Mixin: home location settings dialog."""

    def settingsLocation(self, widget):
        self.settingsLocationMode = True
        self.checkInternetConnection()

        self.win_location = g4.new_dialog(transient_for=self.window)
        g4.window_set_icon(self.win_location, g.cfg.iconWindow)
        self.win_location.set_title(_("Please Set Your Home Location"))
        self.win_location.connect(
            "close-request", lambda w, *args: self.settingsLocationDestroy())
        self.win_location.set_default_size(580, 300)

        table = g4.new_table(5, 2, False)
        g4.grid_set_spacing(table, 12)
        g4.box_pack(g4.dialog_content(self.win_location), table, True, True, 0)

        g4.grid_attach(table, g4.new_label(_('Location') + ':'), 0, 1, 1, 2)
        self.LLoc = g4.new_label(g.astrology_chart.home_location)
        self.LLoc.set_halign(Gtk.Align.START)
        self.LLoc.set_wrap(True)
        g4.grid_attach(table, self.LLoc, 1, 2, 1, 2)

        g4.grid_attach(table, g4.new_label(_('Latitude') + ':'), 0, 1, 2, 3)
        self.LLat = g4.new_label(str(g.astrology_chart.home_geolat))
        g4.grid_attach(table, self.LLat, 1, 2, 2, 3)

        g4.grid_attach(table, g4.new_label(_('Longitude') + ':'), 0, 1, 3, 4)
        self.LLon = g4.new_label(str(g.astrology_chart.home_geolon))
        g4.grid_attach(table, self.LLon, 1, 2, 3, 4)

        if self.iconn:
            loc_row = g4.new_hbox(5)
            g4.box_pack(loc_row, g4.new_label(_("City") + ": "), False, False, 0)
            self.geoLoc = Gtk.Entry()
            self.geoLoc.set_max_length(100)
            self.geoLoc.set_width_chars(30)
            self.geoLoc.set_text(g.astrology_chart.home_location.partition(',')[0])
            g4.box_pack(loc_row, self.geoLoc, True, True, 0)
            g4.box_pack(loc_row, g4.new_label(" " + _("Country-code") + ": "), False, False, 0)
            self.geoCC = Gtk.Entry()
            self.geoCC.set_max_length(2)
            self.geoCC.set_width_chars(2)
            self.geoCC.set_text(g.astrology_chart.home_countrycode)
            g4.box_pack(loc_row, self.geoCC, False, False, 0)
            g4.grid_attach(table, loc_row, 0, 2, 0, 1)
        else:
            picker_row = g4.new_hbox(8)
            attach_offline_picker(
                self, picker_row,
                g.astrology_chart.geolat, g.astrology_chart.geolon,
                g.db,
                self.eventDataChangedContbox,
                self.eventDataChangedCountrybox,
                self.eventDataChangedProvbox,
                self.eventDataChangedCitybox,
            )
            g4.grid_attach(table, picker_row, 0, 2, 0, 1)

        buttonbox = g4.dialog_action_area(self.win_location)
        button = g4.button_new_stock(g4.STOCK_OK)
        button.connect("clicked", self.settingsLocationSubmit)
        g4.button_set_can_default(button, True)
        g4.box_pack(buttonbox, button, False, False, 0)
        g4.button_grab_default(button)

        button = g4.button_new_stock(g4.STOCK_APPLY, _('Test'))
        button.connect("clicked", self.settingsLocationApply)
        g4.box_pack(buttonbox, button, False, False, 0)

        button = g4.button_new_stock(g4.STOCK_CANCEL)
        button.connect("clicked", lambda w: self.settingsLocationDestroy())
        g4.box_pack(buttonbox, button, False, False, 0)

        self.win_location.present()

    def settingsLocationSubmit(self, widget):
        self.settingsLocationApply(widget)
        if self.geoLocFound:
            self.settingsLocationDestroy()

    def settingsLocationApply(self, widget):
        self.geoLocFound = True
        if self.iconn:
            result = geoname.search(self.geoLoc.get_text(), self.geoCC.get_text())
            if result:
                lat = float(result[0]['lat'])
                lon = float(result[0]['lng'])
                tzstr = result[0]['timezonestr']
                cc = result[0]['countryCode']
                loc = '%s, %s' % (result[0]['name'], result[0]['countryName'])
                dprint(
                    'settingsLocationApply: %s found; %s %s %s'
                    % (self.geoLoc.get_text(), lat, lon, loc))
            else:
                self.geoLocFound = False
                self.geoLoc.set_text('City Not Found, Try Again!')
                return
        else:
            lat = float(self.GEON_lat)
            lon = float(self.GEON_lon)
            loc = self.GEON_loc
            cc = self.GEON_cc
            tzstr = self.GEON_tzstr

        g.db.setSettingsLocation(lat, lon, loc, cc, tzstr)
        g.astrology_chart.home_location = loc
        g.astrology_chart.home_geolat = lat
        g.astrology_chart.home_geolon = lon
        g.astrology_chart.home_countrycode = cc
        g.astrology_chart.home_timezonestr = tzstr
        g.astrology_chart.location = loc
        g.astrology_chart.timezonestr = tzstr
        g.astrology_chart.geolat = lat
        g.astrology_chart.geolon = lon
        g.astrology_chart.countrycode = cc
        g.astrology_chart.transit = False
        g.astrology_chart.name = _("Here and Now")
        g.astrology_chart.type = "Radix"
        self.LLat.set_text(str(lat))
        self.LLon.set_text(str(lon))
        self.LLoc.set_text(str(loc))

        now = datetime.datetime.now()
        dt_input = datetime.datetime(
            now.year, now.month, now.day, now.hour, now.minute, now.second)
        dt = localize_naive(dt_input, g.astrology_chart.timezonestr)
        dt_utc = naive_utc(dt)
        g.astrology_chart.name = _("Here and Now")
        g.astrology_chart.charttype = g.astrology_chart.label["radix"]
        g.astrology_chart.year = dt_utc.year
        g.astrology_chart.month = dt_utc.month
        g.astrology_chart.day = dt_utc.day
        g.astrology_chart.hour = g.astrology_chart.decHourJoin(
            dt_utc.hour, dt_utc.minute, dt_utc.second)
        g.astrology_chart.timezone = g.astrology_chart.offsetToTz(dt.utcoffset())
        g.astrology_chart.altitude = 25
        g.astrology_chart.utcToLocal()
        self.updateChart()
        dprint('Setting New Home Location: %s %s %s' % (lat, lon, loc))

    def settingsLocationDestroy(self):
        self.settingsLocationMode = False
        self.win_location.close()
