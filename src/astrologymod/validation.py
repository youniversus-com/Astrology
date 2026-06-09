# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Input validation helpers."""

import re

_ISO2 = re.compile(r'^[A-Za-z]{2}$')
_LABEL_KEY = re.compile(r'^[a-z_][a-z0-9_]*$')
_COLOR_KEY = re.compile(r'^[a-z0-9_]+$')
_HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


def normalize_iso2(code: str) -> str | None:
    """Return upper-case ISO 3166-1 alpha-2 or None if invalid."""
    if not code:
        return None
    code = code.strip().upper()
    if _ISO2.match(code):
        return code
    return None


def validate_label_key(name: str) -> bool:
    return bool(_LABEL_KEY.match(name))


def validate_color_key(name: str) -> bool:
    return bool(_COLOR_KEY.match(name))


def validate_hex_color(code: str) -> bool:
    return bool(_HEX_COLOR.match(code.strip()))
