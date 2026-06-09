# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Debug logging redaction."""

import pytest

from astrology_app.debug import _redact_sensitive

pytestmark = pytest.mark.unit


def test_redacts_home_paths():
    text = 'Exported chart to /home/alice/charts/natal.svg'
    assert '/home/alice' not in _redact_sensitive(text)
    assert '<user-data>' in _redact_sensitive(text)


def test_redacts_geonames_lookup_message():
    text = 'gnearest: found town Amsterdam at 52.120710,6.219530,Europe/Amsterdam'
    redacted = _redact_sensitive(text)
    assert 'Amsterdam' not in redacted
    assert '52.120710' not in redacted
    assert '6.219530' not in redacted
    assert 'Europe/Amsterdam' not in redacted
    assert '<place>' in redacted
    assert '<coords>' in redacted
    assert '<timezone>' in redacted


def test_redacts_home_location_message():
    text = 'known home location: Amsterdam 52.120710 6.219530'
    redacted = _redact_sensitive(text)
    assert 'Amsterdam' not in redacted
    assert '52.120710' not in redacted
    assert '6.219530' not in redacted


def test_preserves_low_precision_astronomical_degrees():
    text = 'localToSolar: first sun 285.123456'
    assert _redact_sensitive(text) == text
