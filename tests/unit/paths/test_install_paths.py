# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for astrologymod.install_paths."""

import pytest

from astrologymod import install_paths

pytestmark = pytest.mark.unit


def test_find_astrology_datadir_in_source_tree():
    datadir = install_paths.find_astrology_datadir()
    assert datadir is not None
    assert (datadir / 'astrology-svg.xml').is_file()


def test_ephemeris_search_paths_includes_bundled():
    paths = install_paths.ephemeris_search_paths(
        __import__('pathlib').Path('/tmp/astrology-test-swiss'),
    )
    assert paths
    assert any('swisseph' in part for part in paths.split(':'))
