# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Golden tests share GUI fixtures; support ``--update-golden``."""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        '--update-golden',
        action='store_true',
        default=False,
        help='Regenerate golden SVG digest baselines',
    )


@pytest.fixture
def update_golden(request):
    return request.config.getoption('--update-golden', default=False)
