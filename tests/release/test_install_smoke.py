# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Release smoke: install layout and launcher entry points."""
import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.release

ROOT = Path(__file__).resolve().parents[2]


def test_venv_python_exists():
    venv_py = ROOT / '.venv' / 'bin' / 'python'
    if not venv_py.is_file():
        pytest.skip('Run ./install.sh before release tests')
    assert os.access(venv_py, os.X_OK)


def test_astrology_importable_in_venv():
    venv_py = ROOT / '.venv' / 'bin' / 'python'
    if not venv_py.is_file():
        pytest.skip('Run ./install.sh before release tests')
    code = (
        'import sys; sys.path.insert(0, %r); '
        'from astrology_app.constants import VERSION; '
        'assert VERSION'
    ) % (str(ROOT / 'src'),)
    r = subprocess.run([str(venv_py), '-c', code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout


def test_swisseph_in_venv():
    venv_py = ROOT / '.venv' / 'bin' / 'python'
    if not venv_py.is_file():
        pytest.skip('Run ./install.sh before release tests')
    r = subprocess.run(
        [str(venv_py), '-c', 'import swisseph; print(swisseph.version)'],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert r.stdout.strip()
