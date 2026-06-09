# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Vedic astrology constants: nakshatras, rashis, lords, dasha periods."""

from __future__ import annotations

# Planet indices matching Swiss Ephemeris order in ephData (0-9) + nodes
GRAHA_SUN = 0
GRAHA_MOON = 1
GRAHA_MARS = 4
GRAHA_MERCURY = 2
GRAHA_JUPITER = 5
GRAHA_VENUS = 3
GRAHA_SATURN = 6
GRAHA_RAHU = 10
GRAHA_KETU = 29

DEFAULT_GRAHA_INDICES = (0, 1, 2, 3, 4, 5, 6, 10, 29)

NAKSHATRA_SPAN = 360.0 / 27.0  # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4.0

NAKSHATRA_NAMES = (
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
    'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
    'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada',
    'Revati',
)

RASHI_NAMES = (
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
    'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
)

RASHI_NAMES_EN = (
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
)

# Sign lords: Mars, Venus, Mercury, Moon, Sun, Mercury, Venus, Mars, Jupiter, Saturn, Saturn, Jupiter
RASHI_LORDS = (4, 3, 2, 1, 0, 2, 3, 4, 5, 6, 6, 5)

NAKSHATRA_LORDS = (
    4, 3, 0, 1, 4, 3,  # Ketu..Mercury cycle start Ketu=... use planet index
)
# Vimshottari sequence by planet index: Ketu(9), Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
# Map to swe indices: Ketu not in 0-9 - use symbolic 9 for ketu in dasha only
VIMSHOTTARI_LORD_IDS = (9, 3, 0, 1, 4, 10, 5, 6, 2)  # Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
VIMSHOTTARI_YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)
VIMSHOTTARI_TOTAL = 120.0

YOGINI_LORD_IDS = (1, 3, 5, 6, 4, 2, 0, 1)  # Moon, Sun, Jupiter, Mars, Mercury, Saturn, Venus, Rahu approx
YOGINI_YEARS = (1, 2, 3, 4, 5, 6, 7, 8)
YOGINI_TOTAL = 36.0

ASHTOTTARI_LORD_IDS = (0, 1, 4, 10, 5, 6, 2, 3, 9)
ASHTOTTARI_YEARS = (6, 15, 8, 17, 19, 16, 9, 12, 18)
ASHTOTTARI_TOTAL = 108.0

LORD_LABELS = {
    0: 'Sun', 1: 'Moon', 2: 'Mercury', 3: 'Venus', 4: 'Mars',
    5: 'Jupiter', 6: 'Saturn', 9: 'Ketu', 10: 'Rahu',
}

EXALTATION_SIGN = {0: 0, 1: 1, 2: 5, 3: 11, 4: 9, 5: 3, 6: 6}
DEBILITATION_SIGN = {0: 6, 1: 7, 2: 11, 3: 5, 4: 3, 5: 9, 6: 0}

COMBUST_ORB = {0: 17, 1: 12, 2: 14, 3: 10, 4: 17, 5: 11, 6: 15}

VARGA_CODES = (
    'D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12',
    'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60',
)

VARGA_NAMES = {
    'D1': 'Rashi', 'D2': 'Hora', 'D3': 'Drekkana', 'D4': 'Chaturthamsa',
    'D7': 'Saptamsa', 'D9': 'Navamsa', 'D10': 'Dasamsa', 'D12': 'Dwadasamsa',
    'D16': 'Shodasamsa', 'D20': 'Vimsamsa', 'D24': 'Chaturvimsamsa',
    'D27': 'Bhamsa', 'D30': 'Trimsamsa', 'D40': 'Khavedamsa',
    'D45': 'Akshavedamsa', 'D60': 'Shashtiamsa',
}

TITHI_NAMES = (
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi',
    'Saptami', 'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi',
    'Trayodashi', 'Chaturdashi', 'Purnima/Amavasya',
)

YOGA_NAMES = (
    'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
    'Sukarma', 'Dhriti', 'Shula', 'Ganda', 'Vriddhi', 'Dhruva', 'Vyaghata',
    'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan', 'Parigha',
    'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra',
    'Vaidhriti',
)

KARANA_NAMES = (
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garija', 'Vanija', 'Vishti',
    'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna',
)

VARA_NAMES = (
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
)

VARA_LORDS = (0, 1, 4, 2, 5, 3, 6)
