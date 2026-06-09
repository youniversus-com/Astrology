# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke tests: module loads and core dependencies import."""
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
ASTROLOGY_SCRIPT = ROOT / 'src' / 'astrology'


def test_astrology_module_has_version(astrology_mod):
    assert hasattr(astrology_mod, 'VERSION')
    assert astrology_mod.VERSION


def test_astrologymod_packages_import():
    from astrologymod import dignities, gtkcompat, importfile, zonetab  # noqa: F401


def test_python_syntax_check_astrology():
    r = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(ASTROLOGY_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
