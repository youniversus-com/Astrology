# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Online geocoding via the geonames.org HTTP API.

API documentation: https://www.geonames.org/export/geonames-search.html

Default search uses ``featureClass=P`` (populated places) and ``maxRows=1``.
The registered username is ``astrology``.
"""

import os
from socket import timeout
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from astrologymod.xml_io import parse_xml_bytes

_GEONAMES_API = 'https://api.geonames.org'


def _geonames_username():
    """Registered geonames.org user; override via env or ``geonames_username`` astrocfg."""
    user = os.environ.get('ASTROLOGY_GEONAMES_USER', '').strip()
    if user:
        return user
    try:
        import astrology_app.globals as g
        if g.db is not None:
            cfg = g.db.getAstrocfg('geonames_username')
            if cfg:
                return str(cfg).strip()
    except Exception:
        pass
    return 'astrology'


def _getText(nodelist):
    """Concatenate text node data from a minidom nodelist.

    Args:
        nodelist: DOM child nodes.

    Returns:
        str: Combined text content.
    """
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def search(name='', country=''):
    """Search geonames.org for a populated place and resolve its timezone.

    Args:
        name: Place name query (required).
        country: Optional ISO 3166-1 alpha-2 country code filter.

    Returns:
        list[dict] | None: One-element list with keys ``name``, ``lat``, ``lng``,
        ``geonameId``, ``countryCode``, ``countryName``, ``fcl``, ``fcode``,
        ``timezonestr``; or None on error / no results.
    """
    if name == '':
        print('No name specified!')
        return None

    params = urlencode({
        'q': name,
        'country': country,
        'maxRows': 1,
        'featureClass': 'P',
        'username': _geonames_username(),
    })

    search_url = '%s/search?%s' % (_GEONAMES_API, params)
    try:
        f = urlopen(search_url, timeout=20)
    except (HTTPError, URLError) as error:
        print('Error: not retrieved because %s\nURL: %s' % (error, search_url))
        return None
    except timeout:
        print('Timeout on search!')
        return None

    data = f.read()
    dom = parse_xml_bytes(data)

    totalResultsCount = _getText(dom.getElementsByTagName("totalResultsCount")[0].childNodes)

    geoname = []
    for i in dom.getElementsByTagName("geoname"):
        geoname.append({})
        geoname[-1]['name'] = _getText(i.getElementsByTagName("name")[0].childNodes)
        geoname[-1]['lat'] = _getText(i.getElementsByTagName("lat")[0].childNodes)
        geoname[-1]['lng'] = _getText(i.getElementsByTagName("lng")[0].childNodes)
        geoname[-1]['geonameId'] = _getText(i.getElementsByTagName("geonameId")[0].childNodes)
        geoname[-1]['countryCode'] = _getText(i.getElementsByTagName("countryCode")[0].childNodes)
        geoname[-1]['countryName'] = _getText(i.getElementsByTagName("countryName")[0].childNodes)
        geoname[-1]['fcl'] = _getText(i.getElementsByTagName("fcl")[0].childNodes)
        geoname[-1]['fcode'] = _getText(i.getElementsByTagName("fcode")[0].childNodes)
        tparams = urlencode({
            'lat': geoname[-1]['lat'],
            'lng': geoname[-1]['lng'],
            'username': _geonames_username(),
        })
        tz_url = '%s/timezone?%s' % (_GEONAMES_API, tparams)
        try:
            f = urlopen(tz_url, timeout=20)
        except (HTTPError, URLError) as error:
            print('Error: not retrieved because %s\nURL: %s' % (error, tz_url))
        except timeout:
            print('Timeout on search!')
            return None

        data = f.read()
        tdom = parse_xml_bytes(data)
        geoname[-1]['timezonestr'] = _getText(tdom.getElementsByTagName("timezoneId")[0].childNodes)
        tdom.unlink()
        break
    dom.unlink()

    if totalResultsCount == "0":
        print("No results!")
        return None
    print(geoname)
    return geoname
