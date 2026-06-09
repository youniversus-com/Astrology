# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test helpers for Swiss Ephemeris file paths."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_EPHE_DIR = PROJECT_ROOT / 'src' / 'swisseph'


def ensure_bundled_ephemeris():
    """Point pysweph at bundled ``src/swisseph``.

    Uses a single directory path: colon-separated search paths longer than ~241
    characters are ignored by pysweph (``set_ephe_path`` silently falls back).
    """
    if not any(BUNDLED_EPHE_DIR.glob('*.se1')):
        return

    path = str(BUNDLED_EPHE_DIR.resolve())

    import swisseph as swe

    swe.set_ephe_path(path)

    import astrologymod.swiss as swiss_mod

    swiss_mod.EPHE_PATH = path
