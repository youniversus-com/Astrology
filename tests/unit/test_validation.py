# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from astrologymod.validation import normalize_iso2, validate_hex_color, validate_label_key


def test_normalize_iso2():
    assert normalize_iso2('nl') == 'NL'
    assert normalize_iso2('NLD') is None
    assert normalize_iso2("'; DROP--") is None


def test_validate_label_key():
    assert validate_label_key('radix')
    assert not validate_label_key('bad-key')


def test_validate_hex_color():
    assert validate_hex_color('#AABBCC')
    assert not validate_hex_color('red')
