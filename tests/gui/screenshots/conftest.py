# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Documentation screenshot capture (--update-screenshots)."""

from pathlib import Path

import pytest

SCREENSHOT_DIR = Path(__file__).resolve().parents[3] / 'docs' / 'screenshots'
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUNDLED_EPHE = PROJECT_ROOT / 'src' / 'swisseph'


def pytest_addoption(parser):
    parser.addoption(
        '--update-screenshots',
        action='store_true',
        default=False,
        help='Regenerate PNG files under docs/screenshots/',
    )


@pytest.fixture
def update_screenshots(request):
    return request.config.getoption('--update-screenshots', default=False)


@pytest.fixture
def screenshot_dir():
    if not any(BUNDLED_EPHE.glob('*.se1')):
        pytest.skip(
            'Missing Swiss Ephemeris files in src/swisseph; '
            'run: make update-ephemeris')
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOT_DIR
