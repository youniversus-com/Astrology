# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Primary application window and menus."""

import codecs
import datetime
import math
import os
import socket
import sys
import webbrowser
from shutil import copy2, copyfile
from urllib.error import URLError
from urllib.request import urlopen as url_open
from string import Template

from astrologymod.branding import APP_NAME, PROJECT_HOMEPAGE
from astrologymod.timezone_utils import localize_naive, naive_utc
from gi import require_version

require_version('Gtk', '4.0')
from gi.repository import Gdk, Gio, GLib, GObject, Gtk

from astrologymod import geoname, importfile, zonetab
from astrologymod import gtkcompat as g4
from astrologymod import swiss as ephemeris
from astrologymod.appmenu import MainMenu

from astrology_app.chart import AstrologyInstance
from astrology_app.config import AstrologyCfg
from astrology_app.db import AstrologySqlite
from astrology_app.debug import dprint
import astrology_app.globals as g
from astrology_app.i18n import LANGUAGES, LANGUAGES_LABEL, TRANSLATION
from astrology_app.export_image import (
	export_svg_to_raster,
	safe_chart_basename,
	try_convert_cli,
)
from astrology_app.menu_actions import resolve_export_kind, resolve_import_kind
from astrology_app.paths import DATADIR
from astrology_app.ui.chart_table_io import write_table_svg
from astrology_app.ui.draw_svg import AstrologyDrawSVG
from astrology_app.ui.event_editor import EventEditorMixin
from astrology_app.ui.geonames_handlers import GeonamesHandlersMixin
from astrology_app.ui.location_dialog import LocationDialogMixin
from astrologymod.validation import (
	validate_color_key,
	validate_hex_color,
	validate_label_key,
)

