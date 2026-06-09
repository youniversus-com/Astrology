# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Edit event details dialog."""

from gi.repository import Gtk

from astrologymod import gtkcompat as g4
import astrology_app.globals as g
from astrology_app.debug import dprint
from astrology_app.i18n import TRANSLATION

def _(msg):
	return TRANSLATION['default'].gettext(msg)
from astrology_app.ui.geonames_picker import attach_offline_picker


class EventEditorMixin:
	def eventData(self, widget, edit=False):
		self.settingsLocationMode = False
		self.checkInternetConnection()

		self.window2 = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.window2, g.cfg.iconWindow)
		self.window2.set_title(_("Edit Event Details"))
		self.window2.connect("close-request", lambda w, *args: self.window2.close())
		self.window2.set_default_size(620, 420)

		table = g4.new_table(5, 2, False)
		g4.grid_set_spacing(table, 12)
		g4.box_pack(g4.dialog_content(self.window2), table, True, True, 0)
		
		#Name entry
		hbox = g4.new_hbox(5)
		g4.grid_attach(table, hbox,0,1,0,1)

		label=g4.new_label(_("Name")+":")
		g4.box_pack(hbox, label, False, False, 0)

		self.name = Gtk.Entry()
		self.name.set_max_length(50)
		self.name.set_width_chars(25)
		self.name.set_text(g.astrology_chart.name)
		g4.box_pack(hbox, self.name, False, False, 0)
		
		#name entry ( non editable)
		self.ename = g4.new_label(g.astrology_chart.name)
		g4.grid_attach(table, self.ename, 1, 2, 0, 1)
		
		#if connection use geocoders, else use geonames sql database

		#display of location (non editable)
		self.entry2 = g4.new_label(' '+_('Latitude')+
			': %s\n '%g.astrology_chart.geolat+_('Longitude')+
			': %s\n '%g.astrology_chart.geolon+_('Location')+
			': %s' %g.astrology_chart.location)
		g4.grid_attach(table, self.entry2, 1, 2, 1, 2)
		
		#check for connection
		if self.iconn:
			hbox = g4.new_hbox(5)
			g4.grid_attach(table, hbox,0,1,1,2)
			#entry for location (editable)
			label=g4.new_label(_("City")+": ")
			g4.box_pack(hbox, label, False, False, 0)
	
			self.geoLoc = Gtk.Entry()
			self.geoLoc.set_max_length(50)
			self.geoLoc.set_width_chars(20)
			self.geoLoc.set_text(g.astrology_chart.location.partition(',')[0])
			g4.box_pack(hbox, self.geoLoc, False, False, 0)

			label=g4.new_label(" "+_("Country-code")+": ")
			g4.box_pack(hbox, label, False, False, 0)
			
			self.geoCC = Gtk.Entry()
			self.geoCC.set_max_length(2)
			self.geoCC.set_width_chars(2)
			self.geoCC.set_text(g.astrology_chart.countrycode)
			g4.box_pack(hbox, self.geoCC, False, False, 0)
		else:
			vbox = g4.new_vbox(5)
			g4.grid_attach(table, vbox, 0, 1, 1, 2)
			hbox = g4.new_hbox(8)
			attach_offline_picker(
				self, hbox,
				g.astrology_chart.geolat, g.astrology_chart.geolon,
				g.db,
				self.eventDataChangedContbox,
				self.eventDataChangedCountrybox,
				self.eventDataChangedProvbox,
				self.eventDataChangedCitybox,
			)
			g4.box_pack(vbox, hbox, False, False, 0)
			hbox=g4.new_hbox(5)			
			label=g4.new_label(_("Search City")+":")
			g4.box_pack(hbox, label, False, False, 0)
			self.citysearch = Gtk.Entry()
			self.citysearch.set_max_length(34)
			self.citysearch.set_width_chars(24)
			g4.box_pack(hbox, self.citysearch, False, False, 0)
			self.citysearchbutton = g4.new_button(_('Search'))
			self.citysearchbutton.connect("clicked", self.citySearch)
			self.citysearch.connect("activate", self.citySearch)
			g4.box_pack(hbox, self.citysearchbutton, False, False, 0)
			label=g4.new_label("("+_("For example: London, GB")+")")
			g4.box_pack(hbox, label, False, False, 0)
			g4.box_pack(vbox, hbox, False, False, 0)

		#Year month day entry
		hbox = g4.new_hbox(5)
		g4.grid_attach(table, hbox, 0, 1, 2, 3)
		
		label=g4.new_label(_("Year")+":")
		g4.box_pack(hbox, label, False, False, 0)

		self.dateY = Gtk.Entry()
		self.dateY.set_max_length(4)
		self.dateY.set_width_chars(4)
		self.dateY.set_text(str(g.astrology_chart.year_loc))
		g4.box_pack(hbox, self.dateY, False, False, 0)

		label=g4.new_label(_("Month")+":")
		g4.box_pack(hbox, label, False, False, 0)

		self.dateM = Gtk.Entry()
		self.dateM.set_max_length(2)
		self.dateM.set_width_chars(2)
		self.dateM.set_text('%(#)02d' % {'#':g.astrology_chart.month_loc})
		g4.box_pack(hbox, self.dateM, False, False, 0)

		label=g4.new_label("Day:")
		g4.box_pack(hbox, label, False, False, 0)

		self.dateD = Gtk.Entry()
		self.dateD.set_max_length(2)
		self.dateD.set_width_chars(2)
		self.dateD.set_text('%(#)02d' % {'#':g.astrology_chart.day_loc})
		g4.box_pack(hbox, self.dateD, False, False, 0)

		#dat entry (non editable)
		labelDateStr = str(g.astrology_chart.year_loc)+'-%(#1)02d-%(#2)02d' % {'#1':g.astrology_chart.month_loc,'#2':g.astrology_chart.day_loc}
		self.labelDate = g4.new_label(labelDateStr)
		g4.grid_attach(table, self.labelDate, 1, 2, 2, 3)

		#time entry (editable) (Hour, Minutes, Seconds, Timezone)
		hbox = g4.new_hbox(5)
		g4.grid_attach(table, hbox, 0, 1, 3, 4)

		label=g4.new_label(_("Hour")+":")
		g4.box_pack(hbox, label, False, False, 0)

		self.eH = Gtk.Entry()
		self.eH.set_max_length(2)
		self.eH.set_width_chars(2)
		self.eH.set_text('%(#)02d' % {'#':g.astrology_chart.hour_loc})
		g4.box_pack(hbox, self.eH, False, False, 0)

		label=g4.new_label(_("Min")+":")
		g4.box_pack(hbox, label, False, False, 0)

		self.eM = Gtk.Entry()
		self.eM.set_max_length(2)
		self.eM.set_width_chars(2)
		self.eM.set_text('%(#)02d' % {'#':g.astrology_chart.minute_loc})
		g4.box_pack(hbox, self.eM, False, False, 0)
		
		label=g4.new_label("Sec:")
		g4.box_pack(hbox, label, False, False, 0)
		
		self.eS = Gtk.Entry()
		self.eS.set_max_length(2)
		self.eS.set_width_chars(2)
		self.eS.set_text('%(#)02d' % {'#':g.astrology_chart.second_loc})
		g4.box_pack(hbox, self.eS, False, False, 0)
		
		#time entry (non editable)
		labelTzStr = '%(#1)02d:%(#2)02d:%(#3)02d' % {'#1':g.astrology_chart.hour_loc,'#2':g.astrology_chart.minute_loc,'#3':g.astrology_chart.second_loc} + g.astrology_chart.decTzStr(g.astrology_chart.timezone)
		self.labelTz = g4.new_label(labelTzStr)
		g4.grid_attach(table, self.labelTz, 1, 2, 3, 4)

		buttonbox = g4.dialog_action_area(self.window2)

		#save to database button
		if edit:
			self.savebutton = g4.button_new_stock(g4.STOCK_SAVE, _('Save'))
			self.savebutton.connect("clicked", self.openDatabaseEditAsk)
			g4.box_pack(buttonbox, self.savebutton, False, False, 0)
		else:
			self.savebutton = g4.new_button(_('Add to Database'))
			self.savebutton.connect("clicked", self.eventDataSaveAsk)
			g4.box_pack(buttonbox, self.savebutton, False, False, 0)


		#Test button
		button = g4.button_new_stock(g4.STOCK_APPLY, _('Test'))
		button.connect("clicked", self.eventDataApply)
		g4.box_pack(buttonbox, button, False, False, 0)
  		#ok button
		if edit == False:
			button = g4.button_new_stock(g4.STOCK_OK)
			button.connect("clicked", self.eventDataSubmit)
			#g4.button_set_can_default(button, True)
			g4.box_pack(buttonbox, button, False, False, 0)
			g4.button_set_can_default(button, True)
			g4.button_grab_default(button)
            
		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.window2.close())
		g4.box_pack(buttonbox, button, False, False, 0)
		
		self.window2.present()
		return
	def eventDataSaveAsk(self, widget):
		#check for duplicate name	
		en = g.db.getDatabase()
		for i in range(len(en)):
			if en[i]["name"] == self.name.get_text():
				dialog=g4.message_dialog(self.window2, _('Duplicate'), '')
				g4.window_set_icon(dialog, g.cfg.iconWindow)			
				dialog.connect("response", lambda w, *args: dialog.close())				
				dialog.connect("close", lambda w, *args: dialog.close())
				g4.box_pack(g4.dialog_content(dialog), g4.new_label(_('There is allready an entry for this name, please choose another')), True, True,0)
				dialog.present()				
				return
		#ask for confirmation
		dialog=g4.question_dialog(self.window2, _('Question'), '')
		dialog.set_destroy_with_parent(True)
		g4.window_set_icon(dialog, g.cfg.iconWindow)
		dialog.connect("close", lambda w, *args: dialog.close())
		dialog.connect("response",self.eventDataSave)
		g4.box_pack(g4.dialog_content(dialog), g4.new_label(_('Are you sure you want to save this entry to the database?')), True, True, 0)
		dialog.present()	
		return	
	
	def eventDataSave(self, widget, response_id):
		if response_id == Gtk.ResponseType.ACCEPT:
			#update chart data
			self.updateChartData()
			#set query to save
			#add data from event_natal table
			sql='INSERT INTO event_natal \
				(id,name,year,month,day,hour,geolon,geolat,altitude,location,timezone,notes,image,countrycode,geonameid,timezonestr,extra)\
				 VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
			tuple=(g.astrology_chart.name,g.astrology_chart.year,g.astrology_chart.month,g.astrology_chart.day,g.astrology_chart.hour,
				g.astrology_chart.geolon,g.astrology_chart.geolat,g.astrology_chart.altitude,g.astrology_chart.location,
				g.astrology_chart.timezone,'','',g.astrology_chart.countrycode,g.astrology_chart.geonameid,g.astrology_chart.timezonestr,'')
			g.db.pquery([sql],[tuple])
			dprint('saved to database: '+g.astrology_chart.name)
			self.updateUI()
			widget.close()		
		else:
			widget.close()
			dprint('rejected save to database')
		return

	def eventDataSubmit(self, widget):
		#check if no changes were made
		if self.name.get_text() == g.astrology_chart.name and \
		self.dateY.get_text() == str(g.astrology_chart.year_loc) and \
		self.dateM.get_text() == '%(#)02d' % {'#':g.astrology_chart.month_loc} and \
		self.dateD.get_text() == '%(#)02d' % {'#':g.astrology_chart.day_loc} and \
		self.eH.get_text() == '%(#)02d' % {'#':g.astrology_chart.hour_loc} and \
		self.eM.get_text() == '%(#)02d' % {'#':g.astrology_chart.minute_loc} and \
		self.eS.get_text() == '%(#)02d' % {'#':g.astrology_chart.second_loc}:
			if self.iconn and \
			self.geoCC.get_text() == g.astrology_chart.countrycode and \
			self.geoLoc.get_text() == g.astrology_chart.location.partition(',')[0]:
				#go ahead ;)				
				self.window2.close()
				return
		
		#apply data
		self.eventDataApply( widget )
		
		if self.geoLocFound:
			self.window2.close()
			#update history
			g.db.addHistory()
			self.updateUI()
			return
		else:
			return

	def eventDataApply(self, widget):
		#update chart data
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.type="Radix"
		g.astrology_chart.transit=False
		self.updateChartData()
		
		#update chart
		self.updateChart()
