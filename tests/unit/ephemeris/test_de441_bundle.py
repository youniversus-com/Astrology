# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Swiss Ephemeris DE441 .se1 bundle is present for Astrology."""
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "scripts" / "ephemeris-de441-astrology.txt"
EPHE_DIRS = (
    ROOT / "src" / "swisseph",
    ROOT / ".venv" / "share" / "swisseph",
)


def _required_files():
    lines = MANIFEST.read_text().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def test_de441_manifest_lists_astrology_epochs():
    names = _required_files()
    assert "sepl_18.se1" in names
    assert len(names) == 6


@pytest.mark.parametrize("name", _required_files())
def test_ephemeris_file_installed(name):
    found = [d / name for d in EPHE_DIRS if (d / name).is_file()]
    assert found, (
        f"Missing {name}; run: make update-ephemeris "
        f"(or ./scripts/update_ephemeris_de441.sh)"
    )
