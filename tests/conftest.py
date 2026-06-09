# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared fixtures and loaders for all Astrology tests."""
import os
import sys
from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

PROJECT_ROOT = TESTS_ROOT.parent
ASTROLOGY_DIR = PROJECT_ROOT / 'src'

from helpers.loader import load_astrology_module, sync_runtime_globals  # noqa: E402


def ensure_bundled_ephemeris():
    """Point pysweph at bundled ``src/swisseph`` (EPHE_PATH is fixed at import time)."""
    from helpers.ephemeris import ensure_bundled_ephemeris as _ensure

    _ensure()


@pytest.fixture
def test_home(tmp_path):
    """Isolated user config directory for each test."""
    home = tmp_path / 'home'
    home.mkdir()
    from astrologymod.branding import USER_CONFIG_DIR

    cfg_dir = home / '.config' / USER_CONFIG_DIR
    cfg_dir.mkdir(parents=True)
    (cfg_dir / 'swiss_ephemeris').mkdir()
    (cfg_dir / 'tmp').mkdir()
    old_home = os.environ.get('HOME')
    os.environ['HOME'] = str(home)
    yield home
    if old_home is not None:
        os.environ['HOME'] = old_home
    elif 'HOME' in os.environ:
        del os.environ['HOME']


@pytest.fixture
def astrology_mod(test_home):
    """Loaded astrology module with isolated HOME (no GTK window)."""
    return load_astrology_module()


@pytest.fixture
def astrology_db(astrology_mod, test_home):
    """``AstrologySqlite`` against an isolated config directory."""
    astrology_mod.cfg = astrology_mod.AstrologyCfg()
    sync_runtime_globals(astrology_mod)
    db = astrology_mod.AstrologySqlite()
    sync_runtime_globals(astrology_mod)
    return db
