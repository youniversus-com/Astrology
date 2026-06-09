# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Application identity for packaging, GTK, and user data paths.

These constants are the single source of truth for branding. Packaging
metadata (``setup.py``, ``debian/``, RPM spec) and the about dialog should
stay aligned with this module.

Attributes:
    APP_NAME: Human-readable application name.
    APP_ID: Freedesktop / GTK application ID (reverse-DNS).
    USER_CONFIG_DIR: Directory name under ``~/.config/`` for user data.
    GITHUB_REPO: ``owner/name`` slug for the upstream repository (customize before publish).
    PROJECT_HOMEPAGE: Canonical project URL (repository home).
    COPYRIGHT_HOLDER: SPDX / license attribution string.
"""

APP_NAME = 'YoUniverse Astrology'
APP_ID = 'com.youniverse.astrology.Desktop'
USER_CONFIG_DIR = 'com.youniverse.astrology'
GITHUB_REPO = 'YOUR_ORG/astrology'
PROJECT_HOMEPAGE = f'https://github.com/{GITHUB_REPO}'
COPYRIGHT_HOLDER = 'YoUniverse Astrology contributors'
