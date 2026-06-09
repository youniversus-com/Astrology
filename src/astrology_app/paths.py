# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install layout paths and bundled asset locations."""

import sys
from pathlib import Path

from astrologymod import install_paths

APP_DIR = str(install_paths._package_root())

_datadir = install_paths.find_astrology_datadir()
if _datadir is None:
    print("Exiting... can't find data directory")
    sys.exit(1)

DATADIR = str(_datadir)


def _find_data_file(filename):
    """Resolve bundled data files (SQL dumps, etc.)."""
    return str(install_paths.find_data_file(filename, _datadir))
