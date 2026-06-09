# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Importers for external astrology chart file formats.

Supported formats:

    Astrology (.yac XML)
    Oroboros (.xml)
    Skylendar (.skif)
    Astrolog / Astrolog32 (.dat)
"""

from astrologymod.xml_io import parse_xml_file

# Keys populated for Astrology native charts.
_YAC_FIELDS = [
    'name', 'datetime', 'location', 'altitude', 'latitude', 'longitude',
    'countrycode', 'timezone', 'geonameid', 'extra',
]


def _getText(nodelist):
    """Concatenate text from DOM text nodes.

    Args:
        nodelist: Child nodes of an XML element.

    Returns:
        str: Combined text.
    """
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def getYAC(filename):
    """Parse an Astrology native chart (``.yac`` XML).

    Args:
        filename: Path to ``.yac`` file.

    Returns:
        list[dict]: One dict per ``<astrologychart>`` with standard field keys.
    """
    dom = parse_xml_file(filename)

    output = []
    for a in dom.getElementsByTagName("astrologychart"):
        output.append({})
        for field in _YAC_FIELDS:
            output[-1][field] = _getText(a.getElementsByTagName(field)[0].childNodes)

    dom.unlink()
    return output


def getOroboros(filename):
    """Parse an Oroboros XML chart export.

    Args:
        filename: Path to XML file.

    Returns:
        list[dict]: Chart metadata including location attributes on LOCATION.
    """
    dom = parse_xml_file(filename)
    output = []
    for a in dom.getElementsByTagName("ASTROLOGY"):
        output.append({})
        output[-1]['name'] = _getText(a.getElementsByTagName('NAME')[0].childNodes)
        output[-1]['datetime'] = _getText(a.getElementsByTagName('DATETIME')[0].childNodes)
        output[-1]['location'] = _getText(a.getElementsByTagName('LOCATION')[0].childNodes)
        loc = a.getElementsByTagName('LOCATION')[0]
        output[-1]['altitude'] = loc.attributes['altitude'].value
        output[-1]['latitude'] = loc.attributes['latitude'].value
        output[-1]['longitude'] = loc.attributes['longitude'].value
        output[-1]['countryname'] = _getText(a.getElementsByTagName('COUNTRY')[0].childNodes)
        output[-1]['zoneinfo'] = a.getElementsByTagName('COUNTRY')[0].attributes['zoneinfo'].value
    dom.unlink()
    return output


def getSkylendar(filename):
    """Parse a Skylendar ``.skif`` chart file.

    Args:
        filename: Path to ``.skif`` XML.

    Returns:
        list[dict]: Parsed chart records (one per DATASET in file).
    """
    dom = parse_xml_file(filename)
    output = []
    for a in dom.getElementsByTagName("DATASET"):
        output.append({})
        output[-1]['name'] = _getText(a.getElementsByTagName('NAME')[0].childNodes)
        date = a.getElementsByTagName('DATE')[0]
        output[-1]['year'] = date.attributes['Year'].value
        output[-1]['month'] = date.attributes['Month'].value
        output[-1]['day'] = date.attributes['Day'].value

        tz = date.attributes['Timezone'].value.split(':')
        if float(tz[0]) < 0:
            output[-1]['timezone'] = float(tz[0]) + (float(tz[1] / 60.0) / -1)
        else:
            output[-1]['timezone'] = float(tz[0]) + float(tz[1] / 60.0)

        output[-1]['daylight'] = date.attributes['Daylight'].value
        hm = date.attributes['Hm'].value
        output[-1]['hour'] = hm.split(':')[0]
        output[-1]['minute'] = hm.split(':')[1]
        output[-1]['location'] = _getText(a.getElementsByTagName('PLACE')[0].childNodes)

        lat = a.getElementsByTagName('PLACE')[0].attributes['Latitude'].value.split(':')
        if float(lat[0]) < 0:
            output[-1]['latitude'] = float(lat[0]) + (float(lat[1] / 60.0) / -1)
        else:
            output[-1]['latitude'] = float(lat[0]) + float(lat[1] / 60.0)

        lon = a.getElementsByTagName('PLACE')[0].attributes['Longitude'].value.split(':')
        if float(lon[0]) < 0:
            output[-1]['longitude'] = float(lon[0]) + (float(lon[1] / 60.0) / -1)
        else:
            output[-1]['longitude'] = float(lon[0]) + float(lon[1] / 60.0)

        country = a.getElementsByTagName('COUNTRY')[0]
        output[-1]['zoneinfofile'] = country.attributes['ZoneInfoFile'].value
        output[-1]['countryname'] = _getText(country.childNodes)

    dom.unlink()
    return output


def getAstrolog32(filename):
    """Parse an Astrolog32 ``.dat`` chart (``/qb`` and ``/zi`` lines).

    Args:
        filename: Path to ``.dat`` file.

    Returns:
        list[dict]: Single-element list with birth data and name/location strings.
    """
    d = {}
    with open(filename, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for line in lines:
        if line[0:3] == "/qb":
            s0 = line.strip().split(' ')
            s = [x for x in s0 if x != '']
            d['month'] = s[1]
            d['day'] = s[2]
            d['year'] = s[3]
            d['hour'], d['minute'], d['second'] = 0, 0, 0
            for x in range(len(s[4].split(':'))):
                if x == 0:
                    d['hour'] = s[4].split(':')[0]
                if x == 1:
                    d['minute'] = s[4].split(':')[1]
                if x == 2:
                    d['second'] = s[4].split(':')[2]

            tz = s[6].split(':')
            d['timezone'] = float(tz[0]) + float(tz[1]) / 60.0
            if float(tz[0]) < 0:
                d['timezone'] = d['timezone'] / -1.0
            lon = s[7].split(':')
            lon.append(lon[-1][-1])
            lon[-2] = lon[-2][0:2]
            d['longitude'] = float(lon[0]) + (float(lon[1]) / 60.0)
            if len(lon) > 3:
                d['longitude'] += float(lon[2]) / 3600.0
            if lon[-1] == 'W':
                d['longitude'] = d['longitude'] / -1.0
            lon = s[8].split(':')
            lon.append(lon[-1][-1])
            lon[-2] = lon[-2][0:2]
            d['latitude'] = float(lon[0]) + (float(lon[1]) / 60.0)
            if len(lon) > 3:
                d['latitude'] += float(lon[2]) / 3600.0
            if lon[-1] == 'S':
                d['latitude'] = d['latitude'] / -1.0

        if line[0:3] == "/zi":
            s0 = line.strip().split('"')
            s = [x for x in s0 if x != '' and x != ' ']
            d['name'] = s[1]
            d['location'] = s[2]
    return [d]
