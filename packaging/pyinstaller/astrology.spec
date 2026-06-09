# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""PyInstaller spec for YoUniverse Astrology (run on target OS only)."""

import os
import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH)
if SPEC_DIR.is_file():
    SPEC_DIR = SPEC_DIR.parent
sys.path.insert(0, str(SPEC_DIR))

from bundle_data import collect_datas, gi_binaries_and_datas, hiddenimports, read_version, repo_root  # noqa: E402

ROOT = repo_root(str(SPEC_DIR))
SRC = ROOT / 'src'

VERSION = read_version(SRC)
APP_ID = 'com.youniverse.astrology.Desktop'
APP_NAME = 'Astrology'

datas = collect_datas(SRC)
gi_binaries, gi_datas = gi_binaries_and_datas()
datas.extend(gi_datas)
binaries = list(gi_binaries)

block_cipher = None

a = Analysis(
    [str(SRC / 'astrology')],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports(),
    hookspath=[str(SPEC_DIR / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=os.environ.get('CODESIGN_IDENTITY') or None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=None,
        bundle_identifier=APP_ID,
        version=VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': 'YoUniverse Astrology',
            'CFBundleIdentifier': APP_ID,
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': True,
        },
    )
