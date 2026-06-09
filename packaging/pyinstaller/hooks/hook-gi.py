# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""PyInstaller hook: collect gi / PyGObject runtime pieces when available."""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hiddenimports = collect_submodules('gi')
binaries = collect_dynamic_libs('gi')
