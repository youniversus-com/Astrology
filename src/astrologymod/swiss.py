# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Swiss Ephemeris wrapper for chart positions, houses, and derived points.

Computes planet longitudes, house cusps, Arabic parts, lunar phase, and
extended points (Asc/MC, nodes, Lilith variants) via ``pysweph``.
"""

from __future__ import annotations

import datetime
import math
import os
import sys
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

import swisseph as swe

from astrologymod import install_paths
from astrologymod.paths import user_data_dir

EPHE_PATH = install_paths.ephemeris_search_paths(
	Path(user_data_dir()) / 'swiss_ephemeris',
)

POLAR_LAT_LIMIT = 66.0
SWE_BODY_COUNT = 23
DERIVED_POINT_START = 23
DERIVED_POINT_END = 35
TRUE_LILITH_Q = 12.333

MOON_PHASE_STEPS = 28
SUN_PHASE_BOUNDS = (
	0, 30, 40, 50, 60, 70, 80, 90, 120, 130, 140, 150, 160, 170, 180,
	210, 220, 230, 240, 250, 260, 270, 300, 310, 320, 330, 340, 350,
)


def _normalize_house_cusps(cusps: Sequence[float]) -> list[float]:
	"""Return twelve ecliptic house cusps from a ``swe.houses`` cusp sequence."""
	if len(cusps) == 13:
		return list(cusps[1:13])
	return list(cusps)


def _calc_positions(result: tuple[Any, ...] | list[Any]) -> tuple[float, ...]:
	"""Extract longitude and speed tuple from ``calc_ut`` return value."""
	if isinstance(result[0], (tuple, list)):
		return tuple(result[0])
	return tuple(result[:6])


def sign_index(lon: float, sign_count: int = 12) -> int:
	"""Map ecliptic longitude to a zodiac sign index (0-based)."""
	for x in range(sign_count):
		deg_low = float(x * 30)
		deg_high = float((x + 1) * 30)
		if lon >= deg_low:
			if lon < deg_high or (x == sign_count - 1 and lon <= deg_high):
				return x
	return sign_count - 1


def degree_in_sign(lon: float) -> float:
	"""Return longitude within the current sign (0–30°)."""
	return lon - float(sign_index(lon) * 30)


def _normalize_longitude(lon: float) -> float:
	"""Wrap ecliptic longitude into [0, 360)."""
	while lon < 0.0:
		lon += 360.0
	while lon > 360.0:
		lon -= 360.0
	return lon


def _build_iflag(astrologycfg: Mapping[str, str]) -> int:
	"""Build Swiss Ephemeris calculation flags from app settings."""
	iflag = swe.FLG_SWIEPH + swe.FLG_SPEED
	postype = astrologycfg['postype']
	if postype == 'truegeo':
		iflag += swe.FLG_TRUEPOS
	elif postype == 'topo':
		iflag += swe.FLG_TOPOCTR
	elif postype == 'helio':
		iflag += swe.FLG_HELCTR

	if astrologycfg['zodiactype'] == 'sidereal':
		iflag += swe.FLG_SIDEREAL
		mode = 'SIDM_' + astrologycfg['siderealmode']
		swe.set_sid_mode(getattr(swe, mode))
	return iflag


def _clamp_polar_latitude(geolat: float) -> float:
	"""Limit house latitude to Swiss Ephemeris polar-circle support."""
	if geolat > POLAR_LAT_LIMIT:
		print('polar circle override for houses, using 66 degrees')
		return POLAR_LAT_LIMIT
	if geolat < -POLAR_LAT_LIMIT:
		print('polar circle override for houses, using -66 degrees')
		return -POLAR_LAT_LIMIT
	return geolat


def _assign_body_longitude(
	index: int,
	lon: float,
	planets_sign: list[int],
	planets_degree: list[float],
	planets_degree_ut: list[float],
	planets_retrograde: list[bool],
	*,
	retrograde: bool | None = None,
) -> None:
	planets_sign[index] = sign_index(lon)
	planets_degree_ut[index] = lon
	planets_degree[index] = degree_in_sign(lon)
	if retrograde is not None:
		planets_retrograde[index] = retrograde


def _compute_houses(
	jul_day_ut: float,
	geolat: float,
	geolon: float,
	astrologycfg: Mapping[str, str],
) -> list[float]:
	house_lat = _clamp_polar_latitude(geolat)
	house_system = astrologycfg['houses_system'].encode('ascii')
	if astrologycfg['zodiactype'] == 'sidereal':
		sh = swe.houses_ex(
			jul_day_ut, house_lat, geolon, house_system, swe.FLG_SIDEREAL,
		)
	else:
		sh = swe.houses(jul_day_ut, house_lat, geolon, house_system)
	return [_normalize_longitude(lon) for lon in _normalize_house_cusps(sh[0])]


def _true_lilith_offset(sun: float, mean_lilith: float) -> float:
	"""Osculating Lilith correction used by the legacy chart engine."""
	deg = sun - mean_lilith
	if deg < 0.0:
		deg += 360.0
	if deg > 180.0:
		deg -= 180.0

	if deg < 60.0:
		return TRUE_LILITH_Q * math.sin(1.5 * math.radians(deg))
	if deg > 120.0:
		return TRUE_LILITH_Q * math.cos(1.5 * math.radians(deg))
	return -TRUE_LILITH_Q * math.cos(3.0 * math.radians(deg))


def _compute_lunar_phase(sun: float, moon: float) -> dict[str, float | int]:
	"""Return sun/moon separation and legacy phase indices."""
	degrees = moon - sun
	if degrees < 0.0:
		degrees += 360.0

	step = 360.0 / MOON_PHASE_STEPS
	moon_phase = 1
	for x in range(MOON_PHASE_STEPS):
		low = x * step
		high = (x + 1) * step
		if low <= degrees < high:
			moon_phase = x + 1
			break

	sun_phase = 1
	for x, low in enumerate(SUN_PHASE_BOUNDS):
		high = 360.0 if x == len(SUN_PHASE_BOUNDS) - 1 else SUN_PHASE_BOUNDS[x + 1]
		if low <= degrees < high:
			sun_phase = x + 1
			break

	return {
		'degrees': degrees,
		'moon_phase': moon_phase,
		'sun_phase': sun_phase,
	}


class ephData:
	"""Ephemeris snapshot for one moment and geographic location.

	Populates planet and house longitudes (tropical or sidereal), retrograde
	flags, sign indices, Arabic parts, and lunar phase metadata. Closes the
	Swiss Ephemeris library when construction finishes.
	"""

	def __init__(
		self,
		year: int,
		month: int,
		day: int,
		hour: float,
		geolon: float,
		geolat: float,
		altitude: float,
		planets: Sequence[Any],
		zodiac: Sequence[str],
		astrologycfg: Mapping[str, str],
		houses_override: Sequence[int | float] | None = None,
	) -> None:
		swe.set_ephe_path(EPHE_PATH)

		self.jul_day_UT = swe.julday(year, month, day, hour)
		self.geo_loc = swe.set_topo(geolon, geolat, altitude)

		body_count = len(planets)
		self.planets_sign = list(range(body_count))
		self.planets_degree = list(range(body_count))
		self.planets_degree_ut = list(range(body_count))
		self.planets_info_string = list(range(body_count))
		self.planets_retrograde = list(range(body_count))

		iflag = _build_iflag(astrologycfg)

		for i in range(SWE_BODY_COUNT):
			pos = _calc_positions(swe.calc_ut(self.jul_day_UT, i, iflag))
			_assign_body_longitude(
				i,
				pos[0],
				self.planets_sign,
				self.planets_degree,
				self.planets_degree_ut,
				self.planets_retrograde,
				retrograde=pos[3] < 0,
			)

		if houses_override:
			self.jul_day_UT = swe.julday(
				int(houses_override[0]),
				int(houses_override[1]),
				int(houses_override[2]),
				float(houses_override[3]),
			)

		self.houses_degree_ut = _compute_houses(
			self.jul_day_UT, geolat, geolon, astrologycfg,
		)

		sun = self.planets_degree_ut[0]
		moon = self.planets_degree_ut[1]
		asc = self.houses_degree_ut[0]
		dsc = self.houses_degree_ut[6]
		venus = self.planets_degree_ut[3]
		mean_lilith = self.planets_degree_ut[12]

		self.houses_degree = [0.0] * 12
		self.houses_sign = [0] * 12
		for i, cusp in enumerate(self.houses_degree_ut):
			self.houses_sign[i] = sign_index(cusp)
			self.houses_degree[i] = degree_in_sign(cusp)

		true_lilith = _true_lilith_offset(sun, mean_lilith)

		self.planets_degree_ut[23] = asc
		self.planets_degree_ut[24] = self.houses_degree_ut[9]
		self.planets_degree_ut[25] = dsc
		self.planets_degree_ut[26] = self.houses_degree_ut[3]
		self.planets_degree_ut[27] = asc + (moon - sun)
		self.planets_degree_ut[28] = asc + (sun - moon)
		self.planets_degree_ut[29] = self.planets_degree_ut[10] - 180.0
		self.planets_degree_ut[30] = (asc + dsc) - venus
		self.planets_degree_ut[31] = swe.nod_aps_ut(
			self.jul_day_UT, 0, swe.NODBIT_MEAN, swe.FLG_SWIEPH,
		)[3][0]
		self.planets_degree_ut[32] = 31.1 + (self.jul_day_UT - 2425246.5) * 0.00150579
		self.planets_degree_ut[33] = 240.0 + (self.jul_day_UT - 2425246.5) * 0.002737829
		self.planets_degree_ut[34] = self.planets_degree_ut[12] + true_lilith

		for i in range(DERIVED_POINT_START, DERIVED_POINT_END):
			self.planets_degree_ut[i] = _normalize_longitude(self.planets_degree_ut[i])
			_assign_body_longitude(
				i,
				self.planets_degree_ut[i],
				self.planets_sign,
				self.planets_degree,
				self.planets_degree_ut,
				self.planets_retrograde,
				retrograde=False,
			)

		self.lunar_phase = _compute_lunar_phase(sun, moon)
		swe.close()


def years_diff(
	y1: int, m1: int, d1: int, h1: float,
	y2: int, m2: int, d2: int, h2: float,
) -> datetime.datetime:
	"""Advance the first date by the tropical years elapsed to the second."""
	swe.set_ephe_path(EPHE_PATH)
	jd1 = swe.julday(y1, m1, d1, h1)
	jd2 = swe.julday(y2, m2, d2, h2)
	jd = jd1 + swe._years_diff(jd1, jd2)
	y, mth, day, hour, minute, second = swe._revjul(jd, swe.GREG_CAL)
	return datetime.datetime(y, mth, day, hour, minute, second)
