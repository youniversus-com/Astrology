# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install and per-user data directory paths.

User settings, chart databases, and optional local ephemeris overrides live
under ``~/.config/<USER_CONFIG_DIR>/`` (see :mod:`astrologymod.branding`).
"""

import os
import shutil

from astrologymod.branding import USER_CONFIG_DIR


def user_data_dir():
	"""Return the per-user config directory path.

	Returns:
		str: Absolute path ``~/.config/<USER_CONFIG_DIR>/``.
	"""
	return os.path.join(os.path.expanduser('~'), '.config', USER_CONFIG_DIR)


def ensure_user_data_dir():
    """Create the user data directory tree if missing."""
    os.makedirs(user_data_dir(), exist_ok=True)


def migrate_legacy_user_data():
    """Copy charts/settings from an older install directory if present."""
    target = user_data_dir()
    if os.path.isdir(target) and os.listdir(target):
        return
    home = os.path.expanduser('~')
    config_candidates = (
        os.path.join(home, '.config', 'youniverse', 'astrology'),
        os.path.join(home, '.config', 'YoUniverse', 'astrology'),
        os.path.join(home, '.config', 'youniverse-astrology'),
        os.path.join(home, '.openastro.org'),
        os.path.join(home, '.config', 'openastro.org'),
    )
    for legacy in config_candidates:
        if os.path.isdir(legacy) and os.path.isfile(os.path.join(legacy, 'astrodb.sql')):
            if os.path.abspath(legacy) == os.path.abspath(target):
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copytree(legacy, target, dirs_exist_ok=True)
            return
    for entry in os.listdir(home):
        if not entry.startswith('.'):
            continue
        candidate = os.path.join(home, entry)
        if not os.path.isdir(candidate):
            continue
        if not os.path.isfile(os.path.join(candidate, 'astrodb.sql')):
            continue
        if os.path.abspath(candidate) == os.path.abspath(target):
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copytree(candidate, target, dirs_exist_ok=True)
        return
