# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Ensure ``astrology`` is importable for unit tests."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASTROLOGY_DIR = PROJECT_ROOT / 'src'

if str(ASTROLOGY_DIR) not in sys.path:
    sys.path.insert(0, str(ASTROLOGY_DIR))
