#!/usr/bin/env python
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# -*- coding: utf-8 -*-
"""Map geographic coordinates to IANA timezones using ``zone.tab``.

Reads the IANA ``zone.tab`` file (default ``/usr/share/zoneinfo/zone.tab``) and
finds the geographically nearest timezone entry. See also:

    http://www.twinsun.com/tz/tz-link.htm
    https://en.wikipedia.org/wiki/Zoneinfo
"""

import math
import re


def nearest_tz(lat, lon, zones):
    """Pick the ``zone.tab`` entry closest to ``(lat, lon)``.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        zones: Iterable of ``(country, (lat, lon), tz_name)`` from :func:`timezones`.

    Returns:
        tuple: Closest record ``(country, (lat, lon), tz_name)``.

    Examples:
        >>> nearest_tz(39.2975, -94.7139, timezones())[2]
        'America/Indiana/Vincennes'
        >>> nearest_tz(39.2975, -94.7139, timezones(exclude=["Indiana"]))[2]
        'America/Chicago'
    """
    def d(tzrec):
        return distance(lat, lon, tzrec[1][0], tzrec[1][1])
    return optimize(zones, d)

def optimize(seq, metric):
    """Return the element of ``seq`` that minimizes ``metric(element)``."""
    best = None
    m = None

    for candidate in seq:
        x = metric(candidate)
        if best is None or x < m:
            m = x
            best = candidate
    return best

def distance(lat_1, long_1, lat_2, long_2):
    """Great-circle distance between two WGS84 points in radians.

    Uses the haversine formula (ActiveState recipe 393241).
    """
    # thanks http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/393241
    # Submitter: Kevin Ryan (other recipes)
    # Last Updated: 2006/04/25 
    lat_1, long_1, lat_2, long_2 = [ v * math.pi / 180.0 for v in [lat_1, long_1, lat_2, long_2] ]
    dlong = long_2 - long_1
    dlat = lat_2 - lat_1
    a = (math.sin(dlat / 2))**2 + math.cos(lat_1) * math.cos(lat_2) \
        * (math.sin(dlong / 2))**2
    return 2 * math.asin(min(1, math.sqrt(a)))
        
def timezones(zonetab="/usr/share/zoneinfo/zone.tab", exclude=None):
    """Iterate IANA timezone entries from ``zone.tab``.

    Args:
        zonetab: Path to ``zone.tab``.
        exclude: Substrings; if any appear in a zone name, that row is skipped
            (e.g. ``["Indiana"]`` to avoid convexity exceptions).

    Yields:
        tuple: ``(country_code, (lat, lon), timezone_name)``.
    """
    if exclude is None:
        exclude = []
    with open(zonetab) as fp:
        for line in fp:
            if line.startswith("#"): continue
            values = line.split()
            if len(values) >= 3:
                country, coords, tz = values[:3]
                for s in exclude:
                    if s in tz:
                        break
                else:
                    yield country, latlong(coords), tz
    


def latlong(coords):
    """Decode ISO 6709 coordinates from ``zone.tab`` (e.g. ``-1247+04514``).

    Args:
        coords: Compact lat/lon string from ``zone.tab``.

    Returns:
        tuple[float, float]: ``(latitude, longitude)`` in decimal degrees.

    Examples:
        >>> latlong("-1247+04514")
    (-12.783333333333333, 45.233333333333334)

    >>> latlong("-690022+0393524")
    (-69.00611111111111, 39.590000000000003)
    """
    m = re.search(r'([^\d])(\d+)([^\d])(\d+)', coords)
    if not m:
        raise ValueError(coords)
    return coord(m.group(1), m.group(2)), coord(m.group(3), m.group(4))

def coord(sign, digits):
    """Convert one signed DMS field from ``zone.tab`` to decimal degrees.

    Args:
        sign: ``'+'`` or ``'-'``.
        digits: Variable-length DMS digits (4–7 chars).

    Returns:
        float: Decimal degrees (negative for ``'-'``).

    Examples:
        >>> coord("-", "1247")
    -12.783333333333333
    >>> coord("+", "04514")
    45.233333333333334
    >>> coord("-", "690022")
    -69.00611111111111
    >>> coord("+", "0393524")
    39.590000000000003
    """

    if len(digits) == 4:
        d, m, s = int(digits[:2]), int(digits[2:]), 0
    elif len(digits) == 5:
        d, m, s = int(digits[:3]), int(digits[3:]), 0
    elif len(digits) == 6:
        d, m, s = int(digits[:2]), int(digits[2:4]), int(digits[4:])
    elif len(digits) == 7:
        d, m, s = int(digits[:3]), int(digits[3:5]), int(digits[5:])
    else:
        raise RuntimeError("not implemented", digits)

    if sign == '+': kludge = 'N'
    else: kludge = 'S'

    return dms(kludge, d, m, s)

def dms(o, d, m, s):
    """Convert degrees/minutes/seconds to decimal degrees with hemisphere sign.

    Args:
        o: Hemisphere letter ``'N'``, ``'E'``, ``'S'``, or ``'W'``.
        d, m, s: Degree, minute, and second components (``s`` may be float).

    Returns:
        float: Signed decimal degrees.

    Examples:
        >>> abs(dms('N', 30, 11, 40.3) - 30.194527777777779) < 0.001
    True
    """
    return (o in ('N', 'E') and 1 or -1) * (d + \
	(m + float(s)/60)/60)