class AstrologyMainWindow(
	GeonamesHandlersMixin,
	EventEditorMixin,
	LocationDialogMixin,
):
	"""Primary application window: menus, dialogs, and chart viewport.

	Wires :class:`MainMenu` actions to chart/database/settings handlers and
	embeds :class:`AstrologyDrawSVG` in a scrolled area. Most user-facing workflows
	live as methods on this class.
	"""

	def _menu_tr(self, msg):
		"""Return a gettext-translated menu string."""
		return _(msg)

	def __init__(self, application=None):
		self.application = application
		self.window = Gtk.ApplicationWindow(application=application)
		self.window.set_title("Astrology")
		g4.window_set_icon(self.window, g.cfg.iconWindow)
		self.window.maximize()

		self.vbox = g4.new_vbox()
		self.menu = MainMenu(self.window, self)
		self.updateUI()
		self.tempfilename = g.cfg.tempfilename

		self.draw = AstrologyDrawSVG()
		self.draw.on_viewport_changed = self._on_chart_viewport_changed
		self._chart_viewport_idle = 0
		scrolledwindow = Gtk.ScrolledWindow()
		g4.scrolled_set_child(scrolledwindow, self.draw)
		scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
		g4.box_pack(self.vbox, scrolledwindow, expand=True, fill=True, padding=0)

		self.window.set_child(self.vbox)
		self.window.present()
		GLib.idle_add(self._initial_chart_refresh)
		
		#check if we need to ask for location
		if g.astrology_chart.ask_for_home and os.environ.get('ASTROLOGY_TEST') != '1':
			self.settingsLocation(self.window)
		
		#check internet connection
		self.checkInternetConnection()

		return

	"""

	'Extra' Menu Items Functions
	
	extraExportDB
	extraImportDB	
		
	"""
	
	def extraExportDB(self, widget):
		chooser = g4.file_chooser_dialog(self.window, None, Gtk.FileChooserAction.SAVE, g4.STOCK_SAVE)
		g4.chooser_set_folder(chooser, g.cfg.homedir)
		chooser.set_current_name('astrology-database.sql')
		filter = Gtk.FileFilter()
		filter.set_name(_("Astrology Databases (*.sql)"))
		filter.add_pattern("*.sql")
		chooser.add_filter(filter)
		response, path = g4.file_chooser_run(chooser)
		if response == Gtk.ResponseType.OK and path:
			copyfile(g.cfg.peopledb, path)
		elif response == Gtk.ResponseType.CANCEL:
			dprint('Dialog closed, no files selected')
	
	def extraImportDB(self, widget):
		chooser = g4.file_chooser_dialog(self.window, _("Please select database to import"), Gtk.FileChooserAction.OPEN, g4.STOCK_OPEN)
		g4.chooser_set_folder(chooser, g.cfg.homedir)
		filter = Gtk.FileFilter()
		filter.set_name(_("Astrology Databases (*.sql)"))
		filter.add_pattern("*.sql")
		chooser.add_filter(filter)
		response, path = g4.file_chooser_run(chooser)
		if response == Gtk.ResponseType.OK and path:
			backup = g.cfg.peopledb + '.bak'
			try:
				copy2(g.cfg.peopledb, backup)
				g.db.databaseMerge(g.cfg.peopledb, path)
			except ValueError as err:
				dlg = Gtk.AlertDialog(
					message=_('Database import failed'),
					detail=str(err),
				)
				dlg.show(self.window)
			except OSError as err:
				dlg = Gtk.AlertDialog(
					message=_('Database import failed'),
					detail=str(err),
				)
				dlg.show(self.window)
		elif response == Gtk.ResponseType.CANCEL:
			dprint('Dialog closed, no files selected')

	"""
	
	Function to check if we have an internet connection
	for geonames.org geocoder

	"""
	def checkInternetConnection(self):
		if g.db.getAstrocfg('use_geonames.org') == "0":
			self.iconn = False
			dprint('iconn: not using geocoding!')
			return
		try:
			url_open('https://api.geonames.org/', timeout=5)
			self.iconn = True
			dprint('iconn: got connection (https)')
		except (URLError, OSError, socket.timeout) as err:
			self.iconn = False
			dprint('iconn: no connection (%s)' % err)
		return

	def zoom(self, action, current):
		#check for zoom level
		if current.get_name() == 'z80':
			g.astrology_chart.zoom=0.8
		elif current.get_name() == 'z150':
			g.astrology_chart.zoom=1.5
		elif current.get_name() == 'z200':
			g.astrology_chart.zoom=2
		else:
			g.astrology_chart.zoom=1

		self.updateChart()
		return

		
	def _export_path_with_extension(self, path, ext):
		"""Ensure saved export path uses the extension for the chosen format."""
		base, _ = os.path.splitext(path)
		return base + ext

	def _export_failed_dialog(self, message):
		dialog = g4.message_dialog(
			self.window, _('Export failed'), message, Gtk.ButtonsType.OK)
		g4.dialog_run(dialog)

	def doExport(self, action_name):
		"""Export chart image or native ``.yac`` (menu: Export / Save Chart)."""
		action = resolve_export_kind(action_name)
		dialog_title = _('Save chart') if action == 'exportXML' else _('Export chart')
		chooser = g4.file_chooser_dialog(
			self.window, dialog_title, Gtk.FileChooserAction.SAVE, g4.STOCK_SAVE)
		g4.chooser_set_folder(chooser, g.cfg.homedir)
		safe_name = safe_chart_basename(g.astrology_chart.name)

		fmt_filter = Gtk.FileFilter()
		if action == 'exportPNG':
			chooser.set_current_name(safe_name + '.png')
			fmt_filter.set_name(_('PNG image (*.png)'))
			fmt_filter.add_mime_type('image/png')
			fmt_filter.add_pattern('*.png')
			default_ext = '.png'
		elif action == 'exportJPG':
			chooser.set_current_name(safe_name + '.jpg')
			fmt_filter.set_name(_('JPEG image (*.jpg)'))
			fmt_filter.add_mime_type('image/jpeg')
			fmt_filter.add_pattern('*.jpg')
			fmt_filter.add_pattern('*.jpeg')
			default_ext = '.jpg'
		elif action == 'exportSVG':
			chooser.set_current_name(safe_name + '.svg')
			fmt_filter.set_name(_('SVG image (*.svg)'))
			fmt_filter.add_mime_type('image/svg+xml')
			fmt_filter.add_pattern('*.svg')
			default_ext = '.svg'
		else:
			action = 'exportXML'
			chooser.set_current_name(safe_name + '.yac')
			fmt_filter.set_name(_('Astrology chart (*.yac)'))
			fmt_filter.add_mime_type('application/xml')
			fmt_filter.add_pattern('*.yac')
			default_ext = '.yac'

		chooser.add_filter(fmt_filter)
		chooser.set_filter(fmt_filter)
		all_filter = Gtk.FileFilter()
		all_filter.set_name(_('All files'))
		all_filter.add_pattern('*')
		chooser.add_filter(all_filter)

		response, chosen = g4.file_chooser_run(chooser)
		if response != Gtk.ResponseType.OK:
			dprint('Export dialog closed, no file selected')
			return
		if not chosen:
			self._export_failed_dialog(
				_('No file path was selected. Please try again.'))
			return
		path = self._export_path_with_extension(chosen, default_ext)
		try:
			g.astrology_chart.makeSVG()
			if action == 'exportSVG':
				copyfile(g.cfg.tempfilename, path)
			elif action in ('exportPNG', 'exportJPG'):
				try:
					export_svg_to_raster(g.cfg.tempfilename, path)
				except Exception as err:
					dprint('Raster export via librsvg failed: %s' % err)
					if not try_convert_cli(g.cfg.tempfilename, path):
						raise
			elif action == 'exportXML':
				g.astrology_chart.exportOAC(path)
			if not os.path.isfile(path) or os.path.getsize(path) < 1:
				raise OSError(_('The file was not written.'))
			dprint('Exported chart to %s' % path)
		except Exception as err:
			dprint('Export failed: %s' % err)
			self._export_failed_dialog(
				_('Could not write the file:\n%s\n\n%s') % (path, err))
		return
	
	def doImport(self, action_name):
		"""Open a chart file (native ``.yac`` or external import formats)."""
		action = resolve_import_kind(action_name)
		chooser = g4.file_chooser_dialog(
			self.window, _('Open chart'), Gtk.FileChooserAction.OPEN, g4.STOCK_OPEN)
		g4.chooser_set_folder(chooser, g.cfg.homedir)

		fmt_filter = Gtk.FileFilter()
		if action == 'importOroboros':
			fmt_filter.set_name(_('Oroboros chart (*.xml)'))
			fmt_filter.add_pattern('*.xml')
		elif action == 'importSkylendar':
			fmt_filter.set_name(_('Skylendar chart (*.skif)'))
			fmt_filter.add_pattern('*.skif')
		elif action == 'importAstrolog32':
			fmt_filter.set_name(_('Astrolog chart (*.dat)'))
			fmt_filter.add_pattern('*.dat')
		elif action == 'importZet8':
			fmt_filter.set_name(_('Zet8 database (*.zbs)'))
			fmt_filter.add_pattern('*.zbs')
		else:
			action = 'importXML'
			fmt_filter.set_name(_('Astrology chart (*.yac)'))
			fmt_filter.add_pattern('*.yac')

		chooser.add_filter(fmt_filter)
		chooser.set_filter(fmt_filter)
		all_filter = Gtk.FileFilter()
		all_filter.set_name(_('All files'))
		all_filter.add_pattern('*')
		chooser.add_filter(all_filter)

		response, path = g4.file_chooser_run(chooser)
		if response == Gtk.ResponseType.OK and path:
			if action == 'importXML':
				g.astrology_chart.importOAC(path)
			elif action == 'importOroboros':
				g.astrology_chart.importOroboros(path)
			elif action == 'importSkylendar':
				g.astrology_chart.importSkylendar(path)
			elif action == 'importAstrolog32':
				g.astrology_chart.importAstrolog32(path)
			elif action == 'importZet8':
				g.astrology_chart.importZet8(path)
			self.updateChart()
		elif response == Gtk.ResponseType.CANCEL:
			dprint('Open dialog closed, no file selected')
		return
	
	def specialRadix(self, widget):
		g.astrology_chart.type="Radix"
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.transit=False
		g.astrology_chart.makeSVG()
		self.draw.queue_draw()
		self.draw.setSVG(self.tempfilename)
			
	def specialTransit(self, widget):
		g.astrology_chart.type="Transit"
		g.astrology_chart.t_geolon=float(g.astrology_chart.home_geolon)
		g.astrology_chart.t_geolat=float(g.astrology_chart.home_geolat)
		
		now = datetime.datetime.now()
		timezone_str = zonetab.nearest_tz(g.astrology_chart.t_geolat,g.astrology_chart.t_geolon,zonetab.timezones())[2]
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = localize_naive(dt_input, timezone_str)
		#naive utc datetime object
		dt_utc = naive_utc(dt)
		#transit data
		g.astrology_chart.t_year=dt_utc.year
		g.astrology_chart.t_month=dt_utc.month
		g.astrology_chart.t_day=dt_utc.day
		g.astrology_chart.t_hour=g.astrology_chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		g.astrology_chart.t_timezone=g.astrology_chart.offsetToTz(dt.utcoffset())
		g.astrology_chart.t_altitude=25

		#make svg with transit
		g.astrology_chart.charttype="%s (%s-%02d-%02d %02d:%02d)" % (g.astrology_chart.label["transit"],dt.year,dt.month,dt.day,dt.hour,dt.minute)
		g.astrology_chart.transit=True
		g.astrology_chart.makeSVG()
		self.draw.queue_draw()
		self.draw.setSVG(self.tempfilename)	

	def specialSolar(self, widget):
		# create a new window
		self.win_SS = g4.new_dialog()
		g4.window_set_icon(self.win_SS, g.cfg.iconWindow)
		self.win_SS.set_title(_("Select year for Solar Return"))
		self.win_SS.connect("close-request", lambda w, *args: self.win_SS.close())
		self.win_SS.set_margin_start(5); self.win_SS.set_margin_end(5)
		self.win_SS.set_size_request(300,100)
		
		#create a table
		table = g4.new_table(2, 1, False)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		table.set_margin_start(10)

		#options
		g4.grid_attach(table, g4.new_label(_("Select year for Solar Return")), 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		entry=Gtk.Entry()
		entry.set_max_length(4)
		entry.set_width_chars(4) 
		entry.set_text(str(datetime.datetime.now().year))
		g4.grid_attach(table, entry, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		
		#make the ui layout with ok button
		g4.box_pack(g4.dialog_content(self.win_SS), table, True, True, 0)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.specialSolarSubmit, entry)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_SS), button, True, True, 0)
		g4.button_grab_default(button)		

		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SS.close())
		g4.box_pack(g4.dialog_action_area(self.win_SS), button, True, True, 0)

		self.win_SS.present()
		return
	
	def specialSolarSubmit(self, widget, entry):
		intyear = int(entry.get_text())
		g.astrology_chart.localToSolar(intyear)
		self.win_SS.close()
		self.updateChart()
		return
	
	def specialSecondaryProgression(self, widget):
		# create a new window
		self.win_SSP = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.win_SSP, g.cfg.iconWindow)
		self.win_SSP.set_title(_("Enter Date"))
		self.win_SSP.connect("close-request", lambda w, *args: self.win_SSP.close())
		self.win_SSP.set_margin_start(5); self.win_SSP.set_margin_end(5)
		self.win_SSP.set_size_request(320,180)
		
		#create a table
		table = g4.new_table(1, 4, False)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		table.set_margin_start(10)

		#options
		g4.grid_attach(table, g4.new_label(_("Select date for Secondary Progression")+":"), 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10, ypadding=10)
		hbox = g4.new_hbox(spacing=4)  # pack_start(child, expand=True, fill=True, padding=0)
		entry={}
		
		g4.box_pack(hbox, g4.new_label(_('Year')+": "), False, False, 0)	
		entry['Y']=Gtk.Entry()
		entry['Y'].set_max_length(4)
		entry['Y'].set_width_chars(4) 
		entry['Y'].set_text(str(datetime.datetime.now().year))
		g4.box_pack(hbox, entry['Y'], False, False, 0)
		g4.box_pack(hbox, g4.new_label(_('Month')+": "), False, False, 0)	
		entry['M']=Gtk.Entry()
		entry['M'].set_max_length(2)
		entry['M'].set_width_chars(2) 
		entry['M'].set_text('%02d'%(datetime.datetime.now().month))
		g4.box_pack(hbox, entry['M'], False, False, 0)
		g4.box_pack(hbox, g4.new_label(_('Day')+": "), False, False, 0)	
		entry['D']=Gtk.Entry()
		entry['D'].set_max_length(2)
		entry['D'].set_width_chars(2) 
		entry['D'].set_text(str(datetime.datetime.now().day))
		g4.box_pack(hbox, entry['D'], False, False, 0)	
		g4.grid_attach(table, hbox,0,1,1,2, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10, ypadding=10)
		
		hbox = g4.new_hbox(spacing=4)
		g4.box_pack(hbox, g4.new_label(_('Hour')+": "), False, False, 0)	
		entry['h']=Gtk.Entry()
		entry['h'].set_max_length(2)
		entry['h'].set_width_chars(2) 
		entry['h'].set_text('%02d'%(datetime.datetime.now().hour))
		g4.box_pack(hbox, entry['h'], False, False, 0)
		g4.box_pack(hbox, g4.new_label(_('Min')+": "), False, False, 0)	
		entry['m']=Gtk.Entry()
		entry['m'].set_max_length(2)
		entry['m'].set_width_chars(2) 
		entry['m'].set_text('%02d'%(datetime.datetime.now().minute))
		g4.box_pack(hbox, entry['m'], False, False, 0)
		g4.grid_attach(table, hbox,0,1,2,3, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10, ypadding=10)
		
		#make the ui layout with ok button
		g4.box_pack(g4.dialog_content(self.win_SSP), table, True, True, 0)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.specialSecondaryProgressionSubmit, entry)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_SSP), button, True, True, 0)
		g4.button_grab_default(button)		

		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SSP.close())
		g4.box_pack(g4.dialog_action_area(self.win_SSP), button, True, True, 0)

		self.win_SSP.present()
		return

	def specialSecondaryProgressionSubmit(self, widget, entry):
		dt	= datetime.datetime(int(entry['Y'].get_text()),int(entry['M'].get_text()),int(entry['D'].get_text()),int(entry['h'].get_text()),int(entry['m'].get_text()))
		g.astrology_chart.localToSecondaryProgression(dt)
		self.win_SSP.close()
		self.updateChart()
		return
	
	def tableMonthlyTimeline(self, widget):
		# Ensure natal positions exist for aspect comparison
		if not hasattr(g.astrology_chart, 'planets_degree_ut'):
			g.astrology_chart.makeSVG()

		dialog = g4.new_dialog(transient_for=self.window, title=_("Select Month"))
		dialog.add_button(g4.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(g4.STOCK_OK, Gtk.ResponseType.OK)
		dialog.set_destroy_with_parent(True)
		dialog.connect("close-request", lambda w, *args: dialog.close())
		dialog.set_default_size(280, 160)
		content = g4.dialog_content(dialog)
		entry_y = Gtk.Entry()
		entry_y.set_max_length(4)
		entry_y.set_width_chars(6)
		entry_y.set_text(str(datetime.datetime.now().year))
		entry_m = Gtk.Entry()
		entry_m.set_max_length(2)
		entry_m.set_width_chars(4)
		entry_m.set_text('%02d' % datetime.datetime.now().month)

		row_y = g4.new_hbox(spacing=8)
		g4.box_pack(row_y, g4.new_label(_('Year') + ':'), False, False, 0)
		g4.box_pack(row_y, entry_y, True, True, 0)
		g4.box_pack(content, row_y, False, False, 0)
		row_m = g4.new_hbox(spacing=8)
		g4.box_pack(row_m, g4.new_label(_('Month') + ':'), False, False, 0)
		g4.box_pack(row_m, entry_m, True, True, 0)
		g4.box_pack(content, row_m, False, False, 0)

		# Keep dialog open until year/month are read (dialog_run must not destroy entries)
		ret = g4.dialog_run(dialog, close_on_response=False)
		if ret in (Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT):
			self.tMTentry = {
				'Y': entry_y.get_text().strip(),
				'M': entry_m.get_text().strip(),
			}
			dialog.close()
			try:
				self.tableMonthlyTimelineShow()
			except Exception:
				import traceback
				traceback.print_exc()
				g4.message_dialog(
					self.window,
					_('Timeline error'),
					_('Could not build the monthly timeline table. See terminal for details.'),
				).present()
		else:
			dialog.close()
		return

	def tableMonthlyTimelinePrint(self, pages, pdf, window, name):
		settings = None
		print_op = Gtk.PrintOperation()
		print_op.set_unit(Gtk.Unit.MM)
		if settings != None: 
			print_op.set_print_settings(settings)
		print_op.connect("begin_print", self.tableMonthlyTimelinePrintBegin, pages)
		print_op.connect("draw_page", self.tableMonthlyTimelinePrintDraw)

		if pdf:
			chooser = g4.file_chooser_dialog(self.window, _("Select Export Filename"), Gtk.FileChooserAction.SAVE, g4.STOCK_SAVE)
			g4.chooser_set_folder(chooser, g.cfg.homedir)
			g4.chooser_set_folder(chooser, g.cfg.homedir)
			chooser.set_current_name(name)
			filter = Gtk.FileFilter()
			filter.set_name(_("PDF Files (*.pdf)"))
			filter.add_pattern("*.pdf")
			chooser.add_filter(filter)
			response, path = g4.file_chooser_run(chooser)
			if response == Gtk.ResponseType.OK and path:
				print_op.set_export_filename(path)
				res = print_op.run(Gtk.PrintOperationAction.EXPORT, window)
			else:
				print_op.cancel()
				res = None
			
		else:
			res = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, window)		

		if res == Gtk.PrintOperationResult.ERROR:
			error_dialog = Gtk.MessageDialog(window,0,Gtk.MESSAGE_ERROR,Gtk.ButtonS_CLOSE,"Error printing:\n")
			error_dialog.set_destroy_with_parent(True)
			error_dialog.connect("response", lambda w, *args: w.close())
			error_dialog.show()
		elif res == Gtk.PrintOperationResult.APPLY:
			settings = print_op.get_print_settings()


	def tableMonthlyTimelinePrintBegin(self, operation, context, pages):
		operation.set_n_pages(pages)
		operation.set_use_full_page(False)
		ps = Gtk.PageSetup()
		ps.set_orientation(Gtk.PageOrientation.PORTRAIT)
		ps.set_paper_size(Gtk.PaperSize(Gtk.PAPER_NAME_A4))
		operation.set_default_page_setup(ps)
	
	def tableMonthlyTimelinePrintDraw(self, operation, context, page_nr):
		cr = context.get_cairo_context()
		#draw svg
		printing={}
		printing['pagenum']=page_nr
		printing['width']=context.get_width()
		printing['height']=context.get_height()
		printing['dpi_x']=context.get_dpi_x()
		printing['dpi_y']=context.get_dpi_y()
		if(self.tabletype == "timeline"):
			self.tableMonthlyTimelineShow(printing)
			#draw svg for printing
			Rsvg.set_default_dpi(900)
			svg = Rsvg.Handle.new_from_file(g.cfg.tempfilenametableprint)
			svg.render_cairo(cr)
		elif(self.tabletype == "cuspaspects"):
			self.tableCuspAspects(None,printing)
			#draw svg for printing
			Rsvg.set_default_dpi(900)
			svg = Rsvg.Handle.new_from_file(g.cfg.tempfilenametableprint)
			svg.render_cairo(cr)		


	def tableMonthlyTimelineShow(self, printing=None):
		self.tabletype="timeline"
		y = int(self.tMTentry['Y'])
		m = int(self.tMTentry['M'])
		tz = datetime.timedelta(seconds=float(g.astrology_chart.timezone)*float(3600))
		startdate = datetime.datetime(y,m,1,12) - tz
		q,r = divmod(startdate.month, 12)
		enddate = datetime.datetime(startdate.year+q, r+1, 1,12)
		delta = enddate - startdate
		atgrid={}
		astypes={}
		retrogrid={}
		for d in range(delta.days):
			cdate = startdate + datetime.timedelta(days=d)
			tmoddata = ephemeris.ephData(cdate.year,cdate.month,cdate.day,cdate.hour,
				g.astrology_chart.geolon,g.astrology_chart.geolat,g.astrology_chart.altitude,g.astrology_chart.planets,
				g.astrology_chart.zodiac,g.db.astrocfg)
			#planets_sign,planets_degree,planets_degree_ut,planets_retrograde,houses_degree
			#houses_sign,houses_degree_ut

			for i in range(len(g.astrology_chart.planets)):
				start=g.astrology_chart.planets_degree_ut[i]
				for x in range(i+1):
					end=tmoddata.planets_degree_ut[x]
					diff=float(g.astrology_chart.degreeDiff(start,end))
					#skip asc/dsc/mc/ic on tmoddata
					if 23 <= x <= 26:
						continue
					#skip moon on tmoddate
					if x == 1:
						continue
					#loop orbs
					if int(g.astrology_chart.planets[i].get('visible', 0)) and int(g.astrology_chart.planets[x].get('visible', 0)):	
						for z in range(len(g.astrology_chart.aspects)):
							#only major aspects
							if int(g.astrology_chart.aspects[z].get('is_major', 0)) != 1:
								continue
							#check for personal planets and determine orb
							orb_before = 4
							orb_after = 4
							#check if we want to display this aspect	
							if	( float(g.astrology_chart.aspects[z]['degree']) - orb_before ) <= diff <= ( float(g.astrology_chart.aspects[z]['degree']) + orb_after ):
								orb = diff - g.astrology_chart.aspects[z]['degree']
								if orb < 0:
									orb = orb/-1						
								#aspect grid dictionary
								s="%02d%02d%02d"%(i,z,x)
								astypes[s]=(i,x,z)
								
								if s not in retrogrid:
									retrogrid[s]={}
								retrogrid[s][d]=tmoddata.planets_retrograde[x]
									
								if s not in atgrid:
									atgrid[s]={}
								atgrid[s][d]=orb
		#sort
		keys = list(astypes.keys())
		keys.sort()
		pages = int(math.ceil(len(keys)/65.0))
		
		out = ""
		#make numbers of days in month
		dx=[80]
		skipdays = [9,19]
		for d in range(delta.days):
			if d in skipdays:
				dx.append(dx[-1]+40)
			else:
				dx.append(dx[-1]+20)	
		
		for p in range(pages):
			if p == 0:
				ystart = 10
			else:
				ystart = (1188 * p) + 62
			pagelen = (len(keys)+1)-p*65
			if pagelen > 65:
				pagelen = 66
			ylen = ((len(keys)+1)-p*65)*16	
			for a in range(delta.days):
				out += '<text x="%s" y="%s" style="fill: %s; font-size: 10">%02d</text>\n'%(
					dx[a],ystart,g.astrology_chart.colors['paper_0'],a+1)
				out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
					dx[a]-5,ystart,dx[a]-5,ystart+pagelen*16,g.astrology_chart.colors['paper_0'])	
				#skipdays line
				if a in skipdays:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[a]-5+20,ystart,dx[a]-5+20,ystart+pagelen*16,g.astrology_chart.colors['paper_0'])						
				

			#last line
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
					dx[-1]-5,ystart,dx[-1]-5,ystart+pagelen*16,g.astrology_chart.colors['paper_0'])
					
		#get the number of total aspects
		c = 0
		for m in range(len(keys)):
			i,x,z = astypes[keys[m]]
			c += 1
			pagenum = int(math.ceil(c/65.0))
			pagey = (pagenum - 1) * 200
			y = (c*16) + pagey
			#horizontal lines
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
				0,y-1,dx[skipdays[0]]+15,y-1,g.astrology_chart.colors['paper_0'])
			for s in range(len(skipdays)):
				if s is len(skipdays)-1:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[skipdays[s]+1]-5,y-1,dx[-1],y-1,g.astrology_chart.colors['paper_0'])
				else:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[skipdays[s]+1]-5,y-1,dx[skipdays[s+1]]+15,y-1,g.astrology_chart.colors['paper_0'])
			#outer planet
			out += '<g transform="translate(0,%s)"><g transform="scale(.5)"><use x="0" y="0" xlink:href="#%s" /></g></g>\n'%(
				y,g.astrology_chart.svgSafeHref(g.astrology_chart.planets[x]['name']))
			#aspect
			out += '<g><use x="20" y="%s" xlink:href="#orb%s" /></g>\n'%(
				y,g.astrology_chart.aspects[z]['degree'])			
			#inner planet
			out += '<g transform="translate(40,%s)"><g transform="scale(.5)"><use x="0" y="0" xlink:href="#%s" /></g></g>\n'%(y,
				g.astrology_chart.svgSafeHref(g.astrology_chart.planets[i]['name']))		
			for d in range(delta.days):					
				if d in atgrid[keys[m]]:
					orb = atgrid[keys[m]][d]
					op = .1+(.7-(orb/(4/.7))) #4 is maxorb
					if op > 1:
						op = 1
					strop = str(float(orb))
					out += '<rect x="%s" y="%s" width="20" height="16" style="fill: %s; fill-opacity:%s;" />'%(
						dx[d]-5,y-1,g.astrology_chart.colors["aspect_%s" %(g.astrology_chart.aspects[z]['degree'])],op)
					#check for retrograde outer planet
					if retrogrid[keys[m]][d]:
						out += '<g transform="translate(%s,%s)"><g transform="scale(.3)">\
							<use x="0" y="0" xlink:href="#retrograde" style="fill:%s; fill-opacity:.8;" /></g></g>\n'%(
							dx[d]+10,y+10,g.astrology_chart.colors['paper_0'],)							
					out += '<text x="%s" y="%s" style="fill: %s; font-size: 10">%s</text>\n'%(
						dx[d],y+9,g.astrology_chart.colors['paper_0'],strop[:3])
							
				else:
					out += ""

		#template
		td = {}
		td['paper_color_0']=g.astrology_chart.colors["paper_0"]
		td['paper_color_1']=g.astrology_chart.colors["paper_1"]
		for i in range(len(g.astrology_chart.planets)):
			td['planets_color_%s'%(i)]=g.astrology_chart.colors["planet_%s"%(i)]
		for i in range(12):
			td['zodiac_color_%s'%(i)]=g.astrology_chart.colors["zodiac_icon_%s" %(i)]
		for i in range(len(g.astrology_chart.aspects)):
			td['orb_color_%s'%(g.astrology_chart.aspects[i]['degree'])]=g.astrology_chart.colors["aspect_%s" %(g.astrology_chart.aspects[i]['degree'])]
		td['stringTitle'] = "%s Timeline for %s"%(
			startdate.strftime("%B %Y"),g.astrology_chart.name)
			
		pagesY = (1188 * pages)+10 #ten is buffer between pages
		if printing:
			td['svgWidth'] = printing['width']
			td['svgHeight'] = printing['height']
			td['viewbox'] = "0 %s 840 1188" %( printing['pagenum']*(1188+10) )
		else:
			td['svgWidth'] = 1050
			td['svgHeight'] = (td['svgWidth']/840.0)* pagesY
			td['viewbox'] = "0 0 840 %s" %( pagesY ) 
		

		td['data'] = out
		
		#pages rectangles
		pagesRect,x,y,w,h="",0,0,840,1188
		for p in range(pages):
			if p == 0:
				offset=0
			else:
				offset=10
			pagesRect += '<rect x="%s" y="%s" width="%s" height="%s" style="fill: %s;" />'%(
				x,y+(p*1188)+offset,w,h,g.astrology_chart.colors['paper_1'],)
				
		td['pagesRect'] = pagesRect
				
		write_table_svg(
			g.cfg.xml_svg_table,
			g.cfg.tempfilenametable,
			g.cfg.tempfilenametableprint,
			printing,
			td,
		)

		if printing == None:
			self.win_TMT = Gtk.Window(transient_for=self.window)
			self.win_TMT.connect("destroy", lambda w: self.win_TMT.close())
			self.win_TMT.set_title("Astrology Timeline")
			g4.window_set_icon(self.win_TMT, g.cfg.iconWindow)
			self.win_TMT.set_size_request(td['svgWidth']+30, 700)
			vbox = g4.new_vbox()
			hbox = g4.new_hbox()
			button = g4.new_button(_('Print'))
			button.connect("clicked", lambda w: self.tableMonthlyTimelinePrint(pages,pdf=False,window=self.win_TMT,name="timeline-%s.pdf"%(g.astrology_chart.name)))
			g4.box_pack(hbox, button, False, False, 0)
			button = g4.new_button(_('Save as PDF'))
			button.connect("clicked", lambda w: self.tableMonthlyTimelinePrint(pages,pdf=True,window=self.win_TMT,name="timeline-%s.pdf"%(g.astrology_chart.name)))
			g4.box_pack(hbox, button, False, False, 0)
			g4.box_pack(vbox, hbox, False, False, 0)
			draw = AstrologyDrawSVG()
			draw.setSVG(g.cfg.tempfilenametable)
			scrolledwindow = Gtk.ScrolledWindow()
			g4.scrolled_set_child(scrolledwindow, draw)
			scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
			g4.box_pack(vbox, scrolledwindow, True, True, 0)
		
			self.win_TMT.set_child(vbox)
			self.win_TMT.present()
		return

	def tableCuspAspects(self, widget, printing=None):
		self.tabletype="cuspaspects"
		#data
		out='<g transform="scale(1.5)">'
		xindent=50
		yindent=200
		box=14
		style='stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none' % (g.astrology_chart.colors['paper_0'],)
		textstyle="font-size: 11px; color: %s" % (g.astrology_chart.colors['paper_0'],)
		#draw cusps
		for cusp in range(len(g.astrology_chart.houses_degree_ut)):
				x = xindent - box
				y = yindent - (box*(cusp+1))
				out += '<text \
						x="%s" \
						y="%s" \
						style="%s">%s</text>\n\
						'%(x-30, y+box-5, textstyle, g.astrology_chart.label['cusp']+" "+str(cusp+1))
									
		revr=range(len(g.astrology_chart.planets))
		for a in revr:
			if 23 <= a <= 26:
				continue; #skip asc/dsc/mc/ic
			if a == 11 or a == 13 or a == 21 or a == 22:
				continue; #skip ?,?,intp. apogee, intp. perigee
				
			start=g.astrology_chart.planets_degree_ut[a]
			#first planet 
			out += '<rect x="%s" \
						y="%s" \
						width="%s" \
						height="%s" \
						style="%s"/>\n' %(xindent,yindent,box,box,style)
			out += '<use transform="scale(0.4)" \
					x="%s" \
					y="%s" \
					xlink:href="#%s" />\n\
					'%((xindent+2)*2.5, (yindent+1)*2.5, g.astrology_chart.planets[a]['name'])
		
			yorb=yindent - box
			for b in range(12):
				end=g.astrology_chart.houses_degree_ut[b]
				diff=g.astrology_chart.degreeDiff(start,end)
				out += '<rect x="%s" \
					y="%s" \
					width="%s" \
					height="%s" \
					style="%s"/>\n\
					'%(xindent,yorb,box,box,style)
				for z in range(len(g.astrology_chart.aspects)):
					if	( float(g.astrology_chart.aspects[z]['degree']) - float(g.astrology_chart.aspects[z]['orb']) ) <= diff <= ( float(g.astrology_chart.aspects[z]['degree']) + float(g.astrology_chart.aspects[z]['orb']) ) and g.astrology_chart.aspects[z]['visible_grid'] == 1:
							out += '<use \
								x="%s" \
								y="%s" \
								xlink:href="#orb%s" />\n\
								'%(xindent,yorb+1,g.astrology_chart.aspects[z]['degree'])
				yorb=yorb-box
				
			xindent += box
				
		#add cusp to cusp
		xindent = 50
		yindent = 400
		#draw cusps
		for cusp in range(len(g.astrology_chart.houses_degree_ut)):
				x = xindent - box
				y = yindent - (box*(cusp+1))
				out += '<text \
						x="%s" \
						y="%s" \
						style="%s">%s</text>\n\
						'%(x-30, y+box-5, textstyle, g.astrology_chart.label['cusp']+" "+str(cusp+1))

		for a in range(12):
			start=g.astrology_chart.houses_degree_ut[a]
			#first planet 
			out += '<rect x="%s" \
						y="%s" \
						width="%s" \
						height="%s" \
						style="%s"/>\n' %(xindent,yindent,box,box,style)
			out += '<text \
						x="%s" \
						y="%s" \
						style="%s">%s</text>\n\
						'%((xindent+2), (yindent+box-4), textstyle, ""+str(a+1))
		
			yorb=yindent - box
			for b in range(12):
				end=g.astrology_chart.houses_degree_ut[b]
				diff=g.astrology_chart.degreeDiff(start,end)
				out += '<rect x="%s" \
					y="%s" \
					width="%s" \
					height="%s" \
					style="%s"/>\n\
					'%(xindent,yorb,box,box,style)
				for z in range(len(g.astrology_chart.aspects)):
					if	( float(g.astrology_chart.aspects[z]['degree']) - float(g.astrology_chart.aspects[z]['orb']) ) <= diff <= ( float(g.astrology_chart.aspects[z]['degree']) + float(g.astrology_chart.aspects[z]['orb']) ) and g.astrology_chart.aspects[z]['visible_grid'] == 1:
							out += '<use \
								x="%s" \
								y="%s" \
								xlink:href="#orb%s" />\n\
								'%(xindent,yorb+1,g.astrology_chart.aspects[z]['degree'])
				yorb=yorb-box
				
			xindent += box	
			
		out += "</g>"
			
						
		#template
		td = {}
		td['paper_color_0']=g.astrology_chart.colors["paper_0"]
		td['paper_color_1']=g.astrology_chart.colors["paper_1"]
		for i in range(len(g.astrology_chart.planets)):
			td['planets_color_%s'%(i)]=g.astrology_chart.colors["planet_%s"%(i)]
		for i in range(12):
			td['zodiac_color_%s'%(i)]=g.astrology_chart.colors["zodiac_icon_%s" %(i)]
		for i in range(len(g.astrology_chart.aspects)):
			td['orb_color_%s'%(g.astrology_chart.aspects[i]['degree'])]=g.astrology_chart.colors["aspect_%s" %(g.astrology_chart.aspects[i]['degree'])]
		td['stringTitle'] = "Cusp Aspects for %s"%(g.astrology_chart.name)
		
		pages=1
		pagesY = (1188 * pages)+10 #ten is buffer between pages
		if printing:
			td['svgWidth'] = printing['width']
			td['svgHeight'] = printing['height']
			td['viewbox'] = "0 %s 840 1188" %( printing['pagenum']*(1188+10) )
		else:
			td['svgWidth'] = 1050
			td['svgHeight'] = (td['svgWidth']/840.0)* pagesY
			td['viewbox'] = "0 0 840 %s" %( pagesY ) 

		td['data'] = out
		td['pagesRect'] = '<rect x="0" y="0" width="840" height="1188" style="fill: %s;" />' % (g.astrology_chart.colors['paper_1'],)
		
		write_table_svg(
			g.cfg.xml_svg_table,
			g.cfg.tempfilenametable,
			g.cfg.tempfilenametableprint,
			printing,
			td,
		)

		if printing == None:
			self.win_TCA = Gtk.Window()
			self.win_TCA.connect("destroy", lambda w: self.win_TCA.close())
			self.win_TCA.set_title("Astrology Cusp Aspects")
			g4.window_set_icon(self.win_TCA, g.cfg.iconWindow)
			self.win_TCA.set_size_request(td['svgWidth']+30, 700)
			vbox = g4.new_vbox()
			hbox = g4.new_hbox()
			button = g4.new_button(_('Print'))
			button.connect("clicked", lambda w: self.tableMonthlyTimelinePrint(pages=1,pdf=False,window=self.win_TCA,name="cusp-aspects-%s.pdf"%(g.astrology_chart.name)))
			g4.box_pack(hbox, button, False, False, 0)
			button = g4.new_button(_('Save as PDF'))
			button.connect("clicked", lambda w: self.tableMonthlyTimelinePrint(pages=1,pdf=True,window=self.win_TCA,name="cusp-aspects-%s.pdf"%(g.astrology_chart.name)))
			g4.box_pack(hbox, button, False, False, 0)
			g4.box_pack(vbox, hbox, False, False, 0)
			draw = AstrologyDrawSVG()
			draw.setSVG(g.cfg.tempfilenametable)
			scrolledwindow = Gtk.ScrolledWindow()
			g4.scrolled_set_child(scrolledwindow, draw)
			scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
			g4.box_pack(vbox, scrolledwindow, True, True, 0)
			self.win_TCA.set_child(vbox)
			self.win_TCA.present()		
		return
		
	def showVedicReport(self, widget):
		"""Open Vedic astrology report (vargas, dashas, yogas, charts)."""
		from astrology_app.ui.vedic_panel import show_vedic_panel
		if g.db.astrocfg.get('tradition') != 'vedic':
			dialog = g4.message_dialog(
				self.window,
				_('Vedic Astrology'),
				_('Set Tradition to Vedic (Jyotish) in Settings → Configuration, then recalculate.'),
			)
			dialog.connect('response', lambda w, *a: dialog.close())
			dialog.present()
			return
		g.astrology_chart.makeSVG()
		show_vedic_panel(self.window)

	def aboutInfo(self, widget):
		dialog=g4.message_dialog(self.window, 'Info', '')
		g4.window_set_icon(dialog, g.cfg.iconWindow)
		dialog.connect("response", lambda w, *args: dialog.close())				
		dialog.connect("close", lambda w, *args: dialog.close())
		about_text = (
			_('Astrology') + '\n\n'
			+ _('Version') + ' ' + g.cfg.version + '\n'
			+ APP_NAME + '\n'
			+ PROJECT_HOMEPAGE
		)
		g4.box_pack(g4.dialog_content(dialog), g4.new_label(label=about_text), True, True, 0)
		dialog.present()
		return

	def openDatabaseFamous(self, widget):
		self.openDatabase(widget,g.db.getDatabaseFamous(limit="500"))

	def nameSearch(self, widget):
		self.listmodel.clear()
		self.DB = g.db.getDatabaseFamous(limit="15",search=self.namesearch.get_text())
		for i in range(len(self.DB)):
			h,m,s = g.astrology_chart.decHour(float(self.DB[i]["hour"]))
			dt_utc=datetime.datetime(int(self.DB[i]["year"]),int(self.DB[i]["month"]),int(self.DB[i]["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(self.DB[i]["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}			
			self.listmodel.append([self.DB[i]["name"],birth_date,self.DB[i]["location"],self.DB[i]["id"]])
		return		

	def nameSearchReset(self, widget):
		self.listmodel.clear()
		self.DB = g.db.getDatabaseFamous(limit="500")
		for i in range(len(self.DB)):
			h,m,s = g.astrology_chart.decHour(float(self.DB[i]["hour"]))
			dt_utc=datetime.datetime(int(self.DB[i]["year"]),int(self.DB[i]["month"]),int(self.DB[i]["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(self.DB[i]["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}			
			self.listmodel.append([self.DB[i]["name"],birth_date,self.DB[i]["location"],self.DB[i]["id"]])
		return		
			
	def openDatabase(self, widget, extraDB=None):
		self.win_OD = Gtk.Window()
		g4.window_set_icon(self.win_OD, g.cfg.iconWindow)
		self.win_OD.set_title(_('Open Database Entry'))
		self.win_OD.set_size_request(600, 450)
		self.win_OD
		self.win_OD.connect("close-request", lambda w, *args: self.win_OD.close())
		#listmodel		
		self.listmodel = Gtk.ListStore(str,str,str,int)	
		self.win_OD_treeview = g4.new_treeview(self.listmodel)
		#selection
		self.win_OD_selection = self.win_OD_treeview.get_selection()
		self.win_OD_selection.set_mode(Gtk.SelectionMode.SINGLE)
		#treeview columns		
		self.win_OD_tvcolumn0 = g4.new_treeview_column(_('Name'))
		self.win_OD_tvcolumn1 = g4.new_treeview_column(_('Birth Date (Local)'))
		self.win_OD_tvcolumn2 = g4.new_treeview_column(_('Location'))
		#add data from event_natal table
		if extraDB != None:
			self.win_OD_treeview.set_enable_search(False)		
			self.DB = extraDB
		else:
			self.win_OD_treeview.set_enable_search(True)		
			self.DB = g.db.getDatabase()
			
		for i in range(len(self.DB)):
			h,m,s = g.astrology_chart.decHour(float(self.DB[i]["hour"]))
			dt_utc=datetime.datetime(int(self.DB[i]["year"]),int(self.DB[i]["month"]),int(self.DB[i]["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(self.DB[i]["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}			
			self.listmodel.append([self.DB[i]["name"],birth_date,self.DB[i]["location"],self.DB[i]["id"]])

		#add columns to treeview
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn0)
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn1)
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn2)
		#cell renderers
		cell0 = Gtk.CellRendererText()
		cell1 = Gtk.CellRendererText()
		cell2 = Gtk.CellRendererText()
		#add cells to columns
		g4.treeview_column_pack_start(self.win_OD_tvcolumn0, cell0, True)
		g4.treeview_column_pack_start(self.win_OD_tvcolumn1, cell1, True)
		g4.treeview_column_pack_start(self.win_OD_tvcolumn2, cell2, True)
		#set the cell attributes to the listmodel column
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn0, cell0, text=0)
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn1, cell1, text=1)
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn2, cell2, text=2)
		#set treeview options
		self.win_OD_treeview.set_search_column(0)
		self.win_OD_tvcolumn0.set_sort_column_id(0)
		self.win_OD_tvcolumn1.set_sort_column_id(1)
		self.win_OD_tvcolumn2.set_sort_column_id(2)
		#add treeview to scrolledwindow
		scrolledwindow = Gtk.ScrolledWindow()
		g4.scrolled_set_child(scrolledwindow, self.win_OD_treeview)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		vbox=g4.new_vbox()
		g4.box_pack(vbox, scrolledwindow, True, True, 0)
		hbox=g4.new_hbox(4)		
		#buttons
		if extraDB == None:
			button = g4.button_new_stock(g4.STOCK_CANCEL)
			button.connect("clicked", lambda w: self.win_OD.close())
			g4.box_pack_end(hbox, button,False,False,0)	
			button = g4.button_new_stock(g4.STOCK_EDIT)
			button.connect("clicked", self.openDatabaseEdit)
			g4.box_pack_end(hbox, button,False,False,0)
			button = g4.button_new_stock(g4.STOCK_DELETE)
			button.connect("clicked", self.openDatabaseDel)
			g4.box_pack_end(hbox, button,False,False,0)
			button = g4.button_new_stock(g4.STOCK_OPEN)
			button.connect("clicked", self.openDatabaseOpen)
			g4.box_pack_end(hbox, button,False,False,0)	
		else:
			label=g4.new_label(_("Search Name")+":")
			self.namesearch = Gtk.Entry()
			self.namesearch.set_max_length(34)
			self.namesearch.set_width_chars(24)
			self.namesearchbutton = g4.new_button(_('Search'))
			self.namesearchbutton.connect("clicked", self.nameSearch)
			self.namesearch.connect("activate", self.nameSearch)
			self.nameresetbutton = g4.new_button(_('Reset'))
			self.nameresetbutton.connect("clicked", self.nameSearchReset)

			g4.box_pack_end(hbox, self.nameresetbutton,False,False,0)
			g4.box_pack_end(hbox, self.namesearchbutton,False,False,0)
			g4.box_pack_end(hbox, self.namesearch,False,False,0)
			g4.box_pack_end(hbox, label,False,False,0)
			
			button = g4.button_new_stock(g4.STOCK_OPEN)
			button.connect("clicked", self.openDatabaseOpen)
			g4.box_pack(hbox, button, False, False, 0)
			button = g4.button_new_stock(g4.STOCK_CLOSE)
			button.connect("clicked", lambda w: self.win_OD.close())
			g4.box_pack(hbox, button, False, False, 0)			
			
			
		#display window
		self.win_OD_treeview.connect("row-activated", lambda w, *args: self.openDatabaseOpen(w))
		g4.box_pack(vbox, hbox, False, False, 0)
		self.win_OD.set_child(vbox)
		self.win_OD_treeview.set_model(self.listmodel)
		self.win_OD.present()
		return
	
	def openDatabaseSelect(self, selectstr, type):
	
		self.win_OD = Gtk.Window()
		g4.window_set_icon(self.win_OD, g.cfg.iconWindow)
		self.win_OD.set_title(_('Select Database Entry'))
		self.win_OD.set_size_request(400, 450)
		self.win_OD
		self.win_OD.connect("close-request", lambda w, *args: self.openDatabaseSelectReject())
		#listmodel		
		listmodel = Gtk.ListStore(str,str,str,int)	
		self.win_OD_treeview = g4.new_treeview(listmodel)
		
		#selection
		self.win_OD_selection = self.win_OD_treeview.get_selection()
		self.win_OD_selection.set_mode(Gtk.SelectionMode.SINGLE)
		#treeview columns		
		self.win_OD_tvcolumn0 = g4.new_treeview_column(_('Name'))
		self.win_OD_tvcolumn1 = g4.new_treeview_column(_('Birth Date (Local)'))
		self.win_OD_tvcolumn2 = g4.new_treeview_column(_('Location'))
		#add data from event_natal table
		self.DB = g.db.getDatabase()
		for i in range(len(self.DB)):
			h,m,s = g.astrology_chart.decHour(float(self.DB[i]["hour"]))
			dt_utc=datetime.datetime(int(self.DB[i]["year"]),int(self.DB[i]["month"]),int(self.DB[i]["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(self.DB[i]["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}			
			listmodel.append([self.DB[i]["name"],birth_date,self.DB[i]["location"],self.DB[i]["id"]])
		#add columns to treeview
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn0)
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn1)
		self.win_OD_treeview.append_column(self.win_OD_tvcolumn2)
		#cell renderers
		cell0 = Gtk.CellRendererText()
		cell1 = Gtk.CellRendererText()
		cell2 = Gtk.CellRendererText()
		#add cells to columns
		g4.treeview_column_pack_start(self.win_OD_tvcolumn0, cell0, True)
		g4.treeview_column_pack_start(self.win_OD_tvcolumn1, cell1, True)
		g4.treeview_column_pack_start(self.win_OD_tvcolumn2, cell2, True)
		#set the cell attributes to the listmodel column
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn0, cell0, text=0)
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn1, cell1, text=1)
		g4.treeview_column_set_attributes(self.win_OD_tvcolumn2, cell2, text=2)
		#set treeview options
		self.win_OD_treeview.set_search_column(0)
		self.win_OD_tvcolumn0.set_sort_column_id(0)
		self.win_OD_tvcolumn1.set_sort_column_id(1)
		self.win_OD_tvcolumn2.set_sort_column_id(2)
		#add treeview to scrolledwindow
		scrolledwindow = Gtk.ScrolledWindow()
		g4.scrolled_set_child(scrolledwindow, self.win_OD_treeview)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		vbox=g4.new_vbox()
		g4.box_pack(vbox, scrolledwindow, True, True, 0)
		hbox=g4.new_hbox()		
		#buttons
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.openDatabaseSelectReject())
		g4.box_pack_end(hbox, button,False, False, 0)	
		button = g4.new_button(selectstr)
		button.connect("clicked", lambda w: self.openDatabaseSelectReturn(type))
		g4.box_pack_end(hbox, button,False, False, 0)		
		#display window
		g4.box_pack(vbox, hbox, False, False, 0)
		self.win_OD.set_child(vbox)
		self.win_OD_treeview.set_model(listmodel)
		self.win_OD.present()
		return
	
	def openDatabaseSelectReject(self):
		self.win_OD.close()
		return
	
	def openDatabaseSelectReturn(self, type):
		model = self.win_OD_selection.get_selected()[0]
		iter = self.win_OD_selection.get_selected()[1]
		for i in range(len(self.DB)):
			if self.DB[i]["id"] == model.get_value(iter,3):
				list = self.DB[i]

		#synastry
		if type == "Synastry":
			g.astrology_chart.type="Transit"
			g.astrology_chart.t_name=str(list["name"])
			g.astrology_chart.t_year=int(list["year"])
			g.astrology_chart.t_month=int(list["month"])
			g.astrology_chart.t_day=int(list["day"])
			g.astrology_chart.t_hour=float(list["hour"])
			g.astrology_chart.t_geolon=float(list["geolon"])
			g.astrology_chart.t_geolat=float(list["geolat"])
			g.astrology_chart.t_altitude=int(list["altitude"])
			g.astrology_chart.t_location=str(list["location"])
			g.astrology_chart.t_timezone=float(list["timezone"])
			g.astrology_chart.charttype="%s (%s)" % (g.astrology_chart.label["synastry"],g.astrology_chart.t_name)
			g.astrology_chart.transit=True
			g.astrology_chart.makeSVG()
			
		elif type == "Composite":
			g.astrology_chart.type="Composite"
			g.astrology_chart.t_name=str(list["name"])
			g.astrology_chart.t_year=int(list["year"])
			g.astrology_chart.t_month=int(list["month"])
			g.astrology_chart.t_day=int(list["day"])
			g.astrology_chart.t_hour=float(list["hour"])
			g.astrology_chart.t_geolon=float(list["geolon"])
			g.astrology_chart.t_geolat=float(list["geolat"])
			g.astrology_chart.t_altitude=int(list["altitude"])
			g.astrology_chart.t_location=str(list["location"])
			g.astrology_chart.t_timezone=float(list["timezone"])
			g.astrology_chart.charttype="%s (%s)" % (g.astrology_chart.label["composite"],g.astrology_chart.t_name)
			g.astrology_chart.transit=False
			g.astrology_chart.makeSVG()
			
		elif type == "Combine":
			g.astrology_chart.type="Combine"
			g.astrology_chart.t_name=str(list["name"])
			g.astrology_chart.t_year=int(list["year"])
			g.astrology_chart.t_month=int(list["month"])
			g.astrology_chart.t_day=int(list["day"])
			g.astrology_chart.t_hour=float(list["hour"])
			g.astrology_chart.t_geolon=float(list["geolon"])
			g.astrology_chart.t_geolat=float(list["geolat"])
			g.astrology_chart.t_altitude=int(list["altitude"])
			g.astrology_chart.t_location=str(list["location"])
			g.astrology_chart.t_timezone=float(list["timezone"])
			
			#calculate combine between both utc times
			h,m,s = g.astrology_chart.decHour(g.astrology_chart.hour)
			dt1 = datetime.datetime(g.astrology_chart.year,g.astrology_chart.month,g.astrology_chart.day,h,m,s)
			h,m,s = g.astrology_chart.decHour(g.astrology_chart.t_hour)
			dt2 = datetime.datetime(g.astrology_chart.t_year,g.astrology_chart.t_month,g.astrology_chart.t_day,h,m,s)
			
			if dt1 > dt2:
				delta = dt1 - dt2
				hdelta = delta // 2
				combine = dt2 + hdelta
			else:
				delta = dt2 - dt1
				hdelta = delta // 2
				combine = dt1 + hdelta
			
			#take lon,lat middle
			g.astrology_chart.c_geolon = (g.astrology_chart.geolon + g.astrology_chart.t_geolon)/2.0
			g.astrology_chart.c_geolat = (g.astrology_chart.geolat + g.astrology_chart.t_geolat)/2.0
			g.astrology_chart.c_altitude = (g.astrology_chart.t_altitude + g.astrology_chart.altitude)/2.0
			g.astrology_chart.c_year = combine.year
			g.astrology_chart.c_month = combine.month
			g.astrology_chart.c_day = combine.day
			g.astrology_chart.c_hour = g.astrology_chart.decHourJoin(combine.hour,combine.minute,combine.second)
			
			g.astrology_chart.charttype="%s (%s)" % (g.astrology_chart.label["combine"],g.astrology_chart.t_name)
			g.astrology_chart.transit=False

			#set new date for printing in svg
			g.astrology_chart.year = g.astrology_chart.c_year
			g.astrology_chart.month = g.astrology_chart.c_month
			g.astrology_chart.day = g.astrology_chart.c_day
			g.astrology_chart.hour = g.astrology_chart.c_hour
			g.astrology_chart.geolat = g.astrology_chart.c_geolat
			g.astrology_chart.geolon = g.astrology_chart.c_geolon
			g.astrology_chart.timezone_str = zonetab.nearest_tz(g.astrology_chart.geolat,g.astrology_chart.geolon,zonetab.timezones())[2]
			#aware datetime object
			dt_input = datetime.datetime(combine.year, combine.month, combine.day, combine.hour, combine.minute, combine.second)
			dt = localize_naive(dt_input, g.astrology_chart.timezone_str)
			g.astrology_chart.timezone=g.astrology_chart.offsetToTz(dt.utcoffset())
			g.astrology_chart.utcToLocal()
			g.astrology_chart.makeSVG()
		
		self.draw.queue_draw()
		self.draw.setSVG(self.tempfilename)			
		self.win_OD.close()		
	
	def openDatabaseDel(self, widget):
		#get name from selection
		model = self.win_OD_selection.get_selected()[0]
		iter = self.win_OD_selection.get_selected()[1]
		for i in range(len(self.DB)):
			if self.DB[i]["id"] == model.get_value(iter,3):
				self.ODDlist = self.DB[i]
		name = self.ODDlist["name"]
		dialog=g4.question_dialog(self.win_OD, _('Question'), '')
		dialog.set_destroy_with_parent(True)
		dialog.connect("close", lambda w, *args: dialog.close())
		dialog.connect("response",self.openDatabaseDelDo)
		g4.box_pack(g4.dialog_content(dialog), g4.new_label(_('Are you sure you want to delete')+' '+name+'?'), True, True, 0)
		dialog.present()
		return
	
	def openDatabaseDelDo(self, widget, response_id):
		if response_id == Gtk.ResponseType.ACCEPT:
			#get id from selection
			del_id = self.ODDlist["id"]
			#delete database entry
			sql='DELETE FROM event_natal WHERE id='+str(del_id)
			g.db.pquery([sql])
			dprint('deleted database entry: '+self.ODDlist["name"])
			widget.close()
			self.win_OD.close()
			self.openDatabase(self.window)
			self.updateUI()
		else:
			widget.close()
			dprint('rejected database deletion')
		return
	
	def openDatabaseOpen(self, widget):
		model = self.win_OD_selection.get_selected()[0]
		iter = self.win_OD_selection.get_selected()[1]
		for i in range(len(self.DB)):
			if self.DB[i]["id"] == model.get_value(iter,3):
				list = self.DB[i]
		g.astrology_chart.type="Radix"
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.transit=False
		self.updateChartList(widget, list)
		self.win_OD.close()
		return
	
	def openDatabaseEdit(self, widget):
		model = self.win_OD_selection.get_selected()[0]
		iter = self.win_OD_selection.get_selected()[1]
		for i in range(len(self.DB)):
			if self.DB[i]["id"] == model.get_value(iter,3):
				self.oDE_list = self.DB[i]
		g.astrology_chart.type="Radix"
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.transit=False
		self.updateChartList(widget, self.oDE_list)
		self.eventData( widget , edit=True )
		return		

	def openDatabaseEditAsk(self, widget):
		#check for duplicate name without duplicate id
		en = g.db.getDatabase()
		for i in range(len(en)):
			if en[i]["name"] == self.name.get_text() and self.oDE_list["id"] != en[i]["id"]:
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
		dialog.connect("response",self.openDatabaseEditSave)
		g4.box_pack(g4.dialog_content(dialog), g4.new_label(_('Are you sure you want to Save?')), True, True, 0)
		dialog.present()	
		return	
	
	def openDatabaseEditSave(self, widget, response_id):
		if response_id == Gtk.ResponseType.ACCEPT:
			#update chart data
			self.updateChartData()
			#set query to save			
			sql = 'UPDATE event_natal SET name=?,year=?,month=?,day=?,hour=?,\
				geolon=?,geolat=?,altitude=?,location=?,timezone=?,notes=?,\
				image=?,countrycode=?,timezonestr=?,geonameid=? WHERE id=?'
			values = (g.astrology_chart.name,g.astrology_chart.year,g.astrology_chart.month,
				g.astrology_chart.day,g.astrology_chart.hour,g.astrology_chart.geolon,g.astrology_chart.geolat,g.astrology_chart.altitude,
				g.astrology_chart.location,g.astrology_chart.timezone,'','',g.astrology_chart.countrycode,
				g.astrology_chart.timezonestr,g.astrology_chart.geonameid,self.oDE_list["id"])
			g.db.pquery([sql],[values])
			dprint('saved edit to database: '+g.astrology_chart.name)
			widget.close()
			self.window2.close()
			self.win_OD.close()
			self.openDatabase( self.window )
			self.updateUI()
		else:
			widget.close()
			dprint('rejected save to database')
		return

	def doPrint(self, widget):
		settings = Gtk.PrintSettings()
		settings.set_resolution(300)
		print_op = Gtk.PrintOperation()
		print_op.set_unit(Gtk.Unit.MM)
		print_op.set_print_settings(settings)
		print_op.connect("begin_print", self.doPrintBegin)
		print_op.connect("draw_page", self.doPrintDraw)

		chooser = g4.file_chooser_dialog(
			self.window, _('Export chart as PDF'), Gtk.FileChooserAction.SAVE, g4.STOCK_SAVE)
		g4.chooser_set_folder(chooser, g.cfg.homedir)
		chooser.set_current_name(safe_chart_basename(g.astrology_chart.name) + '.pdf')
		filter = Gtk.FileFilter()
		filter.set_name(_('PDF file (*.pdf)'))
		filter.add_pattern('*.pdf')
		chooser.add_filter(filter)
		chooser.set_filter(filter)
		response, path = g4.file_chooser_run(chooser)
		if response == Gtk.ResponseType.OK and path:
			print_op.set_export_filename(path)
			res = print_op.run(Gtk.PrintOperationAction.EXPORT, self.window)
		else:
			print_op.cancel()
			res = None


	def doPrintBegin(self, operation, context):
		operation.set_n_pages(1)
		operation.set_use_full_page(False)
		ps = Gtk.PageSetup()
		ps.set_orientation(Gtk.PageOrientation.LANDSCAPE)
		ps.set_paper_size(Gtk.PaperSize(Gtk.PAPER_NAME_A4))
		operation.set_default_page_setup(ps)
	
	def doPrintDraw(self, operation, context, page_nr):
		cr = context.get_cairo_context()
		#draw svg
		printing={}
		printing['pagenum']=page_nr
		printing['width']=context.get_width()
		printing['height']=context.get_height()
		printing['dpi_x']=context.get_dpi_x()
		printing['dpi_y']=context.get_dpi_y()

		#make printing svg
		g.astrology_chart.makeSVG(printing=printing)
		
		#draw svg for printing
		svg = Rsvg.Handle.new_from_file(g.cfg.tempfilenameprint)
		svg.set_dpi(300)
		svg.render_cairo(cr)

		#cr.scale(1.5,1.5)
		
	
	"""
	
	Menu item for general configuration
	
	settingsConfiguration
	settingsConfigurationSubmit	
	
	"""

	def _settings_tradition_from_data(self, data):
		return self.tradition_list[data['tradition'].get_active()]

	def _settings_update_tradition_visibility(self, data):
		"""Show only controls that apply to the selected tradition."""
		is_vedic = self._settings_tradition_from_data(data) == 'vedic'
		for key in (
			'lbl_houses_system', 'houses_system',
			'lbl_chartview', 'chartview',
			'lbl_zodiactype', 'zodiactype',
			'lbl_siderealmode', 'siderealmode',
		):
			w = data.get(key)
			if w is not None:
				w.set_visible(not is_vedic)
		for key in (
			'lbl_vedic_ayanamsa', 'vedic_ayanamsa',
			'lbl_vedic_houses', 'vedic_houses',
			'lbl_vedic_dasha', 'vedic_dasha_system',
			'lbl_vedic_layout', 'vedic_chart_layout',
		):
			w = data.get(key)
			if w is not None:
				w.set_visible(is_vedic)
		if is_vedic:
			layout = self.vedic_layout_list[data['vedic_chart_layout'].get_active()]
			show_chartview = layout == 'wheel'
			for key in ('lbl_chartview', 'chartview'):
				w = data.get(key)
				if w is not None:
					w.set_visible(show_chartview)
		elif data.get('zodiactype') is not None and data.get('siderealmode') is not None:
			sidereal = self.zodiactype_list[data['zodiactype'].get_active()] == 'sidereal'
			data['siderealmode'].set_sensitive(sidereal)
	
	def settingsConfiguration(self, widget):
		# create a new window
		self.win_SC = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.win_SC, g.cfg.iconWindow)
		self.win_SC.set_title(_("General Configuration"))
		self.win_SC.connect("close-request", lambda w, *args: self.win_SC.close())
		self.win_SC.set_margin_start(5); self.win_SC.set_margin_end(5)
		self.win_SC.set_size_request(450,450)
		
		#data dictionary
		data = {}
		
		#create a table
		table = g4.new_table(8, 1, False)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		table.set_margin_start(10)
		
		#description

		#options
		g4.grid_attach(table, g4.new_label(_("Use Online Geocoding (ws.geonames.org)")), 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		data['use_geonames.org'] = Gtk.CheckButton()
		g4.grid_attach(table, data['use_geonames.org'], 0, 1, 1, 2, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		if g.db.getAstrocfg('use_geonames.org') == "1":
			data['use_geonames.org'].set_active(True)

		#tradition (western / vedic) — master switch for the rows below
		data['tradition'] = Gtk.ComboBoxText.new()
		data['lbl_tradition'] = g4.new_label(_('Tradition'))
		g4.grid_attach(table, data['lbl_tradition'], 0, 1, 2, 3, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['tradition'], 0, 1, 4, 5, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		tradition_labels = {"western": _("Western"), "vedic": _("Vedic (Jyotish)")}
		self.tradition_list = ["western", "vedic"]
		active = 0
		for n in range(len(self.tradition_list)):
			data['tradition'].append_text(tradition_labels[self.tradition_list[n]])
			if g.db.astrocfg.get('tradition', 'western') == self.tradition_list[n]:
				active = n
		data['tradition'].set_active(active)
		
		#house system (western)
		data['houses_system'] = Gtk.ComboBoxText.new()
		data['lbl_houses_system'] = g4.new_label(_('Houses System'))
		g4.grid_attach(table, data['lbl_houses_system'], 0, 1, 6, 7, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		g4.grid_attach(table, data['houses_system'], 0, 1, 8, 9, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		hsys={
				"P":"Placidus",
				"K":"Koch",
				"O":"Porphyrius",
				"R":"Regiomontanus",
				"C":"Campanus",
				"A":"Equal (Cusp 1 = Asc)",
				"V":"Vehlow Equal (Asc = 1/2 House 1)",
				"W":"Whole",
				"X":"Axial Rotation",
				"H":"Azimuthal or Horizontal System",
				"T":"Polich/Page ('topocentric system')",
				"B":"Alcabitus",
				"G":"Gauquelin sectors",
				"M":"Morinus"
				}		
		self.houses_list=["P","K","O","R","C","A","V","W","X","H","T","B","G","M"]
		active=0
		for n in range(len(self.houses_list)):
			data['houses_system'].append_text(hsys[self.houses_list[n]])
			if g.db.astrocfg['houses_system'] == self.houses_list[n]:
				active = n
		data['houses_system'].set_active(active)
		
		#position calculation (geo,truegeo,topo,helio)		
		data['postype'] = Gtk.ComboBoxText.new()
		g4.grid_attach(table, g4.new_label(_('Position Calculation')), 0, 1, 10, 11, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		g4.grid_attach(table, data['postype'], 0, 1, 12, 13, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		postype={
		
				"geo":g.astrology_chart.label["apparent_geocentric"]+" "+_("(default)"),
				"truegeo":g.astrology_chart.label["true_geocentric"],
				"topo":g.astrology_chart.label["topocentric"],
				"helio":g.astrology_chart.label["heliocentric"]
				}		
		self.postype_list=["geo","truegeo","topo","helio"]
		active=0
		for n in range(len(self.postype_list)):
			data['postype'].append_text(postype[self.postype_list[n]])
			if g.db.astrocfg['postype'] == self.postype_list[n]:
				active = n
		data['postype'].set_active(active)

		#chart view (traditional,european)		
		data['chartview'] = Gtk.ComboBoxText.new()
		data['lbl_chartview'] = g4.new_label(_('Chart View'))
		g4.grid_attach(table, data['lbl_chartview'], 0, 1, 14, 15, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		g4.grid_attach(table, data['chartview'], 0, 1, 16, 17, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		chartview={
				"traditional":_("Planets in Zodiac"),
				"european":_("Planets around Zodiac")
				}		
		self.chartview_list=["traditional","european"]
		active=0
		for n in range(len(self.chartview_list)):
			data['chartview'].append_text(chartview[self.chartview_list[n]])
			if g.db.astrocfg['chartview'] == self.chartview_list[n]:
				active = n
		data['chartview'].set_active(active)


		#zodiac type (tropical, sidereal)	
		data['zodiactype'] = Gtk.ComboBoxText.new()
		data['lbl_zodiactype'] = g4.new_label(_('Zodiac Type'))
		g4.grid_attach(table, data['lbl_zodiactype'], 0, 1, 18, 19, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		g4.grid_attach(table, data['zodiactype'], 0, 1, 20, 21, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		chartview={
				"tropical":_("Tropical"),
				"sidereal":_("Sidereal")
				}		
		self.zodiactype_list=["tropical","sidereal"]
		active=0
		for n in range(len(self.zodiactype_list)):
			data['zodiactype'].append_text(chartview[self.zodiactype_list[n]])
			if g.db.astrocfg['zodiactype'] == self.zodiactype_list[n]:
				active = n
		data['zodiactype'].set_active(active)

		
		#sidereal mode (western sidereal only)
		data['siderealmode'] = Gtk.ComboBoxText.new()
		if g.db.astrocfg['zodiactype'] != 'sidereal':
			data['siderealmode'].set_sensitive(False)
		def zodiactype_changed(button):
			if self._settings_tradition_from_data(data) != 'western':
				return
			if self.zodiactype_list[data['zodiactype'].get_active()] != 'sidereal':
				data['siderealmode'].set_sensitive(False)
			else:
				data['siderealmode'].set_sensitive(True)
		data['zodiactype'].connect("changed", zodiactype_changed)
		data['lbl_siderealmode'] = g4.new_label(_('Sidereal Mode'))
		g4.grid_attach(table, data['lbl_siderealmode'], 0, 1, 22, 23, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)		
		g4.grid_attach(table, data['siderealmode'], 0, 1, 24, 25, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		self.siderealmode_chartview={
				"FAGAN_BRADLEY":_("Fagan Bradley"),
				"LAHIRI":_("Lahiri"),
				"DELUCE":_("Deluce"),
				"RAMAN":_("Ramanb"),
				"USHASHASHI":_("Ushashashi"),
				"KRISHNAMURTI":_("Krishnamurti"),
				"DJWHAL_KHUL":_("Djwhal Khul"),
				"YUKTESHWAR":_("Yukteshwar"),
				"JN_BHASIN":_("Jn Bhasin"),
				"BABYL_KUGLER1":_("Babyl Kugler 1"),
				"BABYL_KUGLER2":_("Babyl Kugler 2"),
				"BABYL_KUGLER3":_("Babyl Kugler 3"),
				"BABYL_HUBER":_("Babyl Huber"),
				"BABYL_ETPSC":_("Babyl Etpsc"),
				"ALDEBARAN_15TAU":_("Aldebaran 15Tau"),
				"HIPPARCHOS":_("Hipparchos"),
				"SASSANIAN":_("Sassanian"),
				"J2000":_("J2000"),
				"J1900":_("J1900"),
				"B1950":_("B1950")
				}		
		self.siderealmode_list=["FAGAN_BRADLEY",
				"LAHIRI",
				"DELUCE",
				"RAMAN",
				"USHASHASHI",
				"KRISHNAMURTI",
				"DJWHAL_KHUL",
				"YUKTESHWAR",
				"JN_BHASIN",
				"BABYL_KUGLER1",
				"BABYL_KUGLER2",
				"BABYL_KUGLER3",
				"BABYL_HUBER",
				"BABYL_ETPSC",
				"ALDEBARAN_15TAU",
				"HIPPARCHOS",
				"SASSANIAN",
				"J2000",
				"J1900",
				"B1950"]
		active=0
		for n in range(len(self.siderealmode_list)):
			data['siderealmode'].append_text(self.siderealmode_chartview[self.siderealmode_list[n]])
			if g.db.astrocfg['siderealmode'] == self.siderealmode_list[n]:
				active = n
		data['siderealmode'].set_active(active)

		#vedic chart layout
		data['vedic_chart_layout'] = Gtk.ComboBoxText.new()
		data['lbl_vedic_layout'] = g4.new_label(_('Vedic Chart Layout'))
		g4.grid_attach(table, data['lbl_vedic_layout'], 0, 1, 26, 27, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['vedic_chart_layout'], 0, 1, 28, 29, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		layout_labels = {"north": _("North Indian"), "south": _("South Indian"), "wheel": _("Western Wheel")}
		self.vedic_layout_list = ["north", "south", "wheel"]
		active = 0
		for n in range(len(self.vedic_layout_list)):
			data['vedic_chart_layout'].append_text(layout_labels[self.vedic_layout_list[n]])
			if g.db.astrocfg.get('vedic_chart_layout', 'north') == self.vedic_layout_list[n]:
				active = n
		data['vedic_chart_layout'].set_active(active)

		from astrologymod.vedic.graha import VEDIC_AYANAMSA_MODES
		data['vedic_ayanamsa'] = Gtk.ComboBoxText.new()
		data['lbl_vedic_ayanamsa'] = g4.new_label(_('Vedic Ayanamsa'))
		g4.grid_attach(table, data['lbl_vedic_ayanamsa'], 0, 1, 30, 31, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['vedic_ayanamsa'], 0, 1, 32, 33, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		self.vedic_ayanamsa_list = list(VEDIC_AYANAMSA_MODES)
		active = 0
		for n, mode in enumerate(self.vedic_ayanamsa_list):
			data['vedic_ayanamsa'].append_text(mode.replace('_', ' '))
			if g.db.astrocfg.get('vedic_ayanamsa', 'LAHIRI') == mode:
				active = n
		data['vedic_ayanamsa'].set_active(active)

		data['vedic_dasha_system'] = Gtk.ComboBoxText.new()
		data['lbl_vedic_dasha'] = g4.new_label(_('Dasha System'))
		g4.grid_attach(table, data['lbl_vedic_dasha'], 0, 1, 34, 35, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['vedic_dasha_system'], 0, 1, 36, 37, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		self.vedic_dasha_list = ['vimshottari', 'yogini', 'ashtottari']
		dasha_labels = {'vimshottari': _('Vimshottari'), 'yogini': _('Yogini'), 'ashtottari': _('Ashtottari')}
		active = 0
		for n, ds in enumerate(self.vedic_dasha_list):
			data['vedic_dasha_system'].append_text(dasha_labels[ds])
			if g.db.astrocfg.get('vedic_dasha_system', 'vimshottari') == ds:
				active = n
		data['vedic_dasha_system'].set_active(active)

		data['vedic_houses'] = Gtk.ComboBoxText.new()
		data['lbl_vedic_houses'] = g4.new_label(_('Vedic Houses'))
		g4.grid_attach(table, data['lbl_vedic_houses'], 0, 1, 38, 39, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['vedic_houses'], 0, 1, 40, 41, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		self.vedic_houses_list = ['whole_sign', 'equal']
		hlabels = {'whole_sign': _('Whole Sign'), 'equal': _('Equal (Asc = cusp 1)')}
		active = 0
		for n, hs in enumerate(self.vedic_houses_list):
			data['vedic_houses'].append_text(hlabels[hs])
			if g.db.astrocfg.get('vedic_houses', 'whole_sign') == hs:
				active = n
		data['vedic_houses'].set_active(active)

		#language		
		data['language'] = Gtk.ComboBoxText.new()
		g4.grid_attach(table, g4.new_label(_('Language')), 0, 1, 42, 43, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		g4.grid_attach(table, data['language'], 0, 1, 44, 45, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		
		data['language'].append_text(_("Default"))
		active=0
		for i in range(len(LANGUAGES)):
			data['language'].append_text(g.db.lang_label[LANGUAGES[i]])
			if g.db.astrocfg['language'] == LANGUAGES[i]:
				active = i+1
		data['language'].set_active(active)			
		
		#make the ui layout with ok button
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_margin_start(5); scrolledwindow.set_margin_end(5)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		g4.box_pack(g4.dialog_content(self.win_SC), scrolledwindow, True, True, 0)
		g4.scrolled_set_child(scrolledwindow, table)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.settingsConfigurationSubmit, data)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_SC), button, True, True, 0)
		g4.button_grab_default(button)		

		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SC.close())
		g4.box_pack(g4.dialog_action_area(self.win_SC), button, True, True, 0)

		def tradition_changed(*_args):
			self._settings_update_tradition_visibility(data)
		data['tradition'].connect('changed', tradition_changed)
		data['vedic_chart_layout'].connect('changed', tradition_changed)
		self._settings_update_tradition_visibility(data)

		self.win_SC.present()			
		return
	
	def settingsConfigurationSubmit(self, widget, data):
		update=False
		if data['use_geonames.org'].get_active():
			g.db.setAstrocfg("use_geonames.org","1")
		else:
			g.db.setAstrocfg("use_geonames.org","0")
		#position calculation (shared)
		if self.postype_list[data['postype'].get_active()] != g.db.astrocfg['postype']:
			update=True
		g.db.setAstrocfg("postype",self.postype_list[data['postype'].get_active()])
		prev_trad = g.db.astrocfg.get('tradition', 'western')
		trad = self.tradition_list[data['tradition'].get_active()]
		if trad != prev_trad:
			update = True
		g.db.setAstrocfg("tradition", trad)
		if trad == 'vedic':
			if prev_trad != 'vedic':
				from astrologymod.vedic.preset import apply_vedic_defaults
				apply_vedic_defaults(g.db.astrocfg)
				g.db.apply_vedic_planet_visibility()
			layout = self.vedic_layout_list[data['vedic_chart_layout'].get_active()]
			if layout != g.db.astrocfg.get('vedic_chart_layout', 'north'):
				update = True
			g.db.setAstrocfg("vedic_chart_layout", layout)
			ayan = self.vedic_ayanamsa_list[data['vedic_ayanamsa'].get_active()]
			if ayan != g.db.astrocfg.get('vedic_ayanamsa', 'LAHIRI'):
				update = True
			g.db.setAstrocfg("vedic_ayanamsa", ayan)
			g.db.setAstrocfg("siderealmode", ayan)
			g.db.setAstrocfg("zodiactype", "sidereal")
			dasha = self.vedic_dasha_list[data['vedic_dasha_system'].get_active()]
			if dasha != g.db.astrocfg.get('vedic_dasha_system', 'vimshottari'):
				update = True
			g.db.setAstrocfg("vedic_dasha_system", dasha)
			vhouses = self.vedic_houses_list[data['vedic_houses'].get_active()]
			if vhouses != g.db.astrocfg.get('vedic_houses', 'whole_sign'):
				update = True
			g.db.setAstrocfg("vedic_houses", vhouses)
			hsys = "W" if vhouses == 'whole_sign' else "A"
			if hsys != g.db.astrocfg.get('houses_system'):
				update = True
			g.db.setAstrocfg("houses_system", hsys)
			if layout == 'wheel':
				cv = self.chartview_list[data['chartview'].get_active()]
				if cv != g.db.astrocfg['chartview']:
					update = True
				g.db.setAstrocfg("chartview", cv)
		else:
			if prev_trad == 'vedic':
				g.db.apply_western_planet_visibility()
			hsys = self.houses_list[data['houses_system'].get_active()]
			if hsys != g.db.astrocfg['houses_system']:
				update=True
			g.db.setAstrocfg("houses_system", hsys)
			cv = self.chartview_list[data['chartview'].get_active()]
			if cv != g.db.astrocfg['chartview']:
				update=True
			g.db.setAstrocfg("chartview", cv)
			zt = self.zodiactype_list[data['zodiactype'].get_active()]
			if zt != g.db.astrocfg['zodiactype']:
				update=True
			g.db.setAstrocfg("zodiactype", zt)
			sm = self.siderealmode_list[data['siderealmode'].get_active()]
			if sm != g.db.astrocfg['siderealmode']:
				update=True
			g.db.setAstrocfg("siderealmode", sm)
		#language
		model = data['language'].get_model()
		active = data['language'].get_active()
		if active == 0:
			active_lang = "default"
		else:
			active_lang = LANGUAGES[active-1]
		if active_lang != g.db.astrocfg['language']:
			update=True
		g.db.setAstrocfg("language",active_lang)
		
		#set language to be used
		g.db.setLanguage(active_lang)
		self.updateUI()
		
		#updatechart
		if update:
			self.updateChart()		
		self.win_SC.close()
		return

		
	"""
	
	Menu item to set aspect options
	
	settingsAspects
	settingsAspectsSubmit
	
	"""
			
	def settingsAspects(self, widget):
		# create a new window
		self.win_SA = g4.new_dialog()
		g4.window_set_icon(self.win_SA, g.cfg.iconWindow)
		self.win_SA.set_title(_("Aspect Settings"))
		self.win_SA.connect("close-request", lambda w, *args: self.win_SA.close())
		self.win_SA
		self.win_SA.set_margin_start(5); self.win_SA.set_margin_end(5)
		self.win_SA.set_size_request(550,450)
		
		#create a table
		table = g4.new_table(len(g.astrology_chart.aspects)-3, 6, False)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		table.set_margin_start(10)
		
		#description
		label = g4.new_label(_("Deg"))
		g4.grid_attach(table, label, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		label = g4.new_label(_("Aspect Name"))
		g4.grid_attach(table, label, 2, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		label = g4.new_label(_("Visible\nin Circle"))
		g4.grid_attach(table, label, 3, 4, 0, 1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		label = g4.new_label(_("Visible\nin Grid"))
		g4.grid_attach(table, label, 4, 5, 0, 1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		label = g4.new_label(_("Orb"))
		g4.grid_attach(table, label, 5, 6, 0, 1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)		
		
		data = []
		x=1
		for i in range(len(g.astrology_chart.aspects)):
			#0=degree, 1=name, 2=color, 3=is_major, 4=orb
			data.append({})
			data[-1]['icon'] = Gtk.Image()
			filename=os.path.join(g.cfg.iconAspects,str(g.astrology_chart.aspects[i]['degree'])+'.svg')
			data[-1]['icon'].set_from_file(filename)
			data[-1]['degree'] = g.astrology_chart.aspects[i]['degree']
			data[-1]['degree_str'] = g4.new_label(str(g.astrology_chart.aspects[i]['degree']))
			data[-1]['name'] = Gtk.Entry()
			data[-1]['name'].set_max_length(25)
			data[-1]['name'].set_width_chars(15)
			data[-1]['name'].set_text(g.astrology_chart.aspects[i]['name'])
			g4.grid_attach(table, data[-1]['icon'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, data[-1]['degree_str'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, data[-1]['name'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			data[-1]['visible'] = Gtk.CheckButton()
			if g.astrology_chart.aspects[i]['visible'] == 1:
				data[-1]['visible'].set_active(True)
			g4.grid_attach(table, data[-1]['visible'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.EXPAND, xpadding=2, ypadding=2)
			data[-1]['visible_grid'] = Gtk.CheckButton()
			if g.astrology_chart.aspects[i]['visible_grid'] == 1:
				data[-1]['visible_grid'].set_active(True)
			g4.grid_attach(table, data[-1]['visible_grid'], 4, 5, x, x+1, xoptions=Gtk.AttachOptions.EXPAND, xpadding=2, ypadding=2)
			data[-1]['orb'] = Gtk.Entry()
			data[-1]['orb'].set_max_length(4)
			data[-1]['orb'].set_width_chars(4)
			data[-1]['orb'].set_text(str(g.astrology_chart.aspects[i]['orb']))
			g4.grid_attach(table, data[-1]['orb'], 5, 6, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)					
			x=x+1
		
		#make the ui layout with ok button
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_margin_start(5); scrolledwindow.set_margin_end(5)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		g4.box_pack(g4.dialog_content(self.win_SA), scrolledwindow, True, True, 0)
		g4.scrolled_set_child(scrolledwindow, table)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.settingsAspectsSubmit, data)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_SA), button, True, True, 0)
		g4.button_grab_default(button)		

		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SA.close())
		g4.box_pack(g4.dialog_action_area(self.win_SA), button, True, True, 0)

		self.win_SA.present()		
		return
	
	def settingsAspectsSubmit(self, widget, data):
		query=[]
		for i in range(len(data)):
		
			if data[i]['visible'].get_active():
				active = 1
			else:
				active = 0
				
			if data[i]['visible_grid'].get_active():
				active_grid = 1
			else:
				active_grid = 0
			
			orb = float(data[i]['orb'].get_text().replace(',','.'))
			if orb == int(orb):
				orb = int(orb)
			
			query.append((
				'UPDATE settings_aspect SET name=?, visible=?, visible_grid=?, orb=? '
				'WHERE degree=?',
				(
					data[i]['name'].get_text(),
					active,
					active_grid,
					str(orb),
					data[i]['degree'],
				),
			))

		g.db.query([q[0] for q in query], [q[1] for q in query])
		#update chart
		self.updateChart()
		#destroy window
		self.win_SA.close()
	
	"""
	
	Menu item to edit options for planets
	
	settingsPlanets
	settingsPlanetsSubmit	
	
	"""	
		
	def settingsPlanets(self, obj):
		# create a new window
		self.win_SP = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.win_SP, g.cfg.iconWindow)
		self.win_SP.set_title(_("Planets & Angles Settings"))
		self.win_SP.connect("close-request", lambda w, *args: self.win_SP.close())
		self.win_SP
		self.win_SP.set_margin_start(5); self.win_SP.set_margin_end(5)
		self.win_SP.set_size_request(470,450)
		
		#create a table
		table = g4.new_table(len(g.astrology_chart.planets)-3, 4, False)
		table.set_margin_start(10)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		
		#description
		g4.grid_set_row_spacing(table, 0, 8)
		label = g4.new_label(_("Planet Label"))
		g4.grid_attach(table, label, 0, 1, 0, 1)
		label = g4.new_label(_("Symbol"))
		g4.grid_attach(table, label, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		label = g4.new_label(_("Aspect Line"))
		g4.grid_attach(table, label, 2, 3, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
		label = g4.new_label(_("Aspect Grid"))
		g4.grid_attach(table, label, 3, 4, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
						
		data = []
		x=1
		for i in range(len(g.astrology_chart.planets)):
			#planets to skip: 11=true node, 13=osc. apogee, 14=earth, 21=intp. apogee, 22=intp. perigee
			#angles: 23=Asc, 24=Mc, 25=Ds, 26=Ic
			#points: 27=pars fortuna
			if i == 11 or i == 13 or i == 14 or i == 21 or i == 22:
				continue
			#start of the angles			
			if i == 23 or i == 27:
				g4.grid_set_row_spacing(table, x - 1, 20)
				g4.grid_set_row_spacing(table, x, 8)
				if i == 27:
					label = g4.new_label(_("Point Label"))
				else:
					label = g4.new_label(_("Angle Label"))	
				g4.grid_attach(table, label, 0, 1, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
				label = g4.new_label(_("Symbol"))
				g4.grid_attach(table, label, 1, 2, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
				label = g4.new_label(_("Aspect Line"))
				g4.grid_attach(table, label, 2, 3, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
				label = g4.new_label(_("Aspect Grid"))
				g4.grid_attach(table, label, 3, 4, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)				
				x=x+1
			data.append({})
			data[-1]['id'] = g.astrology_chart.planets[i]['id']
			data[-1]['label'] = Gtk.Entry()
			data[-1]['label'].set_max_length(25)
			data[-1]['label'].set_width_chars(15)
			data[-1]['label'].set_text(g.astrology_chart.planets[i]['label'])
			#data[-1]['label'].set_alignment(xalign=0.0, yalign=0.5)
			g4.grid_attach(table, data[-1]['label'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
			data[-1]['visible'] = Gtk.CheckButton()
			if g.astrology_chart.planets[i]['visible'] == 1:
				data[-1]['visible'].set_active(True)
			g4.grid_attach(table, data[-1]['visible'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=2, ypadding=2)
			
			data[-1]['visible_aspect_line'] = Gtk.CheckButton()
			if g.astrology_chart.planets[i]['visible_aspect_line'] == 1:
				data[-1]['visible_aspect_line'].set_active(True)
			g4.grid_attach(table, data[-1]['visible_aspect_line'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=2, ypadding=2)	
			
			data[-1]['visible_aspect_grid'] = Gtk.CheckButton()
			if g.astrology_chart.planets[i]['visible_aspect_grid'] == 1:
				data[-1]['visible_aspect_grid'].set_active(True)
			g4.grid_attach(table, data[-1]['visible_aspect_grid'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=2, ypadding=2)	
			x=x+1
		
		#make the ui layout with ok button
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_margin_start(5); scrolledwindow.set_margin_end(5)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		g4.box_pack(g4.dialog_content(self.win_SP), scrolledwindow, True, True, 0)
		g4.scrolled_set_child(scrolledwindow, table)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.settingsPlanetsSubmit, data)
		g4.button_set_can_default(button, True)
		#button.set_property('can_default',True)		
		g4.box_pack(g4.dialog_action_area(self.win_SP), button, True, True, 0)
		g4.button_grab_default(button)
		
		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SP.close())
		g4.box_pack(g4.dialog_action_area(self.win_SP), button, True, True, 0)
		
		self.win_SP.present()		
		return
	
	def settingsPlanetsSubmit(self, widget, data):
		query = []
		params = []
		for i in range(len(data)):
			radio = {"visible": 0, "visible_aspect_line": 0, "visible_aspect_grid": 0}
			for key in radio:
				if data[i][key].get_active():
					radio[key] = 1
			query.append(
				'UPDATE settings_planet SET label=?, visible=?, '
				'visible_aspect_line=?, visible_aspect_grid=? WHERE id=?')
			params.append((
				data[i]['label'].get_text(),
				radio['visible'],
				radio['visible_aspect_line'],
				radio['visible_aspect_grid'],
				data[i]['id'],
			))
		g.db.query(query, params)
		#update chart
		self.updateChart()
		#destroy window
		self.win_SP.close()


	"""
	
	Menu item to set color options
	
	settingsColors
	settingsColorsSubmit
	
	"""
	
	def settingsColorsReset(self, widget, id):
		self.SCdata[id]['code'].set_text(g.db.defaultColors[self.SCdata[id]['key']])
		g4.entry_modify_base(self.SCdata[id]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.db.defaultColors[self.SCdata[id]['key']]))
		return
			
	def settingsColors(self, widget):
		# initialize settings colors selector
		self.colorseldlg = None
				
		# create a new window
		self.win_SC = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.win_SC, g.cfg.iconWindow)
		self.win_SC.set_title(_("Color Settings"))
		self.win_SC.connect("close-request", lambda w, *args: self.win_SC.close())
		self.win_SC.set_margin_start(5); self.win_SC.set_margin_end(5)
		self.win_SC.set_size_request(470,450)
		
		#create a table
		table = g4.new_table(24, 4, False)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		table.set_margin_start(10)
		
		#data to be processed
		self.SCdata = []
		delimiter="--------------------------------------------"
		
		#Basic color scheme stuff
		g4.grid_attach(table, g4.new_label(delimiter),0,4,0,1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		g4.grid_attach(table, g4.new_label(_("Basic Chart Colors")),0,4,1,2,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		g4.grid_attach(table, g4.new_label(delimiter),0,4,2,3,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x=3
		for i in range(2):
			self.SCdata.append({})
			self.SCdata[-1]['key']="paper_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label("Paper Color %s"%(i))
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["paper_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["paper_%s"%(i)]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1
		#Zodiac background colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Zodiac Background Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1

		for i in range(12):
			self.SCdata.append({})
			self.SCdata[-1]['key']="zodiac_bg_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label(g.astrology_chart.zodiac[i])
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["zodiac_bg_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["zodiac_bg_%s"%(i)]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1
		
		#Circle and Line Colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Circles and Lines Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		for i in range(3):
			self.SCdata.append({})
			self.SCdata[-1]['key']="zodiac_radix_ring_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label("%s %s" %(_("Radix Ring"),(i+1)) )
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["zodiac_radix_ring_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["zodiac_radix_ring_%s"%(i)]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1
			
		for i in range(4):
			self.SCdata.append({})
			self.SCdata[-1]['key']="zodiac_transit_ring_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label("%s %s" %(_("Transit Ring"),(i+1)) )
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["zodiac_transit_ring_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["zodiac_transit_ring_%s"%(i)]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1								
		
		self.SCdata.append({})
		self.SCdata[-1]['key']="houses_radix_line"
		self.SCdata[-1]['name']=g4.new_label(_("Cusp Radix"))
		self.SCdata[-1]['code'] = Gtk.Entry()
		self.SCdata[-1]['code'].set_max_length(25)
		self.SCdata[-1]['code'].set_width_chars(10)
		self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["houses_radix_line"])
		g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["houses_radix_line"]))
		self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
		self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
		self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
		self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
			
		g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		x+=1
		
		self.SCdata.append({})
		self.SCdata[-1]['key']="houses_transit_line"
		self.SCdata[-1]['name']=g4.new_label(_("Cusp Transit"))
		self.SCdata[-1]['code'] = Gtk.Entry()
		self.SCdata[-1]['code'].set_max_length(25)
		self.SCdata[-1]['code'].set_width_chars(10)
		self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["houses_transit_line"])
		g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["houses_transit_line"]))
		self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
		self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
		self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
		self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
			
		g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
		x+=1		

		#Zodiac icon colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Zodiac Icon Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		for i in range(12):
			self.SCdata.append({})
			self.SCdata[-1]['key']="zodiac_icon_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label(g.astrology_chart.zodiac[i])
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["zodiac_icon_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["zodiac_icon_%s"%(i)]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1			

		#Aspects colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Aspects Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		for i in range(len(g.astrology_chart.aspects)):
			self.SCdata.append({})
			self.SCdata[-1]['key']="aspect_%s"%(g.astrology_chart.aspects[i]['degree'])
			self.SCdata[-1]['name']=g4.new_label(g.astrology_chart.aspects[i]['name'])
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["aspect_%s"%(g.astrology_chart.aspects[i]['degree'])])

			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["aspect_%s"%(g.astrology_chart.aspects[i]['degree'])]))
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1

		#Planet colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Planet Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		for i in range(len(g.astrology_chart.planets)):
			self.SCdata.append({})
			self.SCdata[-1]['key']="planet_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label(g.astrology_chart.planets[i]['name'])
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["planet_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["planet_%s"%(i)]) )
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1

		#Lunar phase colors
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(_("Lunar Phase Colors")),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		g4.grid_attach(table, g4.new_label(delimiter),0,4,x,x+1,xoptions=Gtk.AttachOptions.FILL,xpadding=10)
		x+=1
		for i in range(3):
			self.SCdata.append({})
			self.SCdata[-1]['key']="lunar_phase_%s"%(i)
			self.SCdata[-1]['name']=g4.new_label("lunar_phase_%s"%(i))
			self.SCdata[-1]['code'] = Gtk.Entry()
			self.SCdata[-1]['code'].set_max_length(25)
			self.SCdata[-1]['code'].set_width_chars(10)
			self.SCdata[-1]['code'].set_text(g.astrology_chart.colors["lunar_phase_%s"%(i)])
			g4.entry_modify_base(self.SCdata[-1]['code'], Gtk.StateFlags.NORMAL, g4.color_parse(g.astrology_chart.colors["lunar_phase_%s"%(i)]) )
			self.SCdata[-1]['button'] = g4.button_new_stock(g4.STOCK_SELECT_COLOR)
			self.SCdata[-1]['button'].connect("clicked", self.settingsColorsChanger, len(self.SCdata)-1)
			self.SCdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SCdata[-1]['reset'].connect("clicked", self.settingsColorsReset, len(self.SCdata)-1)
				
			g4.grid_attach(table, self.SCdata[-1]['name'], 0, 1, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['code'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['button'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			g4.grid_attach(table, self.SCdata[-1]['reset'], 3, 4, x, x+1, xoptions=Gtk.AttachOptions.FILL, xpadding=10)
			x+=1
		
		#make the ui layout with ok button
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_margin_start(5); scrolledwindow.set_margin_end(5)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		g4.box_pack(g4.dialog_content(self.win_SC), scrolledwindow, True, True, 0)
		g4.scrolled_set_child(scrolledwindow, table)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.settingsColorsSubmit)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_SC), button, True, True, 0)
		g4.button_grab_default(button)		

		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_SC.close())
		g4.box_pack(g4.dialog_action_area(self.win_SC), button, True, True, 0)

		self.win_SC.present()		
		return
	
	def settingsColorsChanger(self, widget, count):
		input_color = g4.color_parse(self.SCdata[count]["code"].get_text())
		
		self.colorseldlg = Gtk.ColorSelectionDialog(_("Please select a color"),parent=self.win_SC)
		colorsel = self.colorseldlg.get_color_selection()
		colorsel.set_current_color(input_color)
		colorsel.set_has_palette(True)
		response = self.colorseldlg.run()
		if response == Gtk.ResponseType.OK:
			output_color = colorsel.get_current_color()
			r=int( output_color.red / 257 )
			g=int( output_color.green / 257 )
			b=int( output_color.blue / 257 )
			self.SCdata[count]["code"].set_text("#%02X%02X%02X"%(r,g,b))
			g4.entry_modify_base(self.SCdata[count]['code'], Gtk.StateFlags.NORMAL, output_color)
		self.colorseldlg.hide()

		return
	
	def settingsColorsSubmit(self, widget):
		query = []
		params = []
		for i in range(len(self.SCdata)):
			key = self.SCdata[i]['key']
			code = self.SCdata[i]['code'].get_text().strip()
			if not validate_color_key(key) or not validate_hex_color(code):
				continue
			query.append('UPDATE color_codes SET code=? WHERE name=?')
			params.append((code, key))
		if query:
			g.db.query(query, params)
		#update colors
		g.astrology_chart.colors = g.db.getColors()
		#update chart
		self.updateChart()
		#destroy window
		self.win_SC.close()



	"""
	
	Menu item to edit options for label
	
	settingsLabel
	settingsLabelSubmit	
	
	"""
		
	def settingsLabelReset(self, widget, id):
		self.SLdata[id]['value'].set_text(g.db.defaultLabel[self.SLdata[id]['name']])
		return
		
	def settingsLabel(self, obj):
		self.win_labels = g4.new_dialog(transient_for=self.window)
		g4.window_set_icon(self.win_labels, g.cfg.iconWindow)
		self.win_labels.set_title(_("Label Settings"))
		self.win_labels.connect("close-request", lambda w, *args: self.win_labels.close())
		self.win_labels.set_default_size(540, 500)
		
		#create a table
		table = g4.new_table(len(g.astrology_chart.label), 3, False)
		table.set_margin_start(10)
		table.set_column_spacing(0)
		table.set_row_spacing(0)
		
		#description
		g4.grid_set_row_spacing(table, 0, 8)
		label = g4.new_label(_("Label"))
		g4.grid_attach(table, label, 0, 1, 0, 1)
		label = g4.new_label(_("Value"))
		g4.grid_attach(table, label, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
						
		self.SLdata = []
		x=1
		keys = list(g.astrology_chart.label.keys())
		keys.sort()
		for key in keys:
			value=g.astrology_chart.label[key]
			self.SLdata.append({})
			self.SLdata[-1]['name'] = key
			self.SLdata[-1]['value'] = Gtk.Entry()
			self.SLdata[-1]['value'].set_max_length(50)
			self.SLdata[-1]['value'].set_width_chars(25)
			self.SLdata[-1]['value'].set_text(value)
			self.SLdata[-1]['reset'] = g4.new_button(_("Default"))
			self.SLdata[-1]['reset'].connect("clicked", self.settingsLabelReset, len(self.SLdata)-1)
			g4.grid_attach(table, g4.new_label(key), 0, 1, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=10)
			g4.grid_attach(table, self.SLdata[-1]['value'], 1, 2, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=2, ypadding=2)
			g4.grid_attach(table, self.SLdata[-1]['reset'], 2, 3, x, x+1, xoptions=Gtk.AttachOptions.SHRINK, xpadding=2, ypadding=2)
			x=x+1
		
		#make the ui layout with ok button
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_margin_start(5); scrolledwindow.set_margin_end(5)
		scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		g4.box_pack(g4.dialog_content(self.win_labels), scrolledwindow, True, True, 0)
		g4.scrolled_set_child(scrolledwindow, table)
		
		#ok button
		button = g4.button_new_stock(g4.STOCK_OK)
		button.connect("clicked", self.settingsLabelSubmit, self.SLdata)
		g4.button_set_can_default(button, True)		
		g4.box_pack(g4.dialog_action_area(self.win_labels), button, True, True, 0)
		g4.button_grab_default(button)
		
		#cancel button
		button = g4.button_new_stock(g4.STOCK_CANCEL)
		button.connect("clicked", lambda w: self.win_labels.close())
		g4.box_pack(g4.dialog_action_area(self.win_labels), button, True, True, 0)
		
		self.win_labels.present()		
		return
	
	def settingsLabelSubmit(self, widget, data):
		query = []
		params = []
		for i in range(len(data)):
			name = data[i]['name']
			value = data[i]['value'].get_text()
			if value == g.astrology_chart.label[name]:
				continue
			if not validate_label_key(name):
				continue
			query.append('UPDATE label SET value=? WHERE name=?')
			params.append((value, name))
		if query:
			g.db.query(query, params)
		g.astrology_chart.label = g.db.getLabel()	
		self.updateChart()
		self.win_labels.close()


	"""
		
		Update the chart with input list data

	"""

	def updateChartList(self, b, list):
		g.astrology_chart.type="Radix"
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.name=str(list["name"])
		g.astrology_chart.year=int(list["year"])
		g.astrology_chart.month=int(list["month"])
		g.astrology_chart.day=int(list["day"])
		g.astrology_chart.hour=float(list["hour"])
		g.astrology_chart.geolon=float(list["geolon"])
		g.astrology_chart.geolat=float(list["geolat"])
		g.astrology_chart.altitude=int(list["altitude"])
		g.astrology_chart.location=str(list["location"])
		g.astrology_chart.timezone=float(list["timezone"])
		g.astrology_chart.countrycode=''
		if "countrycode" in list:
			g.astrology_chart.countrycode=list["countrycode"]
		if "timezonestr" in list:
			g.astrology_chart.timezonestr=list["timezonestr"]
		else:
			g.astrology_chart.timezonestr=g.db.gnearest(g.astrology_chart.geolat,g.astrology_chart.geolon)['timezonestr']
		g.astrology_chart.geonameid=None
		if "geonameid" in list:
			g.astrology_chart.geonameid=list['geonameid']
			
		g.astrology_chart.utcToLocal()
		g.astrology_chart.makeSVG()
		self.draw.queue_draw()
		self.draw.setSVG(self.tempfilename)

	def _on_chart_viewport_changed(self, width, height):
		g.astrology_chart.set_chart_viewport(width, height)
		self.updateChart()

	def _initial_chart_refresh(self):
		width = self.draw.get_width()
		height = self.draw.get_height()
		if width < 200 or height < 200:
			return True
		self.draw._last_viewport = (width, height)
		g.astrology_chart.set_chart_viewport(width, height)
		self.updateChart()
		return False

	def updateChart(self):
		width = self.draw.get_width()
		height = self.draw.get_height()
		if width >= 200 and height >= 200:
			g.astrology_chart.set_chart_viewport(width, height)
		self.tempfilename = g.astrology_chart.makeSVG()
		self.draw.setSVG(self.tempfilename)
		self.draw.queue_draw()

	def updateChartData(self):
		#check for internet connection
		if self.iconn:
			result = geoname.search(self.geoLoc.get_text(),self.geoCC.get_text())
			if result:
				self.geoLocFound = True
				lat=float(result[0]['lat'])
				lon=float(result[0]['lng'])
				gid=int(result[0]['geonameId'])
				cc=result[0]['countryCode']
				tzstr=result[0]['timezonestr']
				loc='%s, %s' % (result[0]['name'],result[0]['countryName'])
				dprint('updateChartData: %s,%s found; %s %s %s' % (
					self.geoLoc.get_text(),self.geoCC.get_text(),lat,lon,loc))
			else:
				self.geoLocFound = False
				#revert to defaults
				lat=g.astrology_chart.geolat
				lon=g.astrology_chart.geolon
				loc=g.astrology_chart.location
				cc=g.astrology_chart.countrycode
				tzstr=g.astrology_chart.timezonestr
				gid=g.astrology_chart.geonameid
				dprint('updateChartData: %s,%s not found, reverting to defaults' % (
					self.geoLoc.get_text(),self.geoCC.get_text()) )
				self.geoLoc.set_text(_('City not found! Try Again.'))
				return
		else:
			#using geonames database
			self.geoLocFound = True
			lat = float(self.GEON_lat)
			lon = float(self.GEON_lon)
			loc = self.GEON_loc
			cc = self.GEON_cc
			tzstr = self.GEON_tzstr
			gid = self.GEON_id

		#calculate timezone
		g.astrology_chart.timezonestr = tzstr
		g.astrology_chart.geonameid = gid

		#aware datetime object
		try:
			dt_input = datetime.datetime(
				int(self.dateY.get_text()),
				int(self.dateM.get_text()),
				int(self.dateD.get_text()),
				int(self.eH.get_text()),
				int(self.eM.get_text()),
				int(self.eS.get_text()),
			)
		except ValueError:
			dlg = Gtk.AlertDialog(
				message=_('Invalid date or time'),
				detail=_('Please enter numeric year, month, day, hour, minute, and second.'),
			)
			dlg.show(self.window2)
			return
		dt = localize_naive(dt_input, g.astrology_chart.timezonestr)
		dprint( dt.strftime('%Y-%m-%d %H:%M:%S %Z%z') )
		dprint( 'Daylight Saving Time: %s' %((dt.dst().seconds / 3600.0) if dt.dst() else 0.0) )
		
		#naive datetime object UTC
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		
		#set globals
		g.astrology_chart.year = dt_utc.year
		g.astrology_chart.month = dt_utc.month
		g.astrology_chart.day = dt_utc.day
		g.astrology_chart.hour = g.astrology_chart.decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
		g.astrology_chart.timezone = g.astrology_chart.offsetToTz(dt.utcoffset())
		g.astrology_chart.name = self.name.get_text()
		
		#location
		g.astrology_chart.geolat=lat
		g.astrology_chart.geolon=lon
		g.astrology_chart.location=loc
		g.astrology_chart.countrycode=cc
		
		#update local time
		g.astrology_chart.utcToLocal()

		#update labels
		labelDateStr = str(g.astrology_chart.year_loc)+'-%(#1)02d-%(#2)02d' % {'#1':g.astrology_chart.month_loc,'#2':g.astrology_chart.day_loc}		
		self.labelDate.set_text(labelDateStr)		
		labelTzStr = '%(#1)02d:%(#2)02d:%(#3)02d' % {'#1':g.astrology_chart.hour_loc,'#2':g.astrology_chart.minute_loc,'#3':g.astrology_chart.second_loc} + g.astrology_chart.decTzStr(g.astrology_chart.timezone)				
		self.labelTz.set_text(labelTzStr)
		self.ename.set_text(g.astrology_chart.name)
		self.entry2.set_text(' %s: %s\n %s: %s\n %s: %s' % ( _('Latitude'),lat,_('Longitude'),lon,_('Location'),loc) )

	def updateUI(self):
		history = list(g.db.history)
		history.reverse()
		hist = []
		for i in range(10):
			if i < len(history):
				hist.append((history[i][1], history[i]))
			else:
				hist.append((_('empty'), None))
		self.DB = g.db.getDatabase()
		self.menu.apply(hist, self.DB, _)

	def set_zoom_from_menu(self, idx):
		if idx == 0:
			g.astrology_chart.zoom = 0.8
		elif idx == 2:
			g.astrology_chart.zoom = 1.5
		elif idx == 3:
			g.astrology_chart.zoom = 2
		else:
			g.astrology_chart.zoom = 1
		g.astrology_chart.makeSVG()
		self.draw.queue_draw()
		self.draw.setSVG(self.tempfilename)
		

	def eventDataNew(self, widget):
		#default location
		g.astrology_chart.location=g.astrology_chart.home_location
		g.astrology_chart.geolat=float(g.astrology_chart.home_geolat)
		g.astrology_chart.geolon=float(g.astrology_chart.home_geolon)
		g.astrology_chart.countrycode=g.astrology_chart.home_countrycode
		
		#timezone string, example Europe/Amsterdam
		now = datetime.datetime.now()
		g.astrology_chart.timezone_str = zonetab.nearest_tz(g.astrology_chart.geolat,g.astrology_chart.geolon,zonetab.timezones())[2]
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = localize_naive(dt_input, g.astrology_chart.timezonestr)
		#naive utc datetime object
		dt_utc = naive_utc(dt)

		#Default
		g.astrology_chart.name=_("New Chart")
		g.astrology_chart.charttype=g.astrology_chart.label["radix"]
		g.astrology_chart.year=dt_utc.year
		g.astrology_chart.month=dt_utc.month
		g.astrology_chart.day=dt_utc.day
		g.astrology_chart.hour=g.astrology_chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		g.astrology_chart.timezone=g.astrology_chart.offsetToTz(dt.utcoffset())
		
		#Make locals
		g.astrology_chart.utcToLocal()
		
		#open editor
		self.eventData(widget, edit=False)
		return

	def quit_cb(self, b):
		dprint('Quitting program')
		app = self.window.get_application()
		if app:
			app.quit()

