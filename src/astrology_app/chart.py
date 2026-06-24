# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Chart state, ephemeris, aspects, and SVG generation."""

import codecs
import datetime
import math
import os
import socket
import sys
import webbrowser
from shutil import copyfile
from string import Template
from xml.sax.saxutils import escape as xml_escape

from gi import require_version

require_version('Gdk', '4.0')
require_version('Rsvg', '2.0')
require_version('Gtk', '4.0')
from gi.repository import Gdk, GObject, Gtk, Rsvg, cairo

from astrologymod import dignities, geoname, importfile, zonetab
from astrologymod import gtkcompat as g4
from astrologymod import swiss as ephemeris
from astrologymod.vedic import build_snapshot
from astrologymod.vedic.constants import DEFAULT_GRAHA_INDICES, RASHI_NAMES
from astrologymod.vedic.chart_svg import render_vedic_chart_svg, render_vedic_chart_svg_on_canvas
from astrologymod.vedic.drishti import has_drishti
from astrologymod.vedic.preset import effective_astrocfg
from astrologymod.vedic.rashi import whole_sign_house
from astrologymod.timezone_utils import localize_naive, naive_utc, utc_offset_timedelta

from astrology_app.debug import dprint
import astrology_app.globals as g
from astrology_app.paths import DATADIR

# Western SVG template design size (astrology-svg.xml).
_WESTERN_DESIGN_W = 772.2
_WESTERN_DESIGN_H = 546.0
# Wheel sign glyphs only (planets use separate templates).
_ZODIAC_SYMBOL_SCALE = 0.9
# Marker in generated SVG (verify placement + scale are active).
_ZODIAC_GLYPH_MARKER = 'openastro-org-s90'


def _escape_svg_text(value):
	"""Escape text embedded in generated SVG."""
	return xml_escape(str(value))


