#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from collections.abc import Sequence
from typing import Any, cast

from setuptools import setup
import glob
import os


def _branding_constants() -> tuple[str, str]:
	"""Read author/URL from branding.py without importing astrologymod (build isolation)."""
	branding_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'astrologymod', 'branding.py')
	ns: dict[str, str] = {}
	with open(branding_path, encoding='utf-8') as f:
		exec(compile(f.read(), branding_path, 'exec'), ns)
	return ns['COPYRIGHT_HOLDER'], ns['PROJECT_HOMEPAGE']


COPYRIGHT_HOLDER, PROJECT_HOMEPAGE = _branding_constants()

with open('VERSION') as f:
    VERSION = f.read().strip()

pre_data_files: list[tuple[str, Sequence[str]]] = []
for loc in glob.glob('locale/*'):
    if loc == 'locale/templates':
        continue
    mo = f'{loc}/LC_MESSAGES/astrology.mo'
    if os.path.isfile(mo):
        pre_data_files.append((f'share/astrology/{loc}/LC_MESSAGES', [mo]))

pre_data_files += [
    ('share/applications', ['astrology.desktop']),
    ('share/astrology', ['astrology-svg.xml', 'astrology-svg-table.xml']),
    ('share/astrology/icons', ['icons/astrology.svg']),
    ('share/astrology/icons/aspects', glob.glob('icons/aspects/*.svg')),
    ('share/astrology/data', ['data/geonames.sql', 'data/famous.sql']),
    ('share/astrology/data/vedic', glob.glob('data/vedic/*')),
    ('share/swisseph', glob.glob('swisseph/*.*')),
]

setup(
    name='astrology',
    version=VERSION,
    description='Desktop astrology application — natal charts and transits (GTK 4)',
    author=COPYRIGHT_HOLDER,
    url=PROJECT_HOMEPAGE,
    scripts=['astrology'],
    py_modules=['run_astrology'],
    packages=[
        'astrologymod', 'astrologymod.vedic',
        'astrology_app', 'astrology_app.ui',
        'astrology_api', 'astrology_api.routers', 'astrology_api.services',
    ],
    package_data=cast(
        Any,
        {
            'astrologymod': ['py.typed'],
            'astrologymod.vedic': ['py.typed'],
            'astrology_app': ['py.typed'],
        },
    ),
    data_files=pre_data_files,
)
