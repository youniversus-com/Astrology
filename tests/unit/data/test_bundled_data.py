# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bundled SQL and ephemeris files ship with astrology."""
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ASTROLOGY_ROOT = Path(__file__).resolve().parents[3] / 'src'


def test_geonames_sql_in_source_tree():
    path = ASTROLOGY_ROOT / 'data' / 'geonames.sql'
    assert path.is_file()
    assert path.stat().st_size > 1_000_000


def test_famous_sql_in_source_tree():
    path = ASTROLOGY_ROOT / 'data' / 'famous.sql'
    assert path.is_file()
    assert path.stat().st_size > 10_000


def test_swisseph_files_in_source_tree():
    se1 = list((ASTROLOGY_ROOT / 'swisseph').glob('*.se1'))
    assert len(se1) >= 4
