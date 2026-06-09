#!/usr/bin/env python
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# -*- coding: utf-8 -*-
"""Traditional essential dignities and debilities for a longitude.

Uses Swiss Ephemeris planet constants (``swisseph.SUN``, etc.) for rulers.
"""

import os
import os.path
import sys

from astrologymod.paths import user_data_dir

# Ephemeris search path: system install, then user override
swissDir = '/usr/share/swisseph:/usr/local/share/swisseph'
swissLocalDir = os.path.join(user_data_dir(), 'swiss_ephemeris')
ephe_path = swissDir + ':' + swissLocalDir

import swisseph as swe

__all__ = ["getdignities"]


def getdignities(lon, isday, terms):
    """Compute essential dignities for an ecliptic longitude.

    Args:
        lon: Ecliptic longitude in degrees (0–360).
        isday: True for a diurnal chart (affects triplicity ruler order).
        terms: ``'termse'`` for Egyptian terms, otherwise Ptolemy terms.

    Returns:
        tuple: Nine Swiss Ephemeris planet ids — ruler, exaltation,
        triplicity rulers (3), terms, decan, detriment, fall. ``-1`` where
        no exaltation/fall applies for that sign.
    """

    temp = 0
    pos = list()
    rul = list()

    # egyptian terms
    eterms = (
        ((0,5,swe.JUPITER), (6,11,swe.VENUS), (12, 19, swe.MERCURY),
            (20,24,swe.MARS), (25,29,swe.SATURN)),
        ((0,7,swe.VENUS), (8,13,swe.MERCURY), (14,21,swe.JUPITER),
            (22,26,swe.SATURN), (27,29,swe.MARS)),
        ((0,5,swe.MERCURY), (6,11,swe.JUPITER), (12,16,swe.VENUS),
            (17,23,swe.MARS), (24,29,swe.SATURN)),
        ((0,6,swe.MARS), (7,12,swe.VENUS), (13,18,swe.MERCURY),
            (19,25,swe.JUPITER), (26,29,swe.SATURN)),
        ((0,5,swe.JUPITER), (6,10,swe.VENUS), (11,17,swe.SATURN),
            (18,23,swe.MERCURY), (24,29,swe.MARS)),
        ((0,6,swe.MERCURY), (7,16,swe.VENUS), (17,20,swe.JUPITER),
            (21,27,swe.MARS), (28,29,swe.SATURN)),
        ((0,5,swe.SATURN), (6,13,swe.MERCURY), (14,20,swe.JUPITER),
            (21,27,swe.VENUS), (28,29,swe.MARS)),
        ((0,6,swe.MARS), (7,10,swe.VENUS), (11,18,swe.MERCURY),
            (19,23,swe.JUPITER), (24,29,swe.SATURN)),
        ((0,11,swe.JUPITER), (12,16,swe.VENUS), (17,20,swe.MERCURY),
            (21,25,swe.SATURN), (26,29,swe.MARS)),
        ((0,6,swe.MERCURY), (7,13,swe.JUPITER), (14,21,swe.VENUS),
            (22,25,swe.SATURN), (26,29,swe.MARS)),
        ((0,6,swe.MERCURY), (7,12,swe.VENUS), (13,19,swe.JUPITER),
            (20,24,swe.MARS), (25,29,swe.SATURN)),
        ((0,11,swe.VENUS), (12,15,swe.JUPITER), (16,18,swe.MERCURY),
            (19,27,swe.MARS), (28,29,swe.SATURN)) )

    # ptolemy terms
    pterms = (
        ((0,5,swe.JUPITER), (6,13, swe.VENUS), (14,20,swe.MERCURY),
            (21,25,swe.MARS), (26,29,swe.SATURN)),
        ((0,7,swe.VENUS), (8,14,swe.MERCURY), (15,21,swe.JUPITER),
            (22,23,swe.SATURN), (24,29,swe.MARS)),
        ((0,6,swe.MERCURY), (7,12,swe.JUPITER), (13,19,swe.VENUS),
            (20,25,swe.MARS), (26,29,swe.SATURN)),
        ((0,5,swe.MARS), (6,12,swe.JUPITER), (13,19,swe.MERCURY),
            (20,26,swe.VENUS), (27,29,swe.SATURN)),
        ((0,5,swe.JUPITER), (6,12,swe.MERCURY), (13,18,swe.SATURN),
            (19,24,swe.VENUS), (25,29,swe.MARS)),
        ((0,6,swe.MERCURY), (6,12,swe.VENUS), (13,17,swe.JUPITER),
            (18,23,swe.SATURN), (24,29,swe.MARS)),
        ((0,5,swe.SATURN), (6,10,swe.VENUS), (11,15,swe.MERCURY),
            (16,23,swe.JUPITER), (24,29,swe.MARS)),
        ((0,5,swe.MARS), (6,12,swe.VENUS), (13,20,swe.JUPITER),
            (21,26,swe.MERCURY), (27,29,swe.SATURN)),
        ((0,7,swe.JUPITER), (8,13,swe.VENUS), (14,18,swe.MERCURY),
            (19,24,swe.SATURN), (25,29,swe.MARS)),
        ((0,5,swe.VENUS), (6,11,swe.MERCURY), (12,18,swe.JUPITER),
            (19,24,swe.SATURN), (25,29,swe.MARS)),
        ((0,5,swe.SATURN), (6,11,swe.MERCURY), (12,19,swe.VENUS),
            (20,24,swe.JUPITER), (25,29,swe.MARS)),
        ((0,7,swe.VENUS), (8,13,swe.JUPITER), (14,19,swe.MERCURY),
            (20,24,swe.MARS), (25,29,swe.SATURN)) )


    ### convert longitude to sign, degree, minute, second
    # sign
    pos.append(int(lon / 30))
    # degree
    pos.append(int(lon - (pos[0] * 30)))
    # minute
    pos.append(int((lon - ((pos[0] * 30) + pos[1])) * 60))
    # second
    pos.append(
        int((lon - ((pos[0] * 30) + pos[1] + (pos[2]/60.0))) * 3600))

    ### get ruler
    rul.append([swe.MARS, swe.VENUS, swe.MERCURY,
        swe.MOON, swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS,
        swe.JUPITER, swe.SATURN, swe.SATURN, swe.JUPITER][pos[0]])

    ### get exaltation
    rul.append([swe.SUN, swe.MOON, -1, swe.JUPITER, -1, swe.MERCURY,
    swe.SATURN, -1, -1, swe.MARS, -1, swe.VENUS][pos[0]])

    ### get triplicity rulers
    temp = list()
    # get day
    temp.append([swe.SUN, swe.VENUS, swe.SATURN, swe.VENUS,
        swe.SUN, swe.VENUS, swe.SATURN, swe.VENUS, swe.SUN,
        swe.VENUS, swe.SATURN, swe.VENUS][pos[0]])
    # get night
    temp.append([swe.JUPITER, swe.MOON, swe.MERCURY, swe.MARS,
        swe.JUPITER, swe.MOON, swe.MERCURY, swe.MARS, swe.JUPITER,
        swe.MOON, swe.MERCURY, swe.MARS][pos[0]])
    # get participating
    temp.append([swe.SATURN, swe.MARS, swe.JUPITER, swe.MOON,
        swe.SATURN, swe.MARS, swe.JUPITER, swe.MOON, swe.SATURN,
        swe.MARS, swe.JUPITER, swe.MOON][pos[0]])
    # add triplicities
    if isday:
        rul.append(temp[0])
        rul.append(temp[1])
    else:
        rul.append(temp[1])
        rul.append(temp[0])
    rul.append(temp[2])

    ### get terms... defaults to ptolemy if eterms not specified
    if terms == "termse":
        for i in eterms[pos[0]]:
            if i[0] <= pos[1] <= i[1]:
                rul.append(i[2])
                break
    else:
        for i in pterms[pos[0]]:
            if i[0] <= pos[1] <= i[1]:
                rul.append(i[2])
                break

    ### get decan
    rul.append([(swe.MARS, swe.SUN, swe.VENUS),
        (swe.MERCURY, swe.MOON, swe.SATURN),
        (swe.JUPITER, swe.MARS, swe.SUN),
        (swe.VENUS, swe.MERCURY, swe.MOON),
        (swe.SATURN, swe.JUPITER, swe.MARS),
        (swe.SUN, swe.VENUS, swe.MERCURY),
        (swe.MOON, swe.SATURN, swe.JUPITER),
        (swe.MARS, swe.SUN, swe.VENUS),
        (swe.MERCURY, swe.MOON, swe.SATURN),
        (swe.JUPITER, swe.MARS, swe.SUN),
        (swe.VENUS, swe.MERCURY, swe.MOON),
        (swe.SATURN, swe.JUPITER, swe.MARS)][pos[0]][int(pos[1] / 10)])

    ### get detriment
    rul.append([swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN,
        swe.SATURN, swe.JUPITER, swe.MARS, swe.VENUS, swe.MERCURY,
        swe.MOON, swe.SUN, swe.MERCURY][pos[0]])

    ### get fall
    rul.append([swe.SATURN, -1, -1, swe.MARS, -1, swe.VENUS,
        swe.SUN, swe.MOON, -1, swe.JUPITER, -1, swe.MERCURY][pos[0]])

    # return a tuple of dignities
    return tuple(rul)