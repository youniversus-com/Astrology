# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""User session paths and packaged asset locations."""

import os

from astrology_app.constants import VERSION
from astrology_app.debug import dprint
from astrology_app.paths import DATADIR, _find_data_file

class AstrologyCfg:
	"""Filesystem paths and install layout for the current user session.

	Creates ``~/.config/<USER_CONFIG_DIR>`` (config DB, people DB, temp SVG,
	local ephemeris override) and resolves packaged UI/XML, icons, and SQL seeds.
	"""

	def __init__(self):
		from astrologymod.paths import user_data_dir, ensure_user_data_dir, migrate_legacy_user_data

		migrate_legacy_user_data()
		self.version = VERSION
		dprint("-------------------------------")
		dprint('  Astrology '+str(self.version))
		dprint("-------------------------------")
		self.homedir = os.path.expanduser("~")

		self.astrodir = user_data_dir()
		ensure_user_data_dir()

		self.tmpdir = os.path.join(self.astrodir, 'tmp')
		os.makedirs(self.tmpdir, exist_ok=True)

		self.swissLocalDir = os.path.join(self.astrodir, 'swiss_ephemeris')
		os.makedirs(self.swissLocalDir, exist_ok=True)

		#geonames database
		self.geonamesdb = _find_data_file('geonames.sql')
		
		#icons
		icons = os.path.join(DATADIR,'icons')
		self.iconWindow = os.path.join(icons, 'astrology.svg')
		self.iconAspects = os.path.join(icons, 'aspects')
		
		#basic files
		self.tempfilename = os.path.join(self.tmpdir, "AstrologyChart.svg")
		self.tempfilenameprint = os.path.join(self.tmpdir, "AstrologyChartPrint.svg")
		self.tempfilenametable = os.path.join(self.tmpdir, "AstrologyChartTable.svg")
		self.tempfilenametableprint = os.path.join(self.tmpdir, "AstrologyChartTablePrint.svg")
		self.xml_svg = os.path.join(DATADIR, 'astrology-svg.xml')
		self.xml_svg_table = os.path.join(DATADIR, 'astrology-svg-table.xml')

		#sqlite databases		
		self.astrodb = os.path.join(self.astrodir, 'astrodb.sql')
		self.peopledb = os.path.join(self.astrodir, 'peopledb.sql')
		self.famousdb = _find_data_file('famous.sql')
		return
