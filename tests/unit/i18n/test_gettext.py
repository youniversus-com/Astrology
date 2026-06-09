# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Translation / gettext smoke tests."""
import builtins

import pytest

pytestmark = pytest.mark.unit


def test_gettext_returns_non_empty(astrology_db):
    label = builtins._('Name')
    assert isinstance(label, str)
    assert len(label) > 0


def test_default_language_astrocfg(astrology_db):
    assert astrology_db.astrocfg.get('language') in (
        'default', 'en', 'de', 'fr', 'nl', '')
