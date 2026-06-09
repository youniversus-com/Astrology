# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""SQLite databases for settings, charts, and geonames."""

import datetime
import os
import sys

from astrologymod.timezone_utils import localize_naive, naive_utc
import sqlite3

from astrologymod import zonetab

from astrology_app.constants import VERSION
from astrology_app.debug import dprint
import astrology_app.globals as g
from astrology_app.i18n import LANGUAGES_LABEL, TRANSLATION
from astrology_app.paths import DATADIR

# Default settings_planet visibility (same as astrodb seed in dbcheck).
_WESTERN_PLANET_VISIBLE = (
	1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 0, 1, 0,
	0, 1, 0, 0, 0, 0, 0,
	0, 0, 1, 1, 0, 0, 1,
	1, 0, 0, 0, 0, 0, 0,
)
_WESTERN_PLANET_VISIBLE_ASPECT_LINE = _WESTERN_PLANET_VISIBLE
_WESTERN_PLANET_VISIBLE_ASPECT_GRID = _WESTERN_PLANET_VISIBLE


class AstrologySqlite:
	"""SQLite access for settings, labels, charts, and geonames.

	Manages ``astrodb.sql`` (configuration), ``peopledb.sql`` (natal events),
	and read-only queries against the bundled ``geonames.sql``. Honors
	``--dbcheck`` and ``--purge`` CLI flags for schema maintenance.
	"""

	def __init__(self):
		self.dbcheck=False
		self.dbpurge="IGNORE"
		
		#--dbcheck puts dbcheck to true
		if "--dbcheck" in sys.argv:
			self.dbcheck=True
			dprint("  Database Check Enabled!")
			dprint("-------------------------------")

		#--purge purges database
		if "--purge" in sys.argv:
			self.dbcheck=True
			self.dbpurge="REPLACE"
			dprint("  Database Check Enabled!")
			dprint("  Database Purge Enabled!")
			dprint("-------------------------------")
			
		self.open()
		#get table names from sqlite_master for astrodb
		sql='SELECT name FROM sqlite_master'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		self.tables={}
		for i in range(len(list)):
				self.tables[list[i][0]]=1
				
		#get table names from sqlite_master for peopledb
		sql='SELECT name FROM sqlite_master'
		self.pcursor.execute(sql)
		list=self.pcursor.fetchall()
		self.ptables={}
		for i in range(len(list)):
				self.ptables[list[i][0]]=1

		#check for event_natal table in peopledb
		self.ptable_event_natal = {
			"id":"INTEGER PRIMARY KEY",
			"name":"VARCHAR(50)",
			"year":"VARCHAR(4)",
			"month":"VARCHAR(2)",
			"day":"VARCHAR(2)",
			"hour":"VARCHAR(50)",
			"geolon":"VARCHAR(50)",
			"geolat":"VARCHAR(50)",
			"altitude":"VARCHAR(50)",
			"location":"VARCHAR(150)",
			"timezone":"VARCHAR(50)",
			"notes":"VARCHAR(500)",
			"image":"VARCHAR(250)",
			"countrycode":"VARCHAR(2)",
			"geonameid":"INTEGER",
			"timezonestr":"VARCHAR(100)",
			"extra":"VARCHAR(500)"
			}
		if 'event_natal' not in self.ptables:		
			sql='CREATE TABLE IF NOT EXISTS event_natal (id INTEGER PRIMARY KEY,name VARCHAR(50)\
				 ,year VARCHAR(4),month VARCHAR(2), day VARCHAR(2), hour VARCHAR(50), geolon VARCHAR(50)\
			 	,geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50)\
			 	,notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER\
			 	,timezonestr VARCHAR(100), extra VARCHAR(250))'
			self.pcursor.execute(sql)
			dprint('creating sqlite table event_natal in peopledb')
		
		#check for astrocfg table in astrodb
		if 'astrocfg' not in self.tables:
			#0=cfg_name, 1=cfg_value
			sql='CREATE TABLE IF NOT EXISTS astrocfg (name VARCHAR(150) UNIQUE,value VARCHAR(150))'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table astrocfg in astrodb')

		#check for astrocfg version
		sql='INSERT OR IGNORE INTO astrocfg (name,value) VALUES(?,?)'
		self.cursor.execute(sql,("version",g.cfg.version))
		#get astrocfg dict
		sql='SELECT value FROM astrocfg WHERE name="version"'
		self.cursor.execute(sql)
		self.astrocfg = {}
		self.astrocfg["version"]=self.cursor.fetchone()[0]

		#check for updated version 
		if self.astrocfg['version'] != str(g.cfg.version):
			dprint('version mismatch(%s != %s), checking table structure' % (self.astrocfg['version'],g.cfg.version))
			#insert current version and set dbcheck to true
			self.dbcheck = True
			sql='INSERT OR REPLACE INTO astrocfg VALUES("version","'+str(g.cfg.version)+'")'
			self.cursor.execute(sql)

		#default astrocfg keys (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.astrocfg')
			default = {
							"version":str(g.cfg.version),
							"use_geonames.org":"0",
							"houses_system":"P",
							"language":"default",
							"postype":"geo",
							"chartview":"traditional",
							"zodiactype":"tropical",
							"siderealmode":"FAGAN_BRADLEY",
							"tradition":"western",
							"vedic_ayanamsa":"LAHIRI",
							"vedic_houses":"whole_sign",
							"vedic_chart_layout":"north",
							"vedic_dasha_system":"vimshottari",
							"vedic_varga_display":"D1,D2,D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,D40,D45,D60",
						 }
			for k, v in default.items():
				sql='INSERT OR %s INTO astrocfg (name,value) VALUES(?,?)' % (self.dbpurge)
				self.cursor.execute(sql,(k,v))
				
		#get astrocfg dict
		sql='SELECT * FROM astrocfg'
		self.cursor.execute(sql)
		self.astrocfg = {}
		for row in self.cursor:
			self.astrocfg[row['name']]=row['value']

		_vedic_keys = {
			'tradition': 'western',
			'vedic_ayanamsa': 'LAHIRI',
			'vedic_houses': 'whole_sign',
			'vedic_chart_layout': 'north',
			'vedic_dasha_system': 'vimshottari',
			'vedic_varga_display': 'D1,D2,D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,D40,D45,D60',
		}
		vedic_cfg_added = False
		for key, val in _vedic_keys.items():
			if key not in self.astrocfg:
				sql = 'INSERT INTO astrocfg (name,value) VALUES(?,?)'
				self.cursor.execute(sql, (key, val))
				self.astrocfg[key] = val
				vedic_cfg_added = True
		if vedic_cfg_added:
			self.link.commit()

		#install language
		self.setLanguage(self.astrocfg['language'])
		self.lang_label=LANGUAGES_LABEL


		#fix inconsitencies between in people's database
		if self.dbcheck:
			sql='PRAGMA table_info(event_natal)'
			self.pcursor.execute(sql)
			list=self.pcursor.fetchall()
			vacuum = False
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			for key,val in self.ptable_event_natal.items():
				if key not in cnames:
					sql = 'ALTER TABLE event_natal ADD %s %s'%(key,val)
					dprint("dbcheck peopledb.event_natal adding %s %s"%(key,val))					
					self.pcursor.execute(sql)
					vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.pcursor.execute(sql)
				dprint('dbcheck peopledb.event_natal: updating table definitions!')

				
		#check for history table in astrodb
		if 'history' not in self.tables:
			#0=id,1=name,2=year,3=month,4=day,5=hour,6=geolon,7=geolat,8=alt,9=location,10=tz
			sql='CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY,name VARCHAR(50)\
				 ,year VARCHAR(50),month VARCHAR(50), day VARCHAR(50), hour VARCHAR(50), geolon VARCHAR(50)\
			 	,geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50)\
			 	,notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER, extra VARCHAR(250))'
			self.cursor.execute(sql)
			dprint('creating sqlite table history in astrodb')

		#fix inconsitencies between 0.6x and 0.7x in history table
		if self.dbcheck:
			sql='PRAGMA table_info(history)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			vacuum = False
			if "notes" not in cnames:
				sql = 'ALTER TABLE history ADD notes VARCHAR(500)'
				self.cursor.execute(sql)
				vacuum = True
			if "image" not in cnames:
				sql = 'ALTER TABLE history ADD image VARCHAR(250)'
				self.cursor.execute(sql)
				vacuum = True				
			if "countrycode" not in cnames:
				sql = 'ALTER TABLE history ADD countrycode VARCHAR(2)'
				self.cursor.execute(sql)
				vacuum = True
			if "geonameid" not in cnames:
				sql = 'ALTER TABLE history ADD geonameid INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "extra" not in cnames:
				sql = 'ALTER TABLE history ADD extra VARCHAR(250)'
				self.cursor.execute(sql)
				vacuum = True		
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)
				dprint('dbcheck: updating history table definitions!')
		
		#check for settings_aspect table in astrodb
		if 'settings_aspect' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS settings_aspect (degree INTEGER UNIQUE, name VARCHAR(50)\
				 ,color VARCHAR(50),visible INTEGER, visible_grid INTEGER\
				 ,is_major INTEGER, is_minor INTEGER, orb VARCHAR(5))'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table settings_aspect in astrodb')
		
		#if update, check if everything is in order
		if self.dbcheck:
			sql='PRAGMA table_info(settings_aspect)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			vacuum = False
			if "visible" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD visible INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "visible_grid" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD visible_grid INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "is_major" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD is_major INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "is_minor" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD is_minor INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "orb" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD orb VARCHAR(5)'
				self.cursor.execute(sql)
				vacuum = True				
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)
		
		#default values for settings_aspect (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.settings_aspect')		
			degree = [ 0 , 30 , 45 , 60 , 72 , 90 , 120 , 135 , 144 , 150 , 180 ]
			name = [ _('conjunction') , _('semi-sextile') , _('semi-square') , _('sextile') , _('quintile') , _('square') , _('trine') , _('sesquiquadrate') , _('biquintile') , _('quincunx') , _('opposition') ]
			color = [ '#5757e2' ,	'#810757' , 			'#b14e58' ,	 '#d59e28' , '#1f99b3' ,'#dc0000' , '#36d100' , '#985a10' , 		  '#7a9810' , 	'#fff600' ,		 '#510060' ]
			visible =      [ 1 , 0 , 0 , 1 , 1 , 1 , 1 , 0 , 1 , 1 , 1 ]
			visible_grid = [ 1 , 0 , 0 , 1 , 1 , 1 , 1 , 0 , 1 , 1 , 1 ]
			is_major =     [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 0 , 1 ]
			is_minor = 	   [ 0 , 1 , 1 , 0 , 1 , 0 , 0 , 1 , 1 , 0 , 0 ]
			orb =    		[ 10, 3 , 3 , 6 , 2 , 8 , 8 , 3 , 2 , 3 , 10]
			#insert values
			for i in range(len(degree)):	
				sql='INSERT OR %s INTO settings_aspect \
				(degree, name, color, visible, visible_grid, is_major, is_minor, orb)\
				VALUES(%s,"%s","%s",%s,%s,%s,%s,"%s")' % ( self.dbpurge,degree[i],name[i],color[i],visible[i],
				visible_grid[i],is_major[i],is_minor[i],orb[i] )
				self.cursor.execute(sql)
	
		#check for colors table in astrodb
		if 'color_codes' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS color_codes (name VARCHAR(50) UNIQUE\
				 ,code VARCHAR(50))'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table color_codes in astrodb')				

		#default values for colors (if dbcheck)
		self.defaultColors = {
			"paper_0":"#000000",
			"paper_1":"#ffffff",
			"zodiac_bg_0":"#482900",
			"zodiac_bg_1":"#6b3d00",
			"zodiac_bg_2":"#5995e7",
			"zodiac_bg_3":"#2b4972",
			"zodiac_bg_4":"#c54100",
			"zodiac_bg_5":"#2b286f",
			"zodiac_bg_6":"#69acf1",
			"zodiac_bg_7":"#ffd237",
			"zodiac_bg_8":"#ff7200",
			"zodiac_bg_9":"#863c00",
			"zodiac_bg_10":"#4f0377",
			"zodiac_bg_11":"#6cbfff",
			"zodiac_icon_0":"#482900",
			"zodiac_icon_1":"#6b3d00",
			"zodiac_icon_2":"#5995e7",
			"zodiac_icon_3":"#2b4972",
			"zodiac_icon_4":"#c54100",
			"zodiac_icon_5":"#2b286f",
			"zodiac_icon_6":"#69acf1",
			"zodiac_icon_7":"#ffd237",
			"zodiac_icon_8":"#ff7200",
			"zodiac_icon_9":"#863c00",
			"zodiac_icon_10":"#4f0377",
			"zodiac_icon_11":"#6cbfff",
			"zodiac_radix_ring_0":"#ff0000",	
			"zodiac_radix_ring_1":"#ff0000",
			"zodiac_radix_ring_2":"#ff0000",	
			"zodiac_transit_ring_0":"#ff0000",
			"zodiac_transit_ring_1":"#ff0000",	
			"zodiac_transit_ring_2":"#0000ff",	
			"zodiac_transit_ring_3":"#0000ff",
			"houses_radix_line":"#ff0000",
			"houses_transit_line":"#0000ff",
			"aspect_0":"#5757e2",
			"aspect_30":"#810757",
			"aspect_45":"#b14e58",
			"aspect_60":"#d59e28",
			"aspect_72":"#1f99b3",
			"aspect_90":"#dc0000",
			"aspect_120":"#36d100",
			"aspect_135":"#985a10",
			"aspect_144":"#7a9810",
			"aspect_150":"#fff600",
			"aspect_180":"#510060",
			"planet_0":"#984b00",
			"planet_1":"#150052",
			"planet_2":"#520800",
			"planet_3":"#400052",
			"planet_4":"#540000",
			"planet_5":"#47133d",
			"planet_6":"#124500",
			"planet_7":"#6f0766",
			"planet_8":"#06537f",
			"planet_9":"#713f04",
			"planet_10":"#4c1541",
			"planet_11":"#4c1541",
			"planet_12":"#331820",
			"planet_13":"#585858",
			"planet_14":"#000000",
			"planet_15":"#666f06",
			"planet_16":"#000000",
			"planet_17":"#000000",
			"planet_18":"#000000",
			"planet_19":"#000000",
			"planet_20":"#000000",
			"planet_21":"#000000",
			"planet_22":"#000000",
			"planet_23":"#ff7e00",
			"planet_24":"#FF0000",
			"planet_25":"#0000FF",
			"planet_26":"#000000",
			"planet_27":"#000000",
			"planet_28":"#000000",
			"planet_29":"#000000",
			"planet_30":"#000000",
			"planet_31":"#000000",
			"planet_32":"#000000",
			"planet_33":"#000000",
			"planet_34":"#000000",
			"lunar_phase_0":"#000000",
			"lunar_phase_1":"#FFFFFF",
			"lunar_phase_2":"#CCCCCC"
		}
		if self.dbcheck:
			dprint('dbcheck astrodb.color_codes')
			#insert values
			for k,v in self.defaultColors.items():	
				sql='INSERT OR %s INTO color_codes \
				(name, code)\
				VALUES("%s","%s")' % ( self.dbpurge , k, v )
				self.cursor.execute(sql)

		#check for label table in astrodb
		if 'label' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS label (name VARCHAR(150) UNIQUE\
				 ,value VARCHAR(200))'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table label in astrodb')				

		#default values for label (if dbcheck)
		self.defaultLabel = {
			"cusp":_("Cusp"),
			"longitude":_("Longitude"),
			"latitude":_("Latitude"),
			"north":_("North"),
			"east":_("East"),
			"south":_("South"),
			"west":_("West"),
			"apparent_geocentric":_("Apparent Geocentric"),
			"true_geocentric":_("True Geocentric"),
			"topocentric":_("Topocentric"),
			"heliocentric":_("Heliocentric"),
			"fire":_("Fire"),
			"earth":_("Earth (element)"),
			"air":_("Air"),
			"water":_("Water"),
			"radix":_("Radix"),
			"transit":_("Transit"),
			"synastry":_("Synastry"),
			"composite":_("Composite"),
			"combine":_("Combine"),
			"solar":_("Solar"),
			"secondary_progressions":_("Secondary Progressions")
		}
		if self.dbcheck:
			dprint('dbcheck astrodb.label')
			#insert values
			for k,v in self.defaultLabel.items():	
				sql='INSERT OR %s INTO label \
				(name, value)\
				VALUES("%s","%s")' % ( self.dbpurge , k, v )
				self.cursor.execute(sql)
		
		#check for settings_planet table in astrodb
		self.table_settings_planet={
				"id":"INTEGER UNIQUE",
				"name":"VARCHAR(50)",
				"color":"VARCHAR(50)",
				"visible":"INTEGER",
				"element_points":"INTEGER",
				"zodiac_relation":"VARCHAR(50)",
				"label":"VARCHAR(50)",
				"label_short":"VARCHAR(20)",
				"visible_aspect_line":"INTEGER",
				"visible_aspect_grid":"INTEGER"
				}
		if 'settings_planet' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS settings_planet (id INTEGER UNIQUE, name VARCHAR(50)\
				,color VARCHAR(50),visible INTEGER, element_points INTEGER, zodiac_relation VARCHAR(50)\
			 	,label VARCHAR(50), label_short VARCHAR(20), visible_aspect_line INTEGER\
			 	,visible_aspect_grid INTEGER)'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table settings_planet in astrodb')
		

		#default values for settings_planet (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.settings_planet')	
			self.value_settings_planet={}	
			self.value_settings_planet['name'] = [
			'sun','moon','mercury','venus','mars','jupiter','saturn',
			'uranus','neptune','pluto','mean node','true node','mean apogee','osc. apogee',
			'earth','chiron','pholus','ceres','pallas','juno','vesta',
			'intp. apogee','intp. perigee','Asc','Mc','Dsc','Ic','day pars',
			'night pars','south node', 'marriage pars', 'black sun', 'vulcanus', 'persephone',
			'true lilith']
			orb = [
			#sun
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#moon
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#mercury
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#venus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#mars
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#jupiter
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#saturn
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#uranus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#neptunus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#pluto
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}'
			]
			self.value_settings_planet['label'] = [
			_('Sun'),_('Moon'),_('Mercury'),_('Venus'),_('Mars'),_('Jupiter'),_('Saturn'),
			_('Uranus'),_('Neptune'),_('Pluto'),_('North Node'),'?',_('Lilith'),_('Osc. Lilith'),
			_('Earth'),_('Chiron'),_('Pholus'),_('Ceres'),_('Pallas'),_('Juno'),_('Vesta'),
			'intp. apogee','intp. perigee',_('Asc'),_('Mc'),_('Dsc'),_('Ic'),_('Day Pars'),
			_('Night Pars'),_('South Node'),_('Marriage Pars'),_('Black Sun'),_('Vulcanus'),
			_('Persephone'),_('True Lilith')]
			self.value_settings_planet['label_short'] = [
			'sun','moon','mercury','venus','mars','jupiter','saturn',
			'uranus','neptune','pluto','Node','?','Lilith','?',
			'earth','chiron','pholus','ceres','pallas','juno','vesta',
			'intp. apogee','intp. perigee','Asc','Mc','Dsc','Ic','DP',
			'NP','SNode','marriage','blacksun','vulcanus','persephone','truelilith']
			self.value_settings_planet['color'] = [
			'#984b00','#150052','#520800','#400052','#540000','#47133d','#124500',
			'#6f0766','#06537f','#713f04','#4c1541','#4c1541','#33182','#000000',
			'#000000','#666f06','#000000','#000000','#000000','#000000','#000000',
			'#000000','#000000','orange','#FF0000','#0000FF','#000000','#000000',
			'#000000','#000000','#000000','#000000','#000000','#000000','#000000']
			self.value_settings_planet['visible'] = [
			1,1,1,1,1,1,1,
			1,1,1,1,0,1,0,
			0,1,0,0,0,0,0,
			0,0,1,1,0,0,1,
			1,0,0,0,0,0,0]
			self.value_settings_planet['visible_aspect_line'] = [
			1,1,1,1,1,1,1,
			1,1,1,1,0,1,0,
			0,1,0,0,0,0,0,
			0,0,1,1,0,0,1,
			1,0,0,0,0,0,0]
			self.value_settings_planet['visible_aspect_grid'] = [
			1,1,1,1,1,1,1,
			1,1,1,1,0,1,0,
			0,1,0,0,0,0,0,
			0,0,1,1,0,0,1,
			1,0,0,0,0,0,0]
			self.value_settings_planet['element_points'] = [
			40,40,15,15,15,10,10,
			10,10,10,20,0,0,0,
			0,5,0,0,0,0,0,
			0,0,40,20,0,0,0,
			0,0,0,0,0,0,0]
			#zodiac relation gives 10 extra points in element calculation
			self.value_settings_planet['zodiac_relation'] = [
			'4','3','2,5','1,6','0','8','9',
			'10','11','7','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1']

			#if update, check if everything is in order with settings_planet
			sql='PRAGMA table_info(settings_planet)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			vacuum = False
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			for key,val in self.table_settings_planet.items():
				if key not in cnames:
					sql = 'ALTER TABLE settings_planet ADD %s %s'%(key,val)
					dprint("dbcheck astrodb.settings_planet adding %s %s"%(key,val))					
					self.cursor.execute(sql)
					#update values for col
					self.cursor.execute("SELECT id FROM settings_planet ORDER BY id DESC LIMIT 1")
					c = self.cursor.fetchone()[0]+1
					for rowid in range(c):
						sql = 'UPDATE settings_planet SET %s=? WHERE id=?' %(key)
						self.cursor.execute(sql,(self.value_settings_planet[key][rowid],rowid))
					vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)

			#insert values for planets that don't exists
			for i in range(len(self.value_settings_planet['name'])):
				sql='INSERT OR %s INTO settings_planet VALUES(?,?,?,?,?,?,?,?,?,?)'%(self.dbpurge)
				values=(i,
						self.value_settings_planet['name'][i],
						self.value_settings_planet['color'][i],
						self.value_settings_planet['visible'][i],
						self.value_settings_planet['element_points'][i],
						self.value_settings_planet['zodiac_relation'][i],
						self.value_settings_planet['label'][i],
						self.value_settings_planet['label_short'][i],
						self.value_settings_planet['visible_aspect_line'][i],
						self.value_settings_planet['visible_aspect_grid'][i]
						)
				self.cursor.execute(sql,values)

		#commit initial changes
		self.updateHistory()
		self.link.commit()
		self.plink.commit()
		self.close()

	def setLanguage(self, lang=None):
		if lang==None or lang=="default":			
			TRANSLATION["default"].install()
			dprint("installing default language")
		else:
			TRANSLATION[lang].install()
			dprint("installing language (%s)"%(lang))
		return

	def addHistory(self):
		self.open()
		sql = 'INSERT INTO history \
			(id,name,year,month,day,hour,geolon,geolat,altitude,location,timezone,countrycode) VALUES \
			(null,?,?,?,?,?,?,?,?,?,?,?)'
		tuple = (g.astrology_chart.name,g.astrology_chart.year,g.astrology_chart.month,g.astrology_chart.day,g.astrology_chart.hour,
			g.astrology_chart.geolon,g.astrology_chart.geolat,g.astrology_chart.altitude,g.astrology_chart.location,
			g.astrology_chart.timezone,g.astrology_chart.countrycode)
		self.cursor.execute(sql,tuple)
		self.link.commit()
		self.updateHistory()
		self.close()
	
	def getAstrocfg(self,key):
		self.open()
		sql='SELECT value FROM astrocfg WHERE name="%s"' % key
		self.cursor.execute(sql)
		one=self.cursor.fetchone()
		self.close()
		if one == None:
			return None
		else:
			return one[0]
	
	def setAstrocfg(self,key,val):
		sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES (?,?)'
		self.query([sql],[(key,val)])
		self.astrocfg[key]=val
		return

	def apply_vedic_planet_visibility(self) -> None:
		"""Show seven grahas + Rahu/Ketu + angles; hide outer bodies for Vedic mode."""
		from astrologymod.vedic.constants import DEFAULT_GRAHA_INDICES
		visible_ids = set(DEFAULT_GRAHA_INDICES) | {23, 24, 25, 26}
		self.open()
		self.cursor.execute('SELECT id FROM settings_planet')
		for (pid,) in self.cursor.fetchall():
			vis = 1 if pid in visible_ids else 0
			self.cursor.execute(
				'UPDATE settings_planet SET visible=?, visible_aspect_line=?, visible_aspect_grid=? WHERE id=?',
				(vis, vis, 0 if vis == 0 else 1, pid),
			)
		self.link.commit()
		self.close()

	def apply_western_planet_visibility(self) -> None:
		"""Restore default planet visibility after leaving Vedic tradition."""
		self.open()
		self.cursor.execute('SELECT id FROM settings_planet ORDER BY id')
		for (pid,) in self.cursor.fetchall():
			if pid >= len(_WESTERN_PLANET_VISIBLE):
				continue
			vis = _WESTERN_PLANET_VISIBLE[pid]
			vis_line = _WESTERN_PLANET_VISIBLE_ASPECT_LINE[pid]
			vis_grid = _WESTERN_PLANET_VISIBLE_ASPECT_GRID[pid]
			self.cursor.execute(
				'UPDATE settings_planet SET visible=?, visible_aspect_line=?, visible_aspect_grid=? WHERE id=?',
				(vis, vis_line, vis_grid, pid),
			)
		self.link.commit()
		self.close()

	def getColors(self):
		self.open()
		sql='SELECT * FROM color_codes'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		out={}
		for i in range(len(list)):
			out[list[i][0]] = list[i][1]
		self.close()
		return out

	def getLabel(self):
		"""Load UI label strings from ``astrodb`` ``label`` table."""
		self.open()
		sql='SELECT * FROM label'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		out={}
		for i in range(len(list)):
			out[list[i][0]] = list[i][1]
		self.close()
		return out	
	
	def getDatabase(self):
		self.open()

		sql = 'SELECT * FROM event_natal ORDER BY id ASC'
		self.pcursor.execute(sql)
		dict = []
		for row in self.pcursor:
			s={}			
			for key,val in self.ptable_event_natal.items():
				if row[key] == None:
					s[key]=""
				else:
					s[key]=row[key]
			dict.append(s)
		self.close()
		return dict
		

	def getDatabaseFamous(self,limit="2000",search=None):
		self.flink = sqlite3.connect(g.cfg.famousdb)
		self.flink.row_factory = sqlite3.Row
		self.fcursor = self.flink.cursor()
		
		if search:
			sql='SELECT * FROM famous WHERE year>? AND \
			(lastname LIKE ? OR firstname LIKE ? OR name LIKE ?)\
			 LIMIT %s'%(limit)
			self.fcursor.execute(sql,(1800,search,search,search))	
		else:
			sql='SELECT * FROM famous WHERE year>? LIMIT %s'%(limit)
			self.fcursor.execute(sql,(1800,))
		
		oldDB=self.fcursor.fetchall()
		
		self.fcursor.close()
		self.flink.close()

		#process database
		newDB = []
		for a in range(len(oldDB)):
			#minus years
			if oldDB[a][12] == '571/': #Muhammad
				year = 571		
			elif oldDB[a][12] <= 0:
				year = 1
			else:
				year = oldDB[a][12]
		
			month = oldDB[a][13]
			day = oldDB[a][14]
			hour = oldDB[a][15]
			h,m,s = g.astrology_chart.decHour(hour)
			
			#aware datetime object
			dt_input = datetime.datetime(year,month,day,h,m,s)
			dt = localize_naive(dt_input, oldDB[a][20])
			
			#naive utc datetime object
			dt_utc = naive_utc(dt)
			#timezone
			timezone=g.astrology_chart.offsetToTz(dt.utcoffset())
			year = dt_utc.year
			month = dt_utc.month
			day = dt_utc.day
			hour = g.astrology_chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		
			newDB.append({
						"id":oldDB[a][0], #id INTEGER
						"name":str(a+1)+". "+oldDB[a][3]+" "+oldDB[a][4], #name
						"year":year, #year
						"month":month, #month
						"day":day, #day
						"hour":hour, #hour
						"geolon":oldDB[a][18], #geolon
						"geolat":oldDB[a][17], #geolat
						"altitude":"25", #altitude
						"location":oldDB[a][16], #location
						"timezone":timezone, #timezone
						"notes":"",#notes
						"image":"",#image
						"countrycode":oldDB[a][8], #countrycode
						"geonameid":oldDB[a][19], #geonameid
						"timezonestr":oldDB[a][20], #timezonestr
						"extra":"" #extra
						}) 

		return newDB	
		
	def getSettingsPlanet(self):
		self.open()
		sql = 'SELECT * FROM settings_planet ORDER BY id ASC'
		self.cursor.execute(sql)
		dict = []
		for row in self.cursor:
			s={}			
			for key,val in self.table_settings_planet.items():
				s[key]=row[key]
			dict.append(s)
		self.close()
		return dict
		
	def getSettingsAspect(self):
		self.open()
		sql = 'SELECT * FROM settings_aspect ORDER BY degree ASC'
		self.cursor.execute(sql)
		dict = []
		for row in self.cursor:
			#degree, name, color, visible, visible_grid, is_major, is_minor, orb
			dict.append({'degree':row['degree'],'name':row['name'],'color':row['color']
			,'visible':row['visible'],'visible_grid':row['visible_grid']			
			,'is_major':row['is_major'],'is_minor':row['is_minor'],'orb':row['orb']})
		self.close()
		return dict
	
	def getSettingsLocation(self):
		#look if location is known
		if 'home_location' not in self.astrocfg or 'home_timezonestr' not in self.astrocfg:
			self.open()			
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_location","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_geolat","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_geolon","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_countrycode","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_timezonestr","")'
			self.cursor.execute(sql)			
			self.link.commit()
			self.close()
			return '','','','',''
		else:
			return self.astrocfg['home_location'],self.astrocfg['home_geolat'],self.astrocfg['home_geolon'],self.astrocfg['home_countrycode'],self.astrocfg['home_timezonestr']
		
	def setSettingsLocation(self, lat, lon, loc, cc, tzstr):
		self.open()
		for name, value in (
			('home_location', loc),
			('home_geolat', lat),
			('home_geolon', lon),
			('home_countrycode', cc),
			('home_timezonestr', tzstr),
		):
			self.cursor.execute(
				'UPDATE astrocfg SET value=? WHERE name=?',
				(str(value), name),
			)
		self.link.commit()
		self.close()
		
	def updateHistory(self):
		sql='SELECT * FROM history'
		self.cursor.execute(sql)
		self.history = self.cursor.fetchall()
		#check if limit is exceeded
		limit=10
		if len(self.history) > limit:
			cutoff_id = self.history[len(self.history) - limit][0]
			self.cursor.execute('DELETE FROM history WHERE id < ?', (cutoff_id,))
			self.link.commit()
			#update self.history
			sql = 'SELECT * FROM history'
			self.cursor.execute(sql)
			self.history = self.cursor.fetchall()
		return	
	
	"""
	
	Function to import zet8 databases

	"""	
	
	def importZet8(self, target_db, data):
	
		target_con = sqlite3.connect(target_db)
		target_con.row_factory = sqlite3.Row
		target_cur = target_con.cursor()
		
		#get target names
		target_names={}
		sql='SELECT name FROM event_natal'
		target_cur.execute(sql)
		for row in target_cur:
			target_names[row['name']]=1
		for k,v in target_names.items():		
			for i in range(1,10):
				if '%s (#%s)' % (k,i) in target_names:
					target_names[k] += 1
					
		#read input write target
		for row in data:
			
			if row['name'] in target_names:
				name_suffix = ' (#%s)' % target_names[row['name']]
				target_names[row['name']] += 1
			else:
				name_suffix = ''
			
			gname = self.gnearest( float(row['latitude']),float(row['longitude']) )	
			
			sql = 'INSERT INTO event_natal (id,name,year,month,day,hour,geolon,geolat,altitude,\
				location,timezone,notes,image,countrycode,geonameid,timezonestr,extra) VALUES \
				(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
			tuple = (row['name']+name_suffix,row['year'],row['month'],row['day'],row['hour'],row['longitude'],
				row['latitude'],25,row['location'],row['timezone'],"",
				"",gname['geonameid'],gname['timezonestr'],"")
			target_cur.execute(sql,tuple)
			
		#Finished, close connection
		target_con.commit()
		target_cur.close()
		target_con.close()
						
		return
	
	"""
	
	Function to merge two databases containing entries for persons
	databaseMerge(target_db,input_db)
	
	database format:
	'CREATE TABLE IF NOT EXISTS event_natal (id INTEGER PRIMARY KEY,name VARCHAR(50)\
				 ,year VARCHAR(4),month VARCHAR(2), day VARCHAR(2), hour VARCHAR(50), geolon VARCHAR(50)\
			 	,geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50)\
			 	,notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER\
			 	,timezonestr VARCHAR(100), extra VARCHAR(250))'
	"""	
	def _validate_peopledb_schema(self, path):
		"""Ensure ``path`` is a people DB with ``event_natal`` before merge."""
		con = sqlite3.connect(path)
		try:
			cur = con.cursor()
			cur.execute(
				"SELECT name FROM sqlite_master WHERE type='table' AND name='event_natal'")
			if cur.fetchone() is None:
				raise ValueError('missing event_natal table')
			cur.execute('PRAGMA table_info(event_natal)')
			cols = {row[1] for row in cur.fetchall()}
			required = {
				'name', 'year', 'month', 'day', 'hour', 'geolon', 'geolat',
				'altitude', 'location', 'timezone', 'notes', 'image',
				'countrycode', 'geonameid', 'timezonestr', 'extra',
			}
			if not required.issubset(cols):
				raise ValueError('event_natal schema mismatch')
		finally:
			con.close()

	def databaseMerge(self,target_db,input_db):
		dprint('g.db.databaseMerge: %s << %s'%(target_db,input_db))
		self._validate_peopledb_schema(input_db)
		target_con = sqlite3.connect(target_db)
		target_con.row_factory = sqlite3.Row
		target_cur = target_con.cursor()
		input_con = sqlite3.connect(input_db)
		input_con.row_factory = sqlite3.Row
		input_cur = input_con.cursor()
		#get target names
		target_names={}
		sql='SELECT name FROM event_natal'
		target_cur.execute(sql)
		for row in target_cur:
			target_names[row['name']]=1
		for k,v in target_names.items():		
			for i in range(1,10):
				if '%s (#%s)'% (k,i) in target_names:
					target_names[k] += 1

		#read input write target
		sql='SELECT * FROM event_natal'
		input_cur.execute(sql)
		for row in input_cur:
			if row['name'] in target_names:
				name_suffix = ' (#%s)' % target_names[row['name']]
				target_names[row['name']] += 1
			else:
				name_suffix = ''
			sql = 'INSERT INTO event_natal (id,name,year,month,day,hour,geolon,geolat,altitude,\
				location,timezone,notes,image,countrycode,geonameid,timezonestr,extra) VALUES \
				(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
			tuple = (row['name']+name_suffix,row['year'],row['month'],row['day'],row['hour'],row['geolon'],
				row['geolat'],row['altitude'],row['location'],row['timezone'],row['notes'],
				row['image'],row['countrycode'],row['geonameid'],row['timezonestr'],row['extra'])
			target_cur.execute(sql,tuple)
		
		#Finished, close connection
		target_con.commit()
		target_cur.close()
		target_con.close()
		input_cur.close()
		input_con.close()
		return
	
	"""
	
	Basic Query Functions for common databases
	
	"""
	def query(self, sql, tuple=None):
		l=sqlite3.connect(g.cfg.astrodb)
		c=l.cursor()
		for i in range(len(sql)):
			if tuple == None:
				c.execute(sql[i])
			else:
				c.execute(sql[i],tuple[i])
		l.commit()
		c.close()
		l.close()		
		
	def pquery(self, sql, tuple=None):
		l=sqlite3.connect(g.cfg.peopledb)
		c=l.cursor()
		for i in range(len(sql)):
			if tuple == None:
				c.execute(sql[i])
			else:
				c.execute(sql[i],tuple[i])
		l.commit()
		c.close()
		l.close()	
	
	def gnearest(self, lat=None, lon=None):
		#check for none
		if lat==None or lon==None:
			return {'country':None,'admin1':None,'geonameid':None,'continent':None,'timezonestr':None}
		#get closest value to lat lon
		dprint('gnearest: using %s,%s' %(lat,lon))
		diff = {}
		self.gquery(
			'SELECT id,latitude,longitude FROM geonames WHERE latitude >= ? '
			'AND latitude <= ? AND longitude >= ? AND longitude <= ?',
			(lat - 0.5, lat + 0.5, lon - 0.5, lon + 0.5),
		)
		for row in self.gcursor:
			diff[zonetab.distance( lat , lon , row['latitude'] , row['longitude'])]=row['id']
		self.gclose()
		keys=list(diff.keys())
		keys.sort()
 		
		dict={}
		if keys == []:
			dict = {'country':None,'admin1':None,'geonameid':None,'continent':None,'timezonestr':None}
			dprint('gnearest: no town found within 66km range!')
		else:
			geoname_id = diff[keys[0]]
			self.gquery('SELECT * FROM geonames WHERE id=? LIMIT 1', (geoname_id,))
			geoname = self.gcursor.fetchone()
			self.gclose()
			dict['country']=geoname['country']
			dict['admin1']=geoname['admin1']
			dict['geonameid']=geoname['geonameid']
			dict['timezonestr']=geoname['timezone']
			self.gquery(
				'SELECT * FROM countryinfo WHERE isoalpha2=? LIMIT 1',
				(geoname['country'],),
			) 			
			countryinfo = self.gcursor.fetchone()
			dict['continent']=countryinfo['continent']
			self.gclose()
			dprint('gnearest: found town %s at %s,%s,%s' % (geoname['name'],geoname['latitude'],
				geoname['longitude'],geoname['timezone']))
		return dict
	
	def gquery(self, sql, tuple=None):
		self.glink = sqlite3.connect(g.cfg.geonamesdb)
		self.glink.row_factory = sqlite3.Row
		self.gcursor = self.glink.cursor()
		if tuple:
			self.gcursor.execute(sql,tuple)
		else:
			self.gcursor.execute(sql)
	
	def gclose(self):
		self.glink.commit()
		self.gcursor.close()
		self.glink.close()
		
	def open(self):
		"""Open connections to ``astrodb`` and ``peopledb``."""
		self.link = sqlite3.connect(g.cfg.astrodb)
		self.link.row_factory = sqlite3.Row
		self.cursor = self.link.cursor()

		self.plink = sqlite3.connect(g.cfg.peopledb)
		self.plink.row_factory = sqlite3.Row
		self.pcursor = self.plink.cursor()
			
	def close(self):
		"""Close astrodb and peopledb connections."""
		self.cursor.close()
		self.pcursor.close()
		self.link.close()
		self.plink.close()

