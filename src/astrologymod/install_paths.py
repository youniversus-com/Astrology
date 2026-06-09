# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Resolve installed and bundled ``share/`` paths (Linux, PyInstaller, macOS .app)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _package_root() -> Path:
    """Directory containing ``astrology_app`` and ``astrologymod`` packages."""
    return Path(__file__).resolve().parent.parent


def _frozen_resource_base() -> Path | None:
    """PyInstaller one-dir/one-file or macOS ``.app`` resource root."""
    if not getattr(sys, 'frozen', False):
        return None
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        return Path(meipass)
    exe = Path(sys.executable).resolve()
    contents = exe.parent.parent
    resources = contents / 'Resources'
    if resources.is_dir() and (resources / 'share').is_dir():
        return resources
    return exe.parent


def share_search_roots() -> list[Path]:
    """Ordered roots that may contain ``astrology/`` or ``swisseph/`` subtrees."""
    roots: list[Path] = []
    frozen = _frozen_resource_base()
    if frozen is not None:
        roots.append(frozen / 'share')
        roots.append(frozen)

    pkg = _package_root()
    roots.append(pkg)
    roots.append(Path(sys.prefix) / 'share')

    if sys.platform != 'win32':
        for prefix in ('/usr/local', '/usr'):
            roots.append(Path(prefix) / 'share')

    # De-duplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        try:
            key = root.resolve()
        except OSError:
            key = root
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def find_astrology_datadir() -> Path | None:
    """Return directory containing packaged chart assets (``astrology-svg.xml``)."""
    marker = 'astrology-svg.xml'
    pkg = _package_root()
    if (pkg / marker).is_file():
        return pkg

    for root in share_search_roots():
        for candidate in (root / 'astrology', root):
            if (candidate / marker).is_file():
                return candidate
    return None


def find_data_file(filename: str, datadir: Path | None = None) -> Path:
    """Resolve a bundled data file (e.g. ``geonames.sql``)."""
    datadir = datadir or find_astrology_datadir()
    candidates: list[Path] = []
    if datadir is not None:
        candidates.extend([datadir / 'data' / filename, datadir / filename])
    candidates.append(_package_root() / 'data' / filename)
    candidates.append(Path(sys.prefix) / 'share' / 'astrology' / 'data' / filename)
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0] if candidates else Path(filename)


def ephemeris_search_paths(user_swiss_dir: Path) -> str:
    """Colon-separated Swiss Ephemeris search path for ``swe.set_ephe_path``."""
    dirs: list[Path] = []
    for root in share_search_roots():
        for candidate in (root / 'swisseph', root / 'share' / 'swisseph'):
            if candidate.is_dir() and any(candidate.glob('*.se1')):
                dirs.append(candidate)
    user_path = Path(user_swiss_dir)
    dirs.append(user_path)

    seen: set[Path] = set()
    parts: list[str] = []
    for d in dirs:
        try:
            key = d.resolve()
        except OSError:
            key = d
        if key in seen:
            continue
        seen.add(key)
        parts.append(str(d))
    return ':'.join(parts) if parts else str(user_path)