class AstrologyInstance:
	"""Chart state, ephemeris, aspects, and SVG generation.

	Holds the active chart datetime/location, Swiss Ephemeris results, aspect
	matrices, and methods to build wheel/table SVG from XML templates.
	"""

	def __init__(self):
		
		#screen size
		#displayManager = Gdk.display_manager_get()
		#display = displayManager.get_default_display()
		self.screen_width, self.screen_height = g4.screen_size()
		# Main chart pane size (pixels); set from the drawing area before makeSVG().
		self.chart_viewport_w = None
		self.chart_viewport_h = None

		#get label configuration
		self.label = g.db.getLabel()

		#check for home
		self.home_location,self.home_geolat,self.home_geolon,self.home_countrycode,self.home_timezonestr = g.db.getSettingsLocation()		
		if self.home_location == '' or self.home_geolat == '' or self.home_geolon == '':
			dprint('Unknown home location, asking for new')
			self.ask_for_home = True
			self.home_location='Amsterdam'
			self.home_geolon=6.219530
			self.home_geolat=52.120710
			self.home_countrycode='NL'
			self.home_timezonestr='Europe/Amsterdam'
		else:	
			self.ask_for_home = False
			dprint('known home location: %s %s %s' % (self.home_location, self.home_geolat, self.home_geolon))
			
		#default location
		self.location=self.home_location
		self.geolat=float(self.home_geolat)
		self.geolon=float(self.home_geolon)
		self.countrycode=self.home_countrycode
		self.timezonestr=self.home_timezonestr
		
		#current datetime
		now = datetime.datetime.now()

		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = localize_naive(dt_input, self.timezonestr)
		
		#naive utc datetime object
		dt_utc = naive_utc(dt)

		#Default
		self.name=_("Here and Now")
		self.charttype=self.label["radix"]
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		self.timezone=self.offsetToTz(dt.utcoffset())
		self.altitude=25
		self.geonameid=None
		
		#Make locals
		self.utcToLocal()
		
		#configuration
		#ZOOM 1 = 100%
		self.zoom=1
		self.type="Radix"
		
		#Default dpi for svg
		# Rsvg.set_default_dpi(400)  # no-op on GTK4

		#12 zodiacs
		self.zodiac = ['aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces']
		self.zodiac_short = ['Ari','Tau','Gem','Cnc','Leo','Vir','Lib','Sco','Sgr','Cap','Aqr','Psc']
		self.zodiac_color = ['#482900','#6b3d00','#5995e7','#2b4972','#c54100','#2b286f','#69acf1','#ffd237','#ff7200','#863c00','#4f0377','#6cbfff']
		self.zodiac_element = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water']

		#get color configuration
		self.colors = g.db.getColors()
		
		return
		
	def utcToLocal(self):
		#make local time variables from global UTC
		h, m, s = self.decHour(self.hour)
		utc = datetime.datetime(self.year, self.month, self.day, h, m, s)
		tz = datetime.timedelta(seconds=float(self.timezone)*float(3600))
		loc = utc + tz
		self.year_loc = loc.year
		self.month_loc = loc.month
		self.day_loc = loc.day
		self.hour_loc = loc.hour
		self.minute_loc = loc.minute
		self.second_loc = loc.second
		#print some info
		dprint('utcToLocal: '+str(utc)+' => '+str(loc)+self.decTzStr(self.timezone))
	
	def localToSolar(self, newyear):
		solaryearsecs = 31556925.51 # 365 days, 5 hours, 48 minutes, 45.51 seconds
		dprint("localToSolar: from %s to %s" %(self.year,newyear))
		h,m,s = self.decHour(self.hour)
		dt_original = datetime.datetime(self.year,self.month,self.day,h,m,s)
		dt_new = datetime.datetime(newyear,self.month,self.day,h,m,s)
		dprint("localToSolar: first sun %s" % (self.planets_degree_ut[0]) )
		mdata = ephemeris.ephData(newyear,self.month,self.day,self.hour,self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,g.db.astrocfg)
		dprint("localToSolar: second sun %s" % (mdata.planets_degree_ut[0]) )
		sundiff = self.planets_degree_ut[0] - mdata.planets_degree_ut[0]
		dprint("localToSolar: sundiff %s" %(sundiff))
		sundelta = ( sundiff / 360.0 ) * solaryearsecs
		dprint("localToSolar: sundelta %s" % (sundelta))
		dt_delta = datetime.timedelta(seconds=int(sundelta))
		dt_new = dt_new + dt_delta
		mdata = ephemeris.ephData(dt_new.year,dt_new.month,dt_new.day,self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second),self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,g.db.astrocfg)
		dprint("localToSolar: new sun %s" % (mdata.planets_degree_ut[0]))
		
		#get precise
		step = 0.000011408 # 1 seconds in degrees
		sundiff = self.planets_degree_ut[0] - mdata.planets_degree_ut[0]
		sundelta = sundiff / step
		dt_delta = datetime.timedelta(seconds=int(sundelta))
		dt_new = dt_new + dt_delta
		mdata = ephemeris.ephData(dt_new.year,dt_new.month,dt_new.day,self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second),self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,g.db.astrocfg)
		dprint("localToSolar: new sun #2 %s" % (mdata.planets_degree_ut[0]))

		step = 0.000000011408 # 1 milli seconds in degrees
		sundiff = self.planets_degree_ut[0] - mdata.planets_degree_ut[0]
		sundelta = sundiff / step
		dt_delta = datetime.timedelta(milliseconds=int(sundelta))
		dt_new = dt_new + dt_delta
		mdata = ephemeris.ephData(dt_new.year,dt_new.month,dt_new.day,self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second),self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,g.db.astrocfg)
		dprint("localToSolar: new sun #3 %s" % (mdata.planets_degree_ut[0]))	
		
		self.s_year = dt_new.year
		self.s_month = dt_new.month
		self.s_day = dt_new.day
		self.s_hour = self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second)
		self.s_geolon = self.geolon
		self.s_geolat = self.geolat
		self.s_altitude = self.altitude
		self.type = "Solar"
		g.astrology_chart.charttype="%s (%s-%02d-%02d %02d:%02d:%02d UTC)" % (g.astrology_chart.label["solar"],self.s_year,self.s_month,self.s_day,dt_new.hour,dt_new.minute,dt_new.second)
		g.astrology_chart.transit=False	
		return
		
	def localToSecondaryProgression(self,dt):
		
		#remove timezone
		dt_utc = dt - datetime.timedelta(seconds=float(self.timezone)*float(3600))
		h,m,s = self.decHour(self.hour)
		dt_new = ephemeris.years_diff(self.year,self.month,self.day,self.hour,
			dt_utc.year,dt_utc.month,dt_utc.day,self.decHourJoin(dt_utc.hour,
			dt_utc.minute,dt_utc.second))
	
		self.sp_year = dt_new.year
		self.sp_month = dt_new.month
		self.sp_day = dt_new.day
		self.sp_hour = self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second)
		self.sp_geolon = self.geolon
		self.sp_geolat = self.geolat
		self.sp_altitude = self.altitude
		self.houses_override = [dt_new.year,dt_new.month,dt_new.day,self.hour]

		dprint("localToSecondaryProgression: got UTC %s-%s-%s %s:%s:%s"%(
			dt_new.year,dt_new.month,dt_new.day,dt_new.hour,dt_new.minute,dt_new.second))
			
		self.type = "SecondaryProgression"
		g.astrology_chart.charttype="%s (%s-%02d-%02d %02d:%02d)" % (g.astrology_chart.label["secondary_progressions"],dt.year,dt.month,dt.day,dt.hour,dt.minute)
		g.astrology_chart.transit=False
		return

	def set_chart_viewport(self, width, height):
		"""Remember the chart drawing area size for Western/Vedic main SVG output."""
		if width is None or height is None:
			return
		w, h = int(width), int(height)
		if w < 200 or h < 200:
			return
		self.chart_viewport_w = w
		self.chart_viewport_h = h
	
	def makeSVG(self, printing=None):
		"""Compute chart data and write wheel/table SVG files.

		Args:
			printing: If set, use print-sized templates and filenames.

		Returns:
			str: Path to the main chart SVG (``g.cfg.tempfilename`` or print variant).
		"""
		#empty element points
		self.fire=0.0
		self.earth=0.0
		self.air=0.0
		self.water=0.0
			
		#get database planet settings	
		self.planets = g.db.getSettingsPlanet()
		
		#get database aspect settings
		self.aspects = g.db.getSettingsAspect()

		astro_cfg = effective_astrocfg(g.db.astrocfg)
		
		#Combine module data
		if self.type == "Combine":
			#make calculations
			module_data = ephemeris.ephData(self.c_year,self.c_month,self.c_day,self.c_hour,self.c_geolon,self.c_geolat,self.c_altitude,self.planets,self.zodiac,astro_cfg)
		
		#Solar module data
		if self.type == "Solar":
			module_data = ephemeris.ephData(self.s_year,self.s_month,self.s_day,self.s_hour,self.s_geolon,self.s_geolat,self.s_altitude,self.planets,self.zodiac,astro_cfg)
		
		elif self.type == "SecondaryProgression":
			module_data = ephemeris.ephData(self.sp_year,self.sp_month,self.sp_day,self.sp_hour,self.sp_geolon,self.sp_geolat,self.sp_altitude,self.planets,self.zodiac,astro_cfg,houses_override=self.houses_override)				
			
		elif self.type == "Transit" or self.type == "Composite":
			module_data = ephemeris.ephData(self.year,self.month,self.day,self.hour,self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,astro_cfg)
			t_module_data = ephemeris.ephData(self.t_year,self.t_month,self.t_day,self.t_hour,self.t_geolon,self.t_geolat,self.t_altitude,self.planets,self.zodiac,astro_cfg)
		
		else:
			#make calculations
			module_data = ephemeris.ephData(self.year,self.month,self.day,self.hour,self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,astro_cfg)

		#Transit module data
		if self.type == "Transit" or self.type == "Composite":
			#grab transiting module data
			self.t_planets_sign = t_module_data.planets_sign
			self.t_planets_degree = t_module_data.planets_degree
			self.t_planets_degree_ut = t_module_data.planets_degree_ut
			self.t_planets_retrograde = t_module_data.planets_retrograde
			self.t_houses_degree = t_module_data.houses_degree
			self.t_houses_sign = t_module_data.houses_sign
			self.t_houses_degree_ut = t_module_data.houses_degree_ut
			
		#grab normal module data
		self.planets_sign = module_data.planets_sign
		self.planets_degree = module_data.planets_degree
		self.planets_degree_ut = module_data.planets_degree_ut
		self.planets_retrograde = module_data.planets_retrograde
		self.houses_degree = module_data.houses_degree
		self.houses_sign = module_data.houses_sign
		self.houses_degree_ut = module_data.houses_degree_ut		
		self.lunar_phase = module_data.lunar_phase

		#make composite averages
		if self.type == "Composite":
			#new houses
			asc = self.houses_degree_ut[0]
			t_asc = self.t_houses_degree_ut[0]
			for i in range(12):
				#difference in distances measured from ASC
				diff = self.houses_degree_ut[i] - asc
				if diff < 0:
					diff = diff + 360.0
				t_diff = self.t_houses_degree_ut[i] - t_asc
				if t_diff < 0:
					t_diff = t_diff + 360.0	
				newdiff = (diff + t_diff) / 2.0
				
				#new ascendant
				if asc > t_asc:
					diff = asc - t_asc
					if diff > 180:
						diff = 360.0 - diff
						nasc = asc + (diff / 2.0)
					else:
						nasc = t_asc + (diff / 2.0)
				else:
					diff = t_asc - asc
					if diff > 180:
						diff = 360.0 - diff
						nasc = t_asc + (diff / 2.0)
					else:
						nasc = asc + (diff / 2.0)
				
				#new house degrees
				self.houses_degree_ut[i] = nasc + newdiff
				if self.houses_degree_ut[i] > 360:
					self.houses_degree_ut[i] = self.houses_degree_ut[i] - 360.0	
					
				#new house sign				
				for x in range(len(self.zodiac)):
					deg_low=float(x*30)
					deg_high=float((x+1)*30)
					if self.houses_degree_ut[i] >= deg_low:
						if self.houses_degree_ut[i] < deg_high or (x == 11 and self.houses_degree_ut[i] <= deg_high):
							self.houses_sign[i]=x
							self.houses_degree[i] = self.houses_degree_ut[i] - deg_low

			#new planets
			for i in range(23):
				#difference in degrees
				p1 = self.planets_degree_ut[i]
				p2 = self.t_planets_degree_ut[i]
				if p1 > p2:
					diff = p1 - p2
					if diff > 180:
						diff = 360.0 - diff
						self.planets_degree_ut[i] = (diff / 2.0) + p1
					else:
						self.planets_degree_ut[i] = (diff / 2.0) + p2
				else:
					diff = p2 - p1
					if diff > 180:
						diff = 360.0 - diff
						self.planets_degree_ut[i] = (diff / 2.0) + p2
					else:
						self.planets_degree_ut[i] = (diff / 2.0) + p1
				
				if self.planets_degree_ut[i] > 360:
					self.planets_degree_ut[i] = self.planets_degree_ut[i] - 360.0
			
			#list index 23 is asc, 24 is Mc, 25 is Dsc, 26 is Ic
			self.planets_degree_ut[23] = self.houses_degree_ut[0]
			self.planets_degree_ut[24] = self.houses_degree_ut[9]
			self.planets_degree_ut[25] = self.houses_degree_ut[6]
			self.planets_degree_ut[26] = self.houses_degree_ut[3]
								
			#new planet signs
			for i in range(27):
				for x in range(len(self.zodiac)):
					deg_low=float(x*30)
					deg_high=float((x+1)*30)
					if self.planets_degree_ut[i] >= deg_low:
						if self.planets_degree_ut[i] < deg_high or (x == 11 and self.planets_degree_ut[i] <= deg_high):
							self.planets_sign[i]=x
							self.planets_degree[i] = self.planets_degree_ut[i] - deg_low
							self.planets_retrograde[i] = False

		self._refresh_vedic_snapshot()
		
		# Western wheel canvas (OpenAstro.org): fixed 772.2×546 viewBox, window-sized width/height.
		if printing == None:
			self.screen_width, self.screen_height = g4.screen_size()
			ratio = float(self.screen_width) / float(self.screen_height)
			if ratio < 1.3:
				wm_off = 130
			else:
				wm_off = 100
			if self.chart_viewport_w and self.chart_viewport_h:
				svgHeight = float(self.chart_viewport_h)
				svgWidth = float(self.chart_viewport_w)
			else:
				svgHeight = float(self.screen_height) - wm_off
				svgWidth = float(self.screen_width) - 5.0
			rotate = "0"
			translate = "0"
			viewbox = '0 0 772.2 546.0'
		else:
			svgWidth = float(printing['width'])
			svgHeight = float(printing['height'])
			rotate = "0"
			translate = "0"
			viewbox = '0 0 772.2 546.0'

		if self._use_vedic_main_chart():
			path = g.cfg.tempfilenameprint if printing else g.cfg.tempfilename
			self._write_vedic_main_svg(path, int(svgWidth), int(svgHeight))
			dprint('Creating Vedic main chart: %s' % path)
			return path
		
		#template dictionary		
		td = dict()
		r=240
		if(g.db.astrocfg['chartview']=="european"):
			self.c1=56
			self.c2=92
			self.c3=112
		else:				
			self.c1=0
			self.c2=36
			self.c3=120
		
		#transit
		if self.type == "Transit":
			td['transitRing']=self.transitRing( r )
			td['degreeRing']=self.degreeTransitRing( r )
			#circles
			td['c1'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-36) + '"'
			td['c1style'] = 'fill: none; stroke: %s; stroke-width: 1px; stroke-opacity:.4;'%(self.colors['zodiac_transit_ring_2'])
			td['c2'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-72) + '"'
			td['c2style'] = 'fill: %s; fill-opacity:.4; stroke: %s; stroke-opacity:.4; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_transit_ring_1'])
			td['c3'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-160) + '"'
			td['c3style'] = 'fill: %s; fill-opacity:.8; stroke: %s; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_transit_ring_0'])
			td['makeAspects'] = self.makeAspectsTransit( r , (r-160))
			td['makeAspectGrid'] = self.makeAspectTransitGrid( r )
			td['makePatterns'] = ''
		else:
			td['transitRing']=""
			td['degreeRing']=self.degreeRing( r )
			#circles
			td['c1'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c1) + '"'
			td['c1style'] = 'fill: none; stroke: %s; stroke-width: 1px; '%(self.colors['zodiac_radix_ring_2'])
			td['c2'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c2) + '"'
			td['c2style'] = 'fill: %s; fill-opacity:.2; stroke: %s; stroke-opacity:.4; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_1'])
			td['c3'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c3) + '"'
			td['c3style'] = 'fill: %s; fill-opacity:.8; stroke: %s; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_0'])
			if self.vedic is not None:
				td['makeAspects'] = self.makeVedicDrishti( r , (r-self.c3))
				td['makeAspectGrid'] = ''
				td['makePatterns'] = ''
			else:
				td['makeAspects'] = self.makeAspects( r , (r-self.c3))
				td['makeAspectGrid'] = self.makeAspectGrid( r )
				td['makePatterns'] = self.makePatterns()

		td['circleX']=str(0)
		td['circleY']=str(0)
		td['svgWidth']=str(svgWidth)
		td['svgHeight']=str(svgHeight)
		td['viewbox']=viewbox
		td['stringTitle'] = _escape_svg_text(self.name)
		td['stringName'] = _escape_svg_text(self.charttype)
		
		#bottom left
		siderealmode_chartview={
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

		if g.db.astrocfg.get('tradition') == 'vedic' and self.vedic is not None:
			td['bottomLeft1']=_("Vedic (Jyotish)")
			td['bottomLeft2']='%s — %s' % (
				self.vedic.lagna_rashi.name,
				self.vedic.panchanga.nakshatra,
			)
		elif g.db.astrocfg['zodiactype'] == 'sidereal':
			td['bottomLeft1']=_("Sidereal")
			td['bottomLeft2']=siderealmode_chartview[g.db.astrocfg['siderealmode']]
		else:
			td['bottomLeft1']=_("Tropical")
			td['bottomLeft2'] = '%s: %s (%s) %s (%s)' % (_("Lunar Phase"),self.lunar_phase['sun_phase'],_("Sun"),self.lunar_phase['moon_phase'],_("Moon"))
		
		if g.db.astrocfg.get('tradition') == 'vedic' and self.vedic is not None:
			td['bottomLeft3'] = '%s: %s (%s)' % (
				_("Tithi"), self.vedic.panchanga.tithi, self.vedic.panchanga.tithi_name)
			if self.vedic.primary_dasha:
				p0 = self.vedic.primary_dasha[0]
				td['bottomLeft4'] = '%s %s: %s' % (_("Dasha"), p0.lord_label, p0.end.strftime('%Y-%m-%d'))
			else:
				td['bottomLeft4'] = ''
		else:
			td['bottomLeft3'] = '%s: %s' % (_("Lunar Phase"),self.dec2deg(self.lunar_phase['degrees']))
			td['bottomLeft4'] = ''
	
		#lunar phase
		deg=self.lunar_phase['degrees']

		if(deg<90.0):
			maxr=deg
			if(deg>80.0): maxr=maxr*maxr
			lfcx=20.0+(deg/90.0)*(maxr+10.0)
			lfr=10.0+(deg/90.0)*maxr
			lffg,lfbg=self.colors["lunar_phase_0"],self.colors["lunar_phase_1"]

		elif(deg<180.0):
			maxr=180.0-deg
			if(deg<100.0): maxr=maxr*maxr
			lfcx=20.0+((deg-90.0)/90.0*(maxr+10.0))-(maxr+10.0)
			lfr=10.0+maxr-((deg-90.0)/90.0*maxr)
			lffg,lfbg=self.colors["lunar_phase_1"],self.colors["lunar_phase_0"]

		elif(deg<270.0):
			maxr=deg-180.0
			if(deg>260.0): maxr=maxr*maxr
			lfcx=20.0+((deg-180.0)/90.0*(maxr+10.0))
			lfr=10.0+((deg-180.0)/90.0*maxr)
			lffg,lfbg=self.colors["lunar_phase_1"],self.colors["lunar_phase_0"]

		elif(deg<361):
			maxr=360.0-deg
			if(deg<280.0): maxr=maxr*maxr
			lfcx=20.0+((deg-270.0)/90.0*(maxr+10.0))-(maxr+10.0)
			lfr=10.0+maxr-((deg-270.0)/90.0*maxr)
			lffg,lfbg=self.colors["lunar_phase_0"],self.colors["lunar_phase_1"]

		td['lunar_phase_fg'] = lffg		
		td['lunar_phase_bg'] = lfbg
		td['lunar_phase_cx'] = '%s' %(lfcx)
		td['lunar_phase_r'] = '%s' %(lfr)
		td['lunar_phase_outline'] = self.colors["lunar_phase_2"]

		#rotation based on latitude
		td['lunar_phase_rotate'] = "%s" % (-90.0-self.geolat)

		#stringlocation
		if len(self.location) > 35:
			split=self.location.split(",")
			if len(split) > 1:
				td['stringLocation']=split[0]+", "+split[-1]
				if len(td['stringLocation']) > 35:
					td['stringLocation'] = td['stringLocation'][:35]+"..."
			else:
				td['stringLocation']=self.location[:35]+"..."
		else:
			td['stringLocation']=self.location
		td['stringDateTime']=str(self.year_loc)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':self.month_loc,'#2':self.day_loc,'#3':self.hour_loc,'#4':self.minute_loc,'#5':self.second_loc} + self.decTzStr(self.timezone)
		td['stringLat']="%s: %s" %(self.label['latitude'],self.lat2str(self.geolat))
		td['stringLon']="%s: %s" %(self.label['longitude'],self.lon2str(self.geolon))
		postype={"geo":self.label["apparent_geocentric"],"truegeo":self.label["true_geocentric"],
				"topo":self.label["topocentric"],"helio":self.label["heliocentric"]}
		td['stringPosition']=postype[g.db.astrocfg['postype']]

		#paper_color_X
		td['paper_color_0']=self.colors["paper_0"]
		td['paper_color_1']=self.colors["paper_1"]
		
		
		#planets_color_X
		for i in range(len(self.planets)):
			td['planets_color_%s'%(i)]=self.colors["planet_%s"%(i)]
		
		#zodiac_color_X
		for i in range(12):
			td['zodiac_color_%s'%(i)]=self.colors["zodiac_icon_%s" %(i)]
		
		#orb_color_X
		for i in range(len(self.aspects)):
			td['orb_color_%s'%(self.aspects[i]['degree'])]=self.colors["aspect_%s" %(self.aspects[i]['degree'])]
		
		#config
		td['cfgZoom']=str(self.zoom)
		td['cfgRotate']=rotate
		td['cfgTranslate']=translate
		
		#functions
		td['makeZodiac'] = self.makeZodiac( r )
		td['makeHouses'] = self.makeHouses( r )
		td['makePlanets'] = self.makePlanets( r )
		td['makeElements'] = self.makeElements( r )
		if self.vedic is not None:
			td['makePlanetGrid'] = self.makeVedicPlanetGrid()
			td['makeHousesGrid'] = self.makeVedicHousesGrid()
		else:
			td['makePlanetGrid'] = self.makePlanetGrid()
			td['makeHousesGrid'] = self.makeHousesGrid()
				
		with open(g.cfg.xml_svg, encoding='utf-8') as f:
			template = Template(f.read()).safe_substitute(td)

		out_path = g.cfg.tempfilenameprint if printing else g.cfg.tempfilename
		if printing:
			dprint("Printing SVG: lat="+str(self.geolat)+' lon='+str(self.geolon)+' loc='+self.location)
		else:
			dprint("Creating SVG: lat="+str(self.geolat)+' lon='+str(self.geolon)+' loc='+self.location)
		with open(out_path, 'w', encoding='utf-8') as f:
			f.write(template)

		#return filename
		return g.cfg.tempfilename

	#draw transit ring
	def transitRing( self , r ):
		out = '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 36px; stroke-opacity: .4;"/>' % (r,r,r-18,self.colors['paper_1'])
		out += '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 1px; stroke-opacity: .6;"/>' % (r,r,r,self.colors['zodiac_transit_ring_3'])
		return out	
	
	#draw degree ring
	def degreeRing( self , r ):
		out=''
		for i in range(72):
			offset = float(i*5) - self.houses_degree_ut[6]
			if offset < 0:
				offset = offset + 360.0
			elif offset > 360:
				offset = offset - 360.0
			x1 = self.sliceToX( 0 , r-self.c1 , offset ) + self.c1
			y1 = self.sliceToY( 0 , r-self.c1 , offset ) + self.c1
			x2 = self.sliceToX( 0 , r+2-self.c1 , offset ) - 2 + self.c1
			y2 = self.sliceToY( 0 , r+2-self.c1 , offset ) - 2 + self.c1
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: 1px; stroke-opacity:.9;"/>\n' % (
				x1,y1,x2,y2,self.colors['paper_0'] )
		return out
		
	def degreeTransitRing( self , r ):
		out=''
		for i in range(72):
			offset = float(i*5) - self.houses_degree_ut[6]
			if offset < 0:
				offset = offset + 360.0
			elif offset > 360:
				offset = offset - 360.0
			x1 = self.sliceToX( 0 , r , offset )
			y1 = self.sliceToY( 0 , r , offset )
			x2 = self.sliceToX( 0 , r+2 , offset ) - 2
			y2 = self.sliceToY( 0 , r+2 , offset ) - 2
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>\n' % (
				x1,y1,x2,y2 )
		return out
	
	#floating latitude an longitude to string
	def lat2str( self, coord ):
		sign=self.label["north"]
		if coord < 0.0:
			sign=self.label["south"]
			coord = abs(coord)
		deg = int(coord)
		min = int( (float(coord) - deg) * 60 )
		sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
		return "%s°%s'%s\" %s" % (deg,min,sec,sign)
		
	def lon2str( self, coord ):
		sign=self.label["east"]
		if coord < 0.0:
			sign=self.label["west"]
			coord = abs(coord)
		deg = int(coord)
		min = int( (float(coord) - deg) * 60 )
		sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
		return "%s°%s'%s\" %s" % (deg,min,sec,sign)
	
	#decimal hour to minutes and seconds
	def decHour( self , input ):
		hours=int(input)
		mands=(input-hours)*60.0
		mands=round(mands,5)
		minutes=int(mands)
		seconds=int(round((mands-minutes)*60))
		return [hours,minutes,seconds]
		
	#join hour, minutes, seconds, timezone integere to hour float
	def decHourJoin( self , inH , inM , inS ):
		dh = float(inH)
		dm = float(inM)/60
		ds = float(inS)/3600
		output = dh + dm + ds
		return output

	#Datetime offset to float in hours	
	def offsetToTz( self, dtoffset ):
		dh = float(dtoffset.days * 24)
		sh = float(dtoffset.seconds / 3600.0)
		output = dh + sh
		return output
	
	
	#decimal timezone string
	def decTzStr( self, tz ):
		if tz > 0:
			h = int(tz)
			m = int((float(tz)-float(h))*float(60))
			return " [+%(#1)02d:%(#2)02d]" % {'#1':h,'#2':m}
		else:
			h = int(tz)
			m = int((float(tz)-float(h))*float(60))/-1
			return " [-%(#1)02d:%(#2)02d]" % {'#1':h/-1,'#2':m}

	#degree difference
	def degreeDiff( self , a , b ):
		out=float()
		if a > b:
			out=a-b
		if a < b:
			out=b-a
		if out > 180.0:
			out=360.0-out
		return out

	#decimal to degrees (a°b'c")
	def dec2deg( self , dec , type="3"):
		dec=float(dec)
		a=int(dec)
		a_new=(dec-float(a)) * 60.0
		b_rounded = int(round(a_new))
		b=int(a_new)
		c=int(round((a_new-float(b))*60.0))
		if type=="3":
			out = '%(#1)02d&#176;%(#2)02d&#39;%(#3)02d&#34;' % {'#1':a,'#2':b, '#3':c}
		elif type=="2":
			out = '%(#1)02d&#176;%(#2)02d&#39;' % {'#1':a,'#2':b_rounded}
		elif type=="1":
			out = '%(#1)02d&#176;' % {'#1':a}
		return str(out)
	
	#draw svg aspects: ring, aspect ring, degreeA degreeB
	def drawAspect( self , r , ar , degA , degB , color):
			offset = (int(self.houses_degree_ut[6]) / -1) + int(degA)
			x1 = self.sliceToX( 0 , ar , offset ) + (r-ar)
			y1 = self.sliceToY( 0 , ar , offset ) + (r-ar)
			offset = (int(self.houses_degree_ut[6]) / -1) + int(degB)
			x2 = self.sliceToX( 0 , ar , offset ) + (r-ar)
			y2 = self.sliceToY( 0 , ar , offset ) + (r-ar)
			out = '			<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+color+'; stroke-width: 1; stroke-opacity: .9;"/>\n'
			return out
	
	def sliceToX( self , slice , r, offset):
		plus = (math.pi * offset) / 180
		radial = ((math.pi/6) * slice) + plus
		return r * (math.cos(radial)+1)
	
	def sliceToY( self , slice , r, offset):
		plus = (math.pi * offset) / 180
		radial = ((math.pi/6) * slice) + plus
		return r * ((math.sin(radial)/-1)+1)
	
	def zodiacSlice( self , num , r , style,  type):
		#pie slices
		if g.db.astrocfg["houses_system"] == "G":
			offset = 360 - self.houses_degree_ut[18]
		else:
			offset = 360 - self.houses_degree_ut[6]
		#check transit
		if self.type == "Transit":
			dropin=0
		else:
			dropin=self.c1		
		slice = '<path d="M' + str(r) + ',' + str(r) + ' L' + str(dropin + self.sliceToX(num,r-dropin,offset)) + ',' + str( dropin + self.sliceToY(num,r-dropin,offset)) + ' A' + str(r-dropin) + ',' + str(r-dropin) + ' 0 0,0 ' + str(dropin + self.sliceToX(num+1,r-dropin,offset)) + ',' + str(dropin + self.sliceToY(num+1,r-dropin,offset)) + ' z" style="' + style + '"/>'
		# Symbols (OpenAstro.org/openastro — translate(-16,-16) + use x/y on ring point)
		offset = offset + 15
		if self.type == "Transit":
			dropin=54
		else:
			dropin=18+self.c1
		sx = dropin + self.sliceToX(num, r - dropin, offset)
		sy = dropin + self.sliceToY(num, r - dropin, offset)
		sc = _ZODIAC_SYMBOL_SCALE
		# OpenAstro anchor + scale at ring point (wheel signs only).
		sign = (
			'<g transform="translate(-16,-16) translate(' + str(sx) + ',' + str(sy)
			+ ') scale(' + str(sc) + ') translate(' + str(-sx) + ',' + str(-sy)
			+ ')"><use x="' + str(sx) + '" y="' + str(sy)
			+ '" xlink:href="#' + type + '" /></g>\n'
		)
		return slice + '\n' + sign
	
	def makeZodiac( self , r ):
		output = '<!-- zodiac-glyphs:' + _ZODIAC_GLYPH_MARKER + ' -->\n'
		for i in range(len(self.zodiac)):
			output = output + self.zodiacSlice( i , r , "fill:" + self.colors["zodiac_bg_%s"%(i)] + "; fill-opacity: 0.5;" , self.zodiac[i]) + '\n'
		return output
		
	def makeHouses( self , r ):
		path = ""
		if g.db.astrocfg["houses_system"] == "G":
			xr = 36
		else:
			xr = 12
		for i in range(xr):
			#check transit
			if self.type == "Transit":
				dropin=160
				roff=72
				t_roff=36
			else:
				dropin=self.c3
				roff=self.c1
				
			#offset is negative desc houses_degree_ut[6]
			offset = (int(self.houses_degree_ut[int(xr/2)]) / -1) + int(self.houses_degree_ut[i])
			x1 = self.sliceToX( 0 , (r-dropin) , offset ) + dropin
			y1 = self.sliceToY( 0 , (r-dropin) , offset ) + dropin
			x2 = self.sliceToX( 0 , r-roff , offset ) + roff
			y2 = self.sliceToY( 0 , r-roff , offset ) + roff
			
			if i < (xr-1):		
				text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[(i+1)], self.houses_degree_ut[i] ) / 2 )
			else:
				text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[0], self.houses_degree_ut[(xr-1)] ) / 2 )

			#mc, asc, dsc, ic
			if i == 0:
				linecolor=self.planets[23]['color']
			elif i == 9:
				linecolor=self.planets[24]['color']	
			elif i == 6:
				linecolor=self.planets[25]['color']
			elif i == 3:
				linecolor=self.planets[26]['color']
			else:
				linecolor=self.colors['houses_radix_line']

			#transit houses lines
			if self.type == "Transit":
				#degrees for point zero
				zeropoint = 360 - self.houses_degree_ut[6]
				t_offset = zeropoint + self.t_houses_degree_ut[i]
				if t_offset > 360:
					t_offset = t_offset - 360
				t_x1 = self.sliceToX( 0 , (r-t_roff) , t_offset ) + t_roff
				t_y1 = self.sliceToY( 0 , (r-t_roff) , t_offset ) + t_roff
				t_x2 = self.sliceToX( 0 , r , t_offset )
				t_y2 = self.sliceToY( 0 , r , t_offset )
				if i < 11:		
					t_text_offset = t_offset + int(self.degreeDiff( self.t_houses_degree_ut[(i+1)], self.t_houses_degree_ut[i] ) / 2 )
				else:
					t_text_offset = t_offset + int(self.degreeDiff( self.t_houses_degree_ut[0], self.t_houses_degree_ut[11] ) / 2 )
				#linecolor
				if i == 0 or i == 9 or i == 6 or i == 3:
					t_linecolor=linecolor
				else:
					t_linecolor = self.colors['houses_transit_line']			
				xtext = self.sliceToX( 0 , (r-8) , t_text_offset ) + 8
				ytext = self.sliceToY( 0 , (r-8) , t_text_offset ) + 8
				path = path + '<text style="fill: #00f; fill-opacity: .4; font-size: 14px"><tspan x="'+str(xtext-3)+'" y="'+str(ytext+3)+'">'+str(i+1)+'</tspan></text>\n'
				path = path + '<line x1="'+str(t_x1)+'" y1="'+str(t_y1)+'" x2="'+str(t_x2)+'" y2="'+str(t_y2)+'" style="stroke: '+t_linecolor+'; stroke-width: 2px; stroke-opacity:.3;"/>\n'				
				
			#if transit			
			if self.type == "Transit":
				dropin=84
			elif g.db.astrocfg["chartview"] == "european":
				dropin=100
			else:		
				dropin=48
				
			xtext = self.sliceToX( 0 , (r-dropin) , text_offset ) + dropin #was 132
			ytext = self.sliceToY( 0 , (r-dropin) , text_offset ) + dropin #was 132
			path = path + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+linecolor+'; stroke-width: 2px; stroke-dasharray:3,2; stroke-opacity:.4;"/>\n'
			path = path + '<text style="fill: #f00; fill-opacity: .6; font-size: 14px"><tspan x="'+str(xtext-3)+'" y="'+str(ytext+3)+'">'+str(i+1)+'</tspan></text>\n'
						
		return path
	
	def makePlanets( self , r ):
		
		planets_degut={}
		
		diff=range(len(self.planets))
		vedic_mode = g.db.astrocfg.get('tradition') == 'vedic'
		for i in range(len(self.planets)):
			if vedic_mode and i not in DEFAULT_GRAHA_INDICES:
				continue
			if self.planets[i]['visible'] == 1:
				#list of planets sorted by degree				
				planets_degut[self.planets_degree_ut[i]]=i
			
			#element: get extra points if planet is in own zodiac
			pz = self.planets[i]['zodiac_relation']
			cz = self.planets_sign[i]
			extrapoints = 0
			if pz != -1:
				for e in range(len(pz.split(','))):
					if int(pz.split(',')[e]) == int(cz):
						extrapoints = 10

			#calculate element points for all planets
			ele = self.zodiac_element[self.planets_sign[i]]			
			if ele == "fire":
				self.fire = self.fire + self.planets[i]['element_points'] + extrapoints
			elif ele == "earth":
				self.earth = self.earth + self.planets[i]['element_points'] + extrapoints
			elif ele == "air":
				self.air = self.air + self.planets[i]['element_points'] + extrapoints
			elif ele == "water":
				self.water = self.water + self.planets[i]['element_points'] + extrapoints
				
		output = ""	
		keys = list(planets_degut.keys())
		keys.sort()
		switch=0
		
		planets_degrouped = {}
		groups = []
		planets_by_pos = list(range(len(planets_degut)))
		planet_drange = 3.4
		#get groups closely together
		group_open=False
		for e in range(len(keys)):
			i=planets_degut[keys[e]]
			#get distances between planets
			if e == 0:
				prev = self.planets_degree_ut[planets_degut[keys[-1]]]
				next = self.planets_degree_ut[planets_degut[keys[1]]]
			elif e == (len(keys)-1):
				prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
				next = self.planets_degree_ut[planets_degut[keys[0]]]	
			else:
				prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
				next = self.planets_degree_ut[planets_degut[keys[e+1]]]
			diffa=self.degreeDiff(prev,self.planets_degree_ut[i])
			diffb=self.degreeDiff(next,self.planets_degree_ut[i])
			planets_by_pos[e]=[i,diffa,diffb]
			#print "%s %s %s" % (self.planets[i]['label'],diffa,diffb)
			if (diffb < planet_drange):
				if group_open:
					groups[-1].append([e,diffa,diffb,self.planets[planets_degut[keys[e]]]["label"]])
				else:
					group_open=True
					groups.append([])
					groups[-1].append([e,diffa,diffb,self.planets[planets_degut[keys[e]]]["label"]])
			else:
				if group_open:
					groups[-1].append([e,diffa,diffb,self.planets[planets_degut[keys[e]]]["label"]])				
				group_open=False	
		
		def zero(x): return 0
		planets_delta = list(map(zero,range(len(self.planets))))

		#print groups
		#print planets_by_pos
		for a in range(len(groups)):
			#Two grouped planets			
			if len(groups[a]) == 2:
				next_to_a = groups[a][0][0]-1
				if groups[a][1][0] == (len(planets_by_pos)-1):
					next_to_b = 0
				else:
					next_to_b = groups[a][1][0]+1
				#if both planets have room
				if (groups[a][0][1] > (2*planet_drange))&(groups[a][1][2] > (2*planet_drange)):
					planets_delta[groups[a][0][0]]=-(planet_drange-groups[a][0][2])/2
					planets_delta[groups[a][1][0]]=+(planet_drange-groups[a][0][2])/2
				#if planet a has room
				elif (groups[a][0][1] > (2*planet_drange)):
					planets_delta[groups[a][0][0]]=-planet_drange
				#if planet b has room
				elif (groups[a][1][2] > (2*planet_drange)):
					planets_delta[groups[a][1][0]]=+planet_drange
				
				#if planets next to a and b have room move them
				elif (planets_by_pos[next_to_a][1] > (2.4*planet_drange))&(planets_by_pos[next_to_b][2] > (2.4*planet_drange)):
					planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2)
					planets_delta[groups[a][0][0]]=-planet_drange*.5				
					planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2)
					planets_delta[groups[a][1][0]]=+planet_drange*.5	
					
				#if planet next to a has room move them
				elif (planets_by_pos[next_to_a][1] > (2*planet_drange)):
					planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2.5)
					planets_delta[groups[a][0][0]]=-planet_drange*1.2

				#if planet next to b has room move them
				elif (planets_by_pos[next_to_b][2] > (2*planet_drange)):
					planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2.5)
					planets_delta[groups[a][1][0]]=+planet_drange*1.2

			#Three grouped planets or more
			xl=len(groups[a])		
			if xl >= 3:
				
				available = groups[a][0][1]
				for f in range(xl):
					available += groups[a][f][2]
				need = (3*planet_drange)+(1.2*(xl-1)*planet_drange)
				leftover = available - need
				xa=groups[a][0][1]
				xb=groups[a][(xl-1)][2]
				
				#center
				if (xa > (need*.5)) & (xb > (need*.5)):
					startA = xa - (need*.5)
				#position relative to next planets
				else:
					startA=(leftover/(xa+xb))*xa
					startB=(leftover/(xa+xb))*xb
			
				if available > need:
					planets_delta[groups[a][0][0]]=startA-groups[a][0][1]+(1.5*planet_drange)
					for f in range(xl-1):
						planets_delta[groups[a][(f+1)][0]]=1.2*planet_drange+planets_delta[groups[a][f][0]]-groups[a][f][2]


		for e in range(len(keys)):
			i=planets_degut[keys[e]]

			#coordinates			
			if self.type == "Transit":
				if 22 < i < 27:
					rplanet = 76
				elif switch == 1:
					rplanet=110
					switch = 0
				else:
					rplanet=130
					switch = 1				
			else:
				#if 22 < i < 27 it is asc,mc,dsc,ic (angles of chart)
				#put on special line (rplanet is range from outer ring)
				amin,bmin,cmin=0,0,0				
				if g.db.astrocfg["chartview"] == "european":
					amin=74-10
					bmin=94-10
					cmin=40-10
				
				if 22 < i < 27:
					rplanet = 40-cmin
				elif switch == 1:
					rplanet=74-amin
					switch = 0
				else:
					rplanet=94-bmin
					switch = 1			
				
			rtext=45
			if g.db.astrocfg['houses_system'] == "G":
				offset = (int(self.houses_degree_ut[18]) / -1) + int(self.planets_degree_ut[i])
			else:
				offset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i]+planets_delta[e])
				trueoffset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i])
			planet_x = self.sliceToX( 0 , (r-rplanet) , offset ) + rplanet
			planet_y = self.sliceToY( 0 , (r-rplanet) , offset ) + rplanet
			if self.type == "Transit":
				scale=0.8
			elif g.db.astrocfg["chartview"] == "european":
				scale=0.8
				#line1
				x1=self.sliceToX( 0 , (r-self.c3) , trueoffset ) + self.c3
				y1=self.sliceToY( 0 , (r-self.c3) , trueoffset ) + self.c3
				x2=self.sliceToX( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				y2=self.sliceToY( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				color=self.planets[i]["color"]
				output += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.3;"/>\n' % (x1,y1,x2,y2,color)
				#line2
				x1=self.sliceToX( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				y1=self.sliceToY( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				x2=self.sliceToX( 0 , (r-rplanet-10) , offset ) + rplanet + 10
				y2=self.sliceToY( 0 , (r-rplanet-10) , offset ) + rplanet + 10
				output += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.5;"/>\n' % (x1,y1,x2,y2,color)
			else:
				scale=1
			#output planet			
			output = output + '<g transform="translate(-'+str(12*scale)+',-'+str(12*scale)+')"><g transform="scale('+str(scale)+')"><use x="' + str(planet_x*(1/scale)) + '" y="' + str(planet_y*(1/scale)) + '" xlink:href="#' + self.svgSafeHref(self.planets[i]['name']) + '" /></g></g>\n'
			
		#make transit degut and display planets
		if self.type == "Transit":
			group_offset={}
			t_planets_degut={}
			for i in range(len(self.planets)):
				group_offset[i]=0
				if self.planets[i]['visible'] == 1:
					t_planets_degut[self.t_planets_degree_ut[i]]=i
			t_keys = list(t_planets_degut.keys())
			t_keys.sort()
			

			#grab closely grouped planets
			groups=[]
			in_group=False
			for e in range(len(t_keys)):
				i_a=t_planets_degut[t_keys[e]]
				if e == (len(t_keys)-1):
					i_b=t_planets_degut[t_keys[0]]
				else:
					i_b=t_planets_degut[t_keys[e+1]]
				
				a=self.t_planets_degree_ut[i_a]
				b=self.t_planets_degree_ut[i_b]
				diff = self.degreeDiff(a,b)
				if diff <= 2.5:
					if in_group:
						groups[-1].append(i_b)
					else:
						groups.append([i_a])
						groups[-1].append(i_b)
						in_group=True
				else:
					in_group=False	
			#loop groups and set degrees display adjustment
			for i in range(len(groups)):
				if len(groups[i]) == 2:
					group_offset[groups[i][0]]=-1.0
					group_offset[groups[i][1]]=1.0
				elif len(groups[i]) == 3:
					group_offset[groups[i][0]]=-1.5
					group_offset[groups[i][1]]=0
					group_offset[groups[i][2]]=1.5
				elif len(groups[i]) == 4:
					group_offset[groups[i][0]]=-2.0
					group_offset[groups[i][1]]=-1.0
					group_offset[groups[i][2]]=1.0
					group_offset[groups[i][3]]=2.0					
			
			switch=0
			for e in range(len(t_keys)):
				i=t_planets_degut[t_keys[e]]
	
				if 22 < i < 27:
					rplanet = 9
				elif switch == 1:
					rplanet=18
					switch = 0
				else:
					rplanet=26
					switch = 1	
				
				zeropoint = 360 - self.houses_degree_ut[6]
				t_offset = zeropoint + self.t_planets_degree_ut[i]
				if t_offset > 360:
					t_offset = t_offset - 360
				planet_x = self.sliceToX( 0 , (r-rplanet) , t_offset ) + rplanet
				planet_y = self.sliceToY( 0 , (r-rplanet) , t_offset ) + rplanet
				output = output + '<g transform="translate(-6,-6)"><g transform="scale(0.5)"><use x="' + str(planet_x*2) + '" y="' + str(planet_y*2) + '" xlink:href="#' + self.svgSafeHref(self.planets[i]['name']) + '" /></g></g>\n'
				#transit planet line
				x1 = self.sliceToX( 0 , r+3 , t_offset ) - 3
				y1 = self.sliceToY( 0 , r+3 , t_offset ) - 3
				x2 = self.sliceToX( 0 , r-3 , t_offset ) + 3
				y2 = self.sliceToY( 0 , r-3 , t_offset ) + 3
				output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 1px; stroke-opacity:.8;"/>\n'
				
				#transit planet degree text
				rotate = self.houses_degree_ut[0] - self.t_planets_degree_ut[i]
				textanchor="end"
				t_offset += group_offset[i]
				rtext=-3.0
	
				if -90 > rotate > -270:
					rotate = rotate + 180.0
					textanchor="start"
				if 270 > rotate > 90:
					rotate = rotate - 180.0
					textanchor="start"
	
					
				if textanchor == "end":
					xo=1
				else:
					xo=-1				
				deg_x = self.sliceToX( 0 , (r-rtext) , t_offset + xo ) + rtext
				deg_y = self.sliceToY( 0 , (r-rtext) , t_offset + xo ) + rtext
				degree=int(t_offset)
				output += '<g transform="translate(%s,%s)">' % (deg_x,deg_y)
				output += '<text transform="rotate(%s)" text-anchor="%s' % (rotate,textanchor)
				output += '" style="fill: '+self.planets[i]['color']+'; font-size: 10px;">'+self.dec2deg(self.t_planets_degree[i],type="1")
				output += '</text></g>\n'
			
			#check transit
			if self.type == "Transit":
				dropin=36
			else:
				dropin=0			
			
			#planet line
			x1 = self.sliceToX( 0 , r-(dropin+3) , offset ) + (dropin+3)
			y1 = self.sliceToY( 0 , r-(dropin+3) , offset ) + (dropin+3)
			x2 = self.sliceToX( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			y2 = self.sliceToY( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 2px; stroke-opacity:.6;"/>\n'
			
			#check transit
			if self.type == "Transit":
				dropin=160
			else:
				dropin=120
				
			x1 = self.sliceToX( 0 , r-dropin , offset ) + dropin
			y1 = self.sliceToY( 0 , r-dropin , offset ) + dropin
			x2 = self.sliceToX( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			y2 = self.sliceToY( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 2px; stroke-opacity:.6;"/>\n'

		return output

	def makePatterns( self ):
		"""
		Find major aspect patterns for the current chart.

		Patterns detected:

		* Stellium: at least four planets linked by continuous conjunctions.
		* Grand trine: three trine aspects together.
		* Grand cross: two pairs of opposing planets squared to each other.
		* T-Square: two planets in opposition squared to a third.
		* Yod: two quincunxes joined by a sextile.
		"""
		conj = {} #0
		opp = {} #10
		sq = {} #5
		tr = {} #6
		qc = {} #9
		sext = {} #3
		for i in range(len(self.planets)):
			a=self.planets_degree_ut[i]
			qc[i]={}
			sext[i]={}
			opp[i]={}
			sq[i]={}
			tr[i]={}
			conj[i]={}
			#skip some points
			n = self.planets[i]['name']
			if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
				continue
			if n == 'Dsc' or n == 'Ic':
				continue
			for j in range(len(self.planets)):
				#skip some points
				n = self.planets[j]['name']
				if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
					continue	
				if n == 'Dsc' or n == 'Ic':
					continue
				b=self.planets_degree_ut[j]
				delta=float(self.degreeDiff(a,b))
				#check for opposition
				xa = float(self.aspects[10]['degree']) - float(self.aspects[10]['orb'])
				xb = float(self.aspects[10]['degree']) + float(self.aspects[10]['orb'])
				if( xa <= delta <= xb ):
					opp[i][j]=True	
				#check for conjunction
				xa = float(self.aspects[0]['degree']) - float(self.aspects[0]['orb'])
				xb = float(self.aspects[0]['degree']) + float(self.aspects[0]['orb'])
				if( xa <= delta <= xb ):
					conj[i][j]=True					
				#check for squares
				xa = float(self.aspects[5]['degree']) - float(self.aspects[5]['orb'])
				xb = float(self.aspects[5]['degree']) + float(self.aspects[5]['orb'])
				if( xa <= delta <= xb ):
					sq[i][j]=True			
				#check for qunicunxes
				xa = float(self.aspects[9]['degree']) - float(self.aspects[9]['orb'])
				xb = float(self.aspects[9]['degree']) + float(self.aspects[9]['orb'])
				if( xa <= delta <= xb ):
					qc[i][j]=True
				#check for sextiles
				xa = float(self.aspects[3]['degree']) - float(self.aspects[3]['orb'])
				xb = float(self.aspects[3]['degree']) + float(self.aspects[3]['orb'])
				if( xa <= delta <= xb ):
					sext[i][j]=True
							
		yot={}
		#check for double qunicunxes
		for k,v in qc.items():
			if len(qc[k]) >= 2:
				#check for sextile
				for l,w in qc[k].items():
					for m,x in qc[k].items():
						if m in sext[l]:
							if l > m:
								yot['%s,%s,%s' % (k,m,l)] = [k,m,l]
							else:
								yot['%s,%s,%s' % (k,l,m)] = [k,l,m]
		tsquare={}
		#check for opposition
		for k,v in opp.items():
			if len(opp[k]) >= 1:
				#check for square
				for l,w in opp[k].items():
						for a,b in sq.items():
							if k in sq[a] and l in sq[a]:
								#print 'got tsquare %s %s %s' % (a,k,l)
								if k > l:
									tsquare['%s,%s,%s' % (a,l,k)] = '%s => %s, %s' % (
										self.planets[a]['label'],self.planets[l]['label'],self.planets[k]['label'])
								else:
									tsquare['%s,%s,%s' % (a,k,l)] = '%s => %s, %s' % (
										self.planets[a]['label'],self.planets[k]['label'],self.planets[l]['label'])
		stellium={}
		#check for 4 continuous conjunctions	
		for k,v in conj.items():
			if len(conj[k]) >= 1:
				#first conjunction
				for l,m in conj[k].items():
					if len(conj[l]) >= 1:
						for n,o in conj[l].items():
							#skip 1st conj
							if n == k:
								continue
							if len(conj[n]) >= 1:
								#third conjunction
								for p,q in conj[n].items():
									#skip first and second conj
									if p == k or p == n:
										continue
									if len(conj[p]) >= 1:										
										#fourth conjunction
										for r,s in conj[p].items():
											#skip conj 1,2,3
											if r == k or r == n or r == p:
												continue
											
											l=[k,n,p,r]
											l.sort()
											stellium['%s %s %s %s' % (l[0],l[1],l[2],l[3])]='%s %s %s %s' % (
												self.planets[l[0]]['label'],self.planets[l[1]]['label'],
												self.planets[l[2]]['label'],self.planets[l[3]]['label'])
		#print yots
		out='<g transform="translate(-30,380)">'
		if len(yot) >= 1:
			y=0
			for k,v in yot.items():
				out += '<text y="%s" style="fill:%s; font-size: 12px;">%s</text>\n' % (y,self.colors['paper_0'],_("Yot"))
				
				#first planet symbol
				out += '<g transform="translate(20,%s)">' % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][0]]['name']))
				
				#second planet symbol
				out += '<g transform="translate(30,%s)">'  % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][1]]['name']))

				#third planet symbol
				out += '<g transform="translate(40,%s)">'  % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][2]]['name']))
				
				y=y+14
		#finalize
		out += '</g>'		
		#return out
		return ''
	
	def makeAspects( self , r , ar ):
		out=""
		for i in range(len(self.planets)):
			start=self.planets_degree_ut[i]
			for x in range(i):
				end=self.planets_degree_ut[x]
				diff=float(self.degreeDiff(start,end))
				#loop orbs
				if (self.planets[i]['visible_aspect_line'] == 1) & (self.planets[x]['visible_aspect_line'] == 1):	
					for z in range(len(self.aspects)):
						if	( float(self.aspects[z]['degree']) - float(self.aspects[z]['orb']) ) <= diff <= ( float(self.aspects[z]['degree']) + float(self.aspects[z]['orb']) ):
							#check if we want to display this aspect
							if self.aspects[z]['visible'] == 1:					
								out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])] )
		return out
	
	def makeAspectsTransit( self , r , ar ):
		out = ""
		self.atgrid=[]
		for i in range(len(self.planets)):
			start=self.planets_degree_ut[i]
			for x in range(i+1):
				end=self.t_planets_degree_ut[x]
				diff=float(self.degreeDiff(start,end))
				#loop orbs
				if (self.planets[i]['visible'] == 1) & (self.planets[x]['visible'] == 1):	
					for z in range(len(self.aspects)):
						#check for personal planets and determine orb
						if 0 <= i <= 4 or 0 <= x <= 4:
							orb_before = 1.0
						else:
							orb_before = 2.0
						#check if we want to display this aspect	
						if	( float(self.aspects[z]['degree']) - orb_before ) <= diff <= ( float(self.aspects[z]['degree']) + 1.0 ):
							if self.aspects[z]['visible'] == 1:
								out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.t_planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])] )		
							#aspect grid dictionary
							if self.aspects[z]['visible_grid'] == 1:
								self.atgrid.append({})
								self.atgrid[-1]['p1']=i
								self.atgrid[-1]['p2']=x
								self.atgrid[-1]['aid']=z
								self.atgrid[-1]['diff']=diff
		return out
	
	def makeAspectTransitGrid( self , r ):
		out = '<g transform="translate(500,310)">'
		out += '<text y="-15" x="0" style="fill:%s; font-size: 12px;">%s</text>\n' % (self.colors['paper_0'],_("Planets in Transit"))
		line = 0
		nl = 0
		for i in range(len(self.atgrid)):
			if i == 12:
				nl = 100
				if len(self.atgrid) > 24:
					line = -1 * ( len(self.atgrid) - 24) * 14
				else:
					line = 0
			out += '<g transform="translate(%s,%s)">' % (nl,line)
			#first planet symbol
			out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />\n' % (
				self.planets[self.atgrid[i]['p2']]['name'])
			#aspect symbol
			out += '<use  x="15" y="0" xlink:href="#orb%s" />\n' % (
				self.aspects[self.atgrid[i]['aid']]['degree'])
			#second planet symbol
			out += '<g transform="translate(30,0)">'
			out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />\n' % (
				self.svgSafeHref(self.planets[self.atgrid[i]['p1']]['name']))
			out += '</g>'
			#difference in degrees
			out += '<text y="8" x="45" style="fill:%s; font-size: 10px;">%s</text>' % (
				self.colors['paper_0'],
				self.dec2deg(self.atgrid[i]['diff']) )
			#line
			out += '</g>'
			line = line + 14		
		out += '</g>'
		return out
	
	def makeAspectGrid( self , r ):
		out=""
		style='stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none' % (self.colors['paper_0'])
		xindent=380
		yindent=468
		box=14
		revr=list(range(len(self.planets)))
		revr.reverse()
		for a in revr:
			if self.planets[a]['visible_aspect_grid'] == 1:
				start=self.planets_degree_ut[a]
				#first planet 
				out = out + '<rect x="'+str(xindent)+'" y="'+str(yindent)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
				out = out + '<use transform="scale(0.4)" x="'+str((xindent+2)*2.5)+'" y="'+str((yindent+1)*2.5)+'" xlink:href="#'+self.svgSafeHref(self.planets[a]['name'])+'" />\n'
				xindent = xindent + box
				yindent = yindent - box
				revr2=list(range(a))
				revr2.reverse()
				xorb=xindent
				yorb=yindent + box
				for b in revr2:
					if self.planets[b]['visible_aspect_grid'] == 1:
						end=self.planets_degree_ut[b]
						diff=self.degreeDiff(start,end)
						out = out + '<rect x="'+str(xorb)+'" y="'+str(yorb)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
						xorb=xorb+box
						for z in range(len(self.aspects)):
							if	( float(self.aspects[z]['degree']) - float(self.aspects[z]['orb']) ) <= diff <= ( float(self.aspects[z]['degree']) + float(self.aspects[z]['orb']) ) and self.aspects[z]['visible_grid'] == 1:
									out = out + '<use  x="'+str(xorb-box+1)+'" y="'+str(yorb+1)+'" xlink:href="#orb'+str(self.aspects[z]['degree'])+'" />\n'
		return out

	def makeElements( self , r ):
		total = self.fire + self.earth + self.air + self.water
		pf = int(round(100*self.fire/total))
		pe = int(round(100*self.earth/total))
		pa = int(round(100*self.air/total))
		pw = int(round(100*self.water/total))
		out = '<g transform="translate(-30,79)">\n'
		out = out + '<text y="0" style="fill:#ff6600; font-size: 10px;">'+self.label['fire']+'  '+str(pf)+'%</text>\n'
		out = out + '<text y="12" style="fill:#6a2d04; font-size: 10px;">'+self.label['earth']+' '+str(pe)+'%</text>\n'
		out = out + '<text y="24" style="fill:#6f76d1; font-size: 10px;">'+self.label['air']+'   '+str(pa)+'%</text>\n'
		out = out + '<text y="36" style="fill:#630e73; font-size: 10px;">'+self.label['water']+' '+str(pw)+'%</text>\n'		
		out = out + '</g>\n'
		return out
		
	def makePlanetGrid( self ):
		out = '<g transform="translate(510,-40)">'
		#loop over all planets
		li=10
		offset=0
		for i in range(len(self.planets)):
			if i == 27:
				li = 10
				offset = -120
			if self.planets[i]['visible'] == 1:
				#start of line				
				out = out + '<g transform="translate(%s,%s)">' % (offset,li)
				#planet text
				out = out + '<text text-anchor="end" style="fill:%s; font-size: 10px;">%s</text>' % (self.colors['paper_0'],self.planets[i]['label'])
				#planet symbol
				out = out + '<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#'+self.svgSafeHref(self.planets[i]['name'])+'" /></g>'								
				#planet degree				
				out = out + '<text text-anchor="start" x="19" style="fill:%s; font-size: 10px;">%s</text>' % (self.colors['paper_0'],self.dec2deg(self.planets_degree[i]))
				#zodiac
				out = out + '<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.planets_sign[i]]+'" /></g>'				
				#planet retrograde
				if self.planets_retrograde[i]:
					out = out + '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'				

				#end of line
				out = out + '</g>\n'
				#offset between lines
				li = li + 14	
		
		out = out + '</g>\n'
		return out

	def _refresh_vedic_snapshot(self):
		"""Build or clear Jyotish snapshot after final planet/house longitudes."""
		if g.db.astrocfg.get('tradition') != 'vedic':
			self.vedic = None
			return
		labels = {i: self.planets[i]['label'] for i in range(len(self.planets))}
		astro_cfg = effective_astrocfg(g.db.astrocfg)
		self.vedic = build_snapshot(
			self.planets_degree_ut,
			self.houses_degree_ut,
			self.planets_retrograde,
			labels,
			self.year,
			self.month,
			self.day,
			self.hour,
			dasha_system=g.db.astrocfg.get('vedic_dasha_system', 'vimshottari'),
			geolon=self.geolon,
			geolat=self.geolat,
			altitude=self.altitude,
			ayanamsa_mode=astro_cfg.get('siderealmode', 'LAHIRI'),
			varga_display=g.db.astrocfg.get('vedic_varga_display', 'D1,D9,D10'),
		)

	def _use_vedic_main_chart(self):
		"""Use North/South Indian SVG as the main window chart."""
		if self.vedic is None:
			return False
		layout = g.db.astrocfg.get('vedic_chart_layout', 'north')
		if layout == 'wheel':
			return False
		if self.type == 'Transit':
			return False
		return True

	def _write_vedic_main_svg(self, path, width, height):
		"""Write primary Vedic chart (D1) centered on the main window canvas."""
		layout = g.db.astrocfg.get('vedic_chart_layout', 'north')
		canvas_w = max(480, int(width))
		canvas_h = max(480, int(height))
		paper = self.colors.get('paper_1', '#ffffff')
		ink = self.colors.get('paper_0', '#000000')
		svg = render_vedic_chart_svg_on_canvas(
			self.vedic,
			layout,
			canvas_w,
			canvas_h,
			varga='D1',
			paper_color=paper,
			line_color=ink,
			text_color=ink,
			accent_color=self.colors.get('zodiac_bg_4', '#8b4513'),
		)
		footer = (
			'<text x="%d" y="%d" text-anchor="middle" font-size="12" fill="%s">%s — %s — %s</text>'
			% (
				canvas_w // 2,
				canvas_h - 12,
				ink,
				self.name,
				self.vedic.lagna_rashi.name,
				self.vedic.panchanga.nakshatra,
			)
		)
		if '</svg>' in svg:
			svg = svg.replace('</svg>', footer + '\n</svg>')
		with open(path, 'w', encoding='utf-8') as f:
			f.write(svg)

	def makeVedicDrishti(self, r, ar):
		"""Draw graha drishti aspect lines on the Western wheel."""
		if self.vedic is None:
			return ''
		out = ''
		color = self.colors.get('aspect_60', '#6699cc')
		seven = (0, 1, 2, 3, 4, 5, 6)
		for g in self.vedic.grahas:
			if g.index not in seven:
				continue
			start = self.planets_degree_ut[g.index]
			for other in self.vedic.grahas:
				if other.index not in seven or other.index >= g.index:
					continue
				if has_drishti(g.index, g.rashi.index, other.rashi.index):
					end = self.planets_degree_ut[other.index]
					out += self.drawAspect(r, ar, start, end, color)
		return out

	def makeVedicHousesGrid(self):
		"""Whole-sign bhavas with Sanskrit rashi names."""
		if self.vedic is None:
			return self.makeHousesGrid()
		lagna = self.vedic.lagna_sign
		out = '<g transform="translate(610,-40)">'
		li = 10
		for h in range(12):
			sign = (lagna + h) % 12
			cusp = h + 1
			out += '<g transform="translate(0,%s)">' % li
			out += '<text text-anchor="end" x="40" style="fill:%s; font-size: 10px;">%s %s:</text>' % (
				self.colors['paper_0'], self.label.get('cusp', 'H'), cusp)
			out += '<text x="45" style="fill:%s; font-size: 10px;">%s</text>' % (
				self.colors['paper_0'], RASHI_NAMES[sign])
			out += '</g>\n'
			li += 14
		out += '</g>\n'
		return out

	def makeVedicPlanetGrid(self):
		"""Planet table with nakshatra and house for Vedic tradition."""
		if self.vedic is None:
			return self.makePlanetGrid()
		out = '<g transform="translate(460,-40)">'
		li = 10
		for gr in self.vedic.grahas:
			out += '<g transform="translate(0,%s)">' % li
			out += '<text text-anchor="end" style="fill:%s; font-size: 9px;">%s</text>' % (
				self.colors['paper_0'], gr.label)
			out += '<text x="42" style="fill:%s; font-size: 9px;">%s %s° H%s</text>' % (
				self.colors['paper_0'],
				gr.rashi.name[:4],
				'%.1f' % gr.rashi.degree_in_sign,
				gr.house,
			)
			out += '<text x="115" style="fill:%s; font-size: 8px;">%s p%s</text>' % (
				self.colors['paper_0'],
				gr.nakshatra.name[:12],
				gr.nakshatra.pada,
			)
			if gr.retrograde:
				out += '<text x="200" style="fill:%s; font-size: 8px;">R</text>' % self.colors['paper_0']
			out += '</g>\n'
			li += 13
		out += '</g>\n'
		return out
	
	def makeHousesGrid( self ):
		out = '<g transform="translate(610,-40)">'
		li=10
		for i in range(12):
			if i < 9:
				cusp = '&#160;&#160;'+str(i+1)
			else:
				cusp = str(i+1)
			out += '<g transform="translate(0,'+str(li)+')">'
			out += '<text text-anchor="end" x="40" style="fill:%s; font-size: 10px;">%s %s:</text>' % (self.colors['paper_0'],self.label['cusp'],cusp)			
			out += '<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.houses_sign[i]]+'" /></g>'
			out += '<text x="53" style="fill:%s; font-size: 10px;"> %s</text>' % (self.colors['paper_0'],self.dec2deg(self.houses_degree[i]))
			out += '</g>\n'
			li = li + 14
		out += '</g>\n'
		return out
	
	"""Export/Import Functions related to astrology

	def exportOAC(filename)
	def importOAC(filename)
	def importOroboros(filename)
	
	"""
	
	def exportOAC(self,filename):
		template="""<?xml version='1.0' encoding='UTF-8'?>
<astrologychart>
	<name>$name</name>
	<datetime>$datetime</datetime>
	<location>$location</location>
	<altitude>$altitude</altitude>
	<latitude>$latitude</latitude>
	<longitude>$longitude</longitude>
	<countrycode>$countrycode</countrycode>
	<timezone>$timezone</timezone>
	<geonameid>$geonameid</geonameid>
	<timezonestr>$timezonestr</timezonestr>
	<extra>$extra</extra>
</astrologychart>"""
		h,m,s = self.decHour(g.astrology_chart.hour)
		dt=datetime.datetime(g.astrology_chart.year,g.astrology_chart.month,g.astrology_chart.day,h,m,s)
		substitute = {
			'name': xml_escape(str(self.name)),
			'datetime': dt.strftime("%Y-%m-%d %H:%M:%S"),
			'location': xml_escape(str(self.location)),
			'altitude': self.altitude,
			'latitude': self.geolat,
			'longitude': self.geolon,
			'countrycode': xml_escape(str(self.countrycode)),
			'timezone': self.timezone,
			'timezonestr': xml_escape(str(self.timezonestr)),
			'geonameid': self.geonameid if self.geonameid is not None else '',
			'extra': '',
		}
		output = Template(template).safe_substitute(substitute)
		with open(filename, 'w', encoding='utf-8') as f:
			f.write(output)
		dprint("exporting OAC: %s" % filename)
		return
	
	def importOAC(self, filename):
		r=importfile.getYAC(filename)[0]
		dt = datetime.datetime.strptime(r['datetime'],"%Y-%m-%d %H:%M:%S")
		self.name=r['name']
		self.countrycode=r['countrycode']
		self.altitude=int(r['altitude'])
		self.geolat=float(r['latitude'])
		self.geolon=float(r['longitude'])
		self.timezone=float(r['timezone'])
		self.geonameid=r['geonameid']
		if "timezonestr" in r:
			self.timezonestr=r['timezonestr']
		else:
			self.timezonestr=g.db.gnearest(self.geolat,self.geolon)['timezonestr']
		self.location=r['location']
		self.year=dt.year
		self.month=dt.month
		self.day=dt.day
		self.hour=self.decHourJoin(dt.hour,dt.minute,dt.second)
		#Make locals
		self.utcToLocal()
		#debug print
		dprint('importOAC: %s' % filename)
		return
	
	def importOroboros(self, filename):
		r=importfile.getOroboros(filename)[0]
		#naive local datetime
		naive = datetime.datetime.strptime(r['datetime'],"%Y-%m-%d %H:%M:%S")
		#aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = localize_naive(dt_input, r['zoneinfo'])
		#naive utc datetime object
		dt_utc = naive_utc(dt)
		
		#process latitude/longitude
		deg,type,min,sec = r['latitude'].split(":")
		lat = float(deg)+( float(min) / 60.0 )+( float(sec) / 3600.0 )
		if type == "S":
			lat = decimal / -1.0
		deg,type,min,sec = r['longitude'].split(":")
		lon = float(deg)+( float(min) / 60.0 )+( float(sec) / 3600.0 )
		if type == "W":
			lon = decimal / -1.0			
		
		geon = g.db.gnearest(float(lat),float(lon))
		self.timezonestr=geon['timezonestr']
		self.geonameid=geon['geonameid']		
		self.name=r['name']
		self.countrycode=''
		self.altitude=int(r['altitude'])
		self.geolat=lat
		self.geolon=lon
		self.timezone=self.offsetToTz(dt.utcoffset())
		self.location='%s, %s' % (r['location'],r['countryname'])
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		#Make locals
		self.utcToLocal()
		#debug print
		dprint('importOroboros: UTC: %s file: %s' % (dt_utc,filename))
		return
	
	def importSkylendar(self, filename):
		r = importfile.getSkylendar(filename)[0]
		
		#naive local datetime
		naive = datetime.datetime(int(r['year']),int(r['month']),int(r['day']),int(r['hour']),int(r['minute']))
		#aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = localize_naive(dt_input, r['zoneinfofile'])
		#naive utc datetime object
		dt_utc = naive_utc(dt)

		geon = g.db.gnearest(float(r['latitude']),float(r['longitude']))
		self.timezonestr=geon['timezonestr']
		self.geonameid=geon['geonameid']				
		self.name=r['name']
		self.countrycode=''
		self.altitude=25
		self.geolat=float(r['latitude'])
		self.geolon=float(r['longitude'])
		self.timezone=float(r['timezone'])
		self.location='%s, %s' % (r['location'],r['countryname'])
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		#Make locals
		self.utcToLocal()		
		return	

	def importAstrolog32(self, filename):
		r = importfile.getAstrolog32(filename)[0]

		#timezone string
		timezone_str = zonetab.nearest_tz(float(r['latitude']),float(r['longitude']),zonetab.timezones())[2]
		#naive local datetime
		naive = datetime.datetime(int(r['year']),int(r['month']),int(r['day']),int(r['hour']),int(r['minute']),int(r['second']))
		#aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = localize_naive(dt_input, timezone_str)
		#naive utc datetime object
		dt_utc = naive_utc(dt)

		geon = g.db.gnearest(float(r['latitude']),float(r['longitude']))
		self.timezonestr=geon['timezonestr']
		self.geonameid=geon['geonameid']		
		self.name=r['name']
		self.countrycode=''
		self.altitude=25
		self.geolat=float(r['latitude'])
		self.geolon=float(r['longitude'])
		self.timezone=self.offsetToTz(dt.utcoffset())
		self.location=r['location']
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		#Make locals
		self.utcToLocal()		
		return
	
	def importZet8(self, filename):
		h=open(filename)
		f=codecs.EncodedFile(h,"utf-8","latin-1")
		data=[]
		for line in f.readlines():
			s=line.split(";")
			if s[0] == line:
				continue
			
			data.append({})
			data[-1]['name']=s[0].strip()
			day=int( s[1].strip().split('.')[0] )
			month=int( s[1].strip().split('.')[1] )
			year=int( s[1].strip().split('.')[2] )
			hour=int(  s[2].strip().split(':')[0] )
			minute=int( s[2].strip().split(':')[1] )
			if len(s[3].strip()) > 3:
				data[-1]['timezone']=float( s[3].strip().split(":")[0] )
				if data[-1]['timezone'] < 0:
					data[-1]['timezone']-= float( s[3].strip().split(":")[1] ) / 60.0
				else:
					data[-1]['timezone']+= float( s[3].strip().split(":")[1] ) / 60.0
			elif len(s[3].strip()) > 0:
				data[-1]['timezone']=int(s[3].strip())
			else:
				data[-1]['timezone']=0
				
			#substract timezone from date
			dt = datetime.datetime(year,month,day,hour,minute)
			dt = dt - datetime.timedelta(seconds=float(data[-1]['timezone'])*float(3600))
			data[-1]['year'] = dt.year
			data[-1]['month'] = dt.month
			data[-1]['day'] = dt.day
			data[-1]['hour'] =  float(dt.hour) + float(dt.minute/60.0)
			data[-1]['location']=s[4].strip()

			#latitude
			p=s[5].strip()
			if p.find("°") != -1:
				#later version of zet8
				if p.find("S") == -1:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['latitude']=float(deg)+(float(min)/60.0)
				else:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['latitude']=( float(deg)+(float(min)/60.0) ) / -1.0				
			else:
				#earlier version of zet8
				if p.find("s") == -1:
					i=p.find("n")
					data[-1]['latitude']=float(p[:i])+(float(p[i+1:])/60.0)
				else:
					i=p.find("s")
					data[-1]['latitude']=( float(p[:i])+(float(p[i+1:])/60.0) ) / -1.0
			#longitude
			p=s[6].strip()
			if p.find("°") != -1:
				#later version of zet8
				if p.find("W") == -1:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['longitude']=float(deg)+(float(min)/60.0)
				else:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['longitude']=( float(deg)+(float(min)/60.0) ) / -1.0				
			else:
				#earlier version of zet8
				if p.find("w") == -1:
					i=p.find("e")
					data[-1]['longitude']=float(p[:i])+(float(p[i+1:])/60.0)
				else:
					i=p.find("w")
					data[-1]['longitude']=( float(p[:i])+(float(p[i+1:])/60.0) ) / -1.0
		
		g.db.importZet8( g.cfg.peopledb , data )
		dprint('importZet8: database with %s entries: %s' % (len(data),filename))
		f.close()
		return

	def svgSafeHref(self, name):
		name=name.replace(' ','_')
		return name
		
##############
# MAIN CLASS #
##############
