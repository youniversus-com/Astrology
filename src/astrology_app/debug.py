# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Debug logging helper."""

import re
import sys
from typing import Any

from astrology_app.constants import DEBUG

# Home-directory paths in debug strings.
_HOME_PATH = re.compile(r'(?:/home/[^/\s"\']+|~(?:/[^\s"\']*)?)')
# Non-home absolute paths that may identify the user.
_ABS_PATH = re.compile(r'(?:/(?:tmp|var|run|mnt|opt|usr|Users|private)[^\s"\']*)')
# IANA timezone names (Europe/Amsterdam, America/New_York).
_TIMEZONE = re.compile(r'\b[A-Z][a-z]+(?:/[A-Za-z_+-]+)+\b')
# Birth/event timestamps emitted by strftime and similar.
_DATETIME = re.compile(
    r'\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\s+[A-Z%+-][\w+-]*)?)?'
)
# Explicit lat/lon labels in debug strings.
_GEO_LABEL = re.compile(
    r'\b((?:lat|lon|latitude|longitude)[=:\s]+)-?\d+(?:\.\d+)?',
    re.IGNORECASE,
)
# Coordinate tuples such as 52.120710,6.219530 (at least two values).
_COORD_RUN = re.compile(
    r'(?<![\w./])-?\d{1,3}\.\d+(?:\s*,\s*-?\d{1,3}\.\d+)+(?![\w.])'
)
# High-precision geo-like decimals (4+ fractional digits, within lon range).
_GEO_DECIMAL = re.compile(r'(?<![\w./])-?\d{1,3}\.\d+(?![\w.])')
# Place or person names after common debug prefixes.
_PLACE_PATTERNS = (
    (re.compile(r'\btown\s+([^,\n]+?)(?=\sat\b)', re.IGNORECASE), r'town <place>'),
    (re.compile(r'\bknown home location:\s+([^,\n]+)(?=\s)', re.IGNORECASE), r'known home location: <place>'),
    (re.compile(r'\bloc=([^,\n]+)(?=(?:\s|$|,))', re.IGNORECASE), r'loc=<place>'),
    (re.compile(r'\bdatabase entry:\s+([^,\n]+)(?=(?:\s|$|,))', re.IGNORECASE), r'database entry: <place>'),
    (re.compile(r'\bsaved to database:\s+([^,\n]+)(?=(?:\s|$|,))', re.IGNORECASE), r'saved to database: <place>'),
    (re.compile(r'\bsaved edit to database:\s+([^,\n]+)(?=(?:\s|$|,))', re.IGNORECASE), r'saved edit to database: <place>'),
)


def _debug_enabled() -> bool:
    return '--debug' in sys.argv or DEBUG


def _redact_geo_decimal(match: re.Match[str]) -> str:
    value = match.group(0)
    try:
        number = float(value)
    except ValueError:
        return value
    if abs(number) > 180.0:
        return value
    fraction = value.split('.', 1)
    if len(fraction) == 2 and len(fraction[1]) >= 4:
        return '<coord>'
    return value


def _redact_sensitive(text: str) -> str:
    """Remove user-identifying data from debug strings."""
    text = _HOME_PATH.sub('<user-data>', text)
    text = _ABS_PATH.sub('<path>', text)
    text = _TIMEZONE.sub('<timezone>', text)
    text = _DATETIME.sub('<datetime>', text)
    text = _GEO_LABEL.sub(r'\1<coord>', text)
    text = _COORD_RUN.sub('<coords>', text)
    text = _GEO_DECIMAL.sub(_redact_geo_decimal, text)
    for pattern, replacement in _PLACE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def dprint(msg: Any) -> None:
    """Write an opt-in debug line to stderr.

    Debug output is disabled unless ``DEBUG`` is True or ``--debug`` is passed.
    User-identifying values are redacted before anything is written.
    """
    if not _debug_enabled():
        return
    line = _redact_sensitive(str(msg))
    sys.stderr.write(f'[astrology:debug] {line}\n')
