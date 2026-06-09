# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Collect PyInstaller ``datas`` and ``hiddenimports`` for YoUniverse Astrology."""

from __future__ import annotations

import glob
import os
from pathlib import Path


def find_repo_root(anchor: Path) -> Path:
    """Walk parents from the spec directory until ``src/VERSION`` is found."""
    start = anchor.parent if anchor.is_file() else anchor
    for candidate in (start, *start.parents):
        if (candidate / 'src' / 'VERSION').is_file():
            return candidate
    raise FileNotFoundError(f'Cannot locate repository root (src/VERSION) from {anchor}')


def repo_root(specpath: str) -> Path:
    """Resolve repository root for PyInstaller (env override or walk from SPECPATH)."""
    env_root = os.environ.get('ASTROLOGY_ROOT')
    if env_root:
        root = Path(env_root)
        if not (root / 'src' / 'VERSION').is_file():
            raise FileNotFoundError(f'ASTROLOGY_ROOT has no src/VERSION: {root}')
        return root
    return find_repo_root(Path(specpath))


def read_version(src_astrology: Path) -> str:
    return src_astrology.joinpath('VERSION').read_text(encoding='utf-8').strip()


def collect_datas(src_astrology: Path) -> list[tuple[str, str]]:
    """Return PyInstaller ``datas`` as ``(source, dest)`` pairs under ``share/``."""
    datas: list[tuple[str, str]] = []
    dest_astrology = 'share/astrology'

    for name in (
        'astrology-svg.xml',
        'astrology-svg-table.xml',
    ):
        path = src_astrology / name
        if path.is_file():
            datas.append((str(path), dest_astrology))

    icon = src_astrology / 'icons' / 'astrology.svg'
    if icon.is_file():
        datas.append((str(icon), f'{dest_astrology}/icons'))

    for aspect in sorted(src_astrology.glob('icons/aspects/*.svg')):
        datas.append((str(aspect), f'{dest_astrology}/icons/aspects'))

    for sql in ('geonames.sql', 'famous.sql'):
        path = src_astrology / 'data' / sql
        if path.is_file():
            datas.append((str(path), f'{dest_astrology}/data'))

    for loc in sorted(src_astrology.glob('locale/*')):
        if loc.name == 'templates':
            continue
        mo = loc / 'LC_MESSAGES' / 'astrology.mo'
        if mo.is_file():
            rel = f'{dest_astrology}/locale/{loc.name}/LC_MESSAGES'
            datas.append((str(mo), rel))

    dest_swisseph = 'share/swisseph'
    for se1 in sorted(src_astrology.glob('swisseph/*.*')):
        datas.append((str(se1), dest_swisseph))

    return datas


def hiddenimports() -> list[str]:
    return [
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.GObject',
        'gi.repository.Gio',
        'gi.repository.Pango',
        'gi.repository.PangoCairo',
        'gi.repository.cairo',
        'gi.repository.Rsvg',
        'swisseph',
        'astrologymod',
        'astrologymod.branding',
        'astrologymod.install_paths',
        'astrologymod.swiss',
        'astrologymod.paths',
        'astrologymod.timezone_utils',
        'astrologymod.gtkcompat',
        'astrologymod.appmenu',
        'astrologymod.dignities',
        'astrologymod.geoname',
        'astrologymod.importfile',
        'astrologymod.zonetab',
        'astrology_app',
        'astrology_app.application',
        'astrology_app.chart',
        'astrology_app.config',
        'astrology_app.db',
        'astrology_app.globals',
        'astrology_app.i18n',
        'astrology_app.paths',
        'astrology_app.ui.main_window',
    ]


def gi_binaries_and_datas() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Best-effort collection of GObject introspection typelibs (platform-specific)."""
    binaries: list[tuple[str, str]] = []
    datas: list[tuple[str, str]] = []

    typelib_roots = []
    if 'GI_TYPELIB_PATH' in __import__('os').environ:
        typelib_roots.extend(__import__('os').environ['GI_TYPELIB_PATH'].split(':'))
    if sys_platform := __import__('sys').platform:
        if sys_platform == 'darwin':
            typelib_roots.extend([
                '/opt/homebrew/lib/girepository-1.0',
                '/usr/local/lib/girepository-1.0',
            ])
        elif sys_platform == 'win32':
            typelib_roots.extend(glob.glob('C:/msys64/ucrt64/lib/girepository-1.0'))

    seen = set()
    for root in typelib_roots:
        root_path = Path(root)
        if not root_path.is_dir():
            continue
        for typelib in root_path.glob('*.typelib'):
            if typelib.name in seen:
                continue
            seen.add(typelib.name)
            datas.append((str(typelib), 'girepository-1.0'))

    return binaries, datas
