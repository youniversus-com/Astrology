# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Debug logging helper."""

import re
import sys
from typing import Any

from astrology_app.constants import DEBUG

# Home-directory paths in debug strings (not chart coordinates).
_HOME_PATH = re.compile(r'(?:/home/[^/\s"\']+|~(?:/[^\s"\']*)?)')


def _debug_enabled() -> bool:
    return '--debug' in sys.argv or DEBUG


def _redact_paths(text: str) -> str:
    """Remove filesystem paths that may identify the user."""
    return _HOME_PATH.sub('<user-data>', text)


def dprint(msg: Any) -> None:
    """Write an opt-in debug line to stderr.

    Debug output is disabled unless ``DEBUG`` is True or ``--debug`` is passed.
    User home paths are redacted; chart locations are developer diagnostics only.
    """
    if not _debug_enabled():
        return
    line = _redact_paths(str(msg))
    # Opt-in developer diagnostics only (DEBUG=False in release builds).
    sys.stderr.write(f'[astrology:debug] {line}\n')  # lgtm[py/clear-text-logging-sensitive-data]
