#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build a native macOS .app bundle with PyInstaller (run on macOS only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
	echo "build-macos.sh must run on macOS." >&2
	exit 1
fi

# shellcheck source=scripts/package-common.sh
source "$ROOT/scripts/package-common.sh"

UPDATE_EPHE="${ASTROLOGY_UPDATE_EPHE:-1}"
if [[ "$UPDATE_EPHE" == 1 ]]; then
	bash "$ROOT/scripts/update_ephemeris_de441.sh"
fi
require_ephemeris "$ROOT/src/swisseph"
ensure_packages_dir

VERSION="$(read_version)"

if ! command -v brew >/dev/null 2>&1; then
	echo "Homebrew required: https://brew.sh" >&2
	exit 1
fi

echo "Checking Homebrew dependencies..."
brew list python@3.12 &>/dev/null || brew install python@3.12
brew list gtk4 &>/dev/null || brew install gtk4
brew list pygobject3 &>/dev/null || brew install pygobject3
brew list librsvg &>/dev/null || brew install librsvg
brew list gobject-introspection &>/dev/null || brew install gobject-introspection

PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
VENV="$ROOT/build/macos-venv"
if [[ ! -d "$VENV" ]]; then
	"$PYTHON" -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
pip install -U pip wheel
pip install pyinstaller 'pysweph==2.10.3.6'

export GI_TYPELIB_PATH
GI_TYPELIB_PATH="$(brew --prefix)/lib/girepository-1.0:${GI_TYPELIB_PATH:-}"
export DYLD_LIBRARY_PATH
DYLD_LIBRARY_PATH="$(brew --prefix)/lib:${DYLD_LIBRARY_PATH:-}"
export ASTROLOGY_ROOT="$ROOT"

echo "Running PyInstaller..."
pyinstaller --noconfirm --clean \
	--distpath "$ROOT/build/pyinstaller/dist" \
	--workpath "$ROOT/build/pyinstaller/work" \
	"$ROOT/packaging/pyinstaller/astrology.spec"

APP="$ROOT/build/pyinstaller/dist/Astrology.app"
if [[ ! -d "$APP" ]]; then
	echo "Expected bundle not found: $APP" >&2
	exit 1
fi

OUT="$ROOT/dist/packages/Astrology-${VERSION}-macos.app.tar.gz"
tar czf "$OUT" -C "$ROOT/build/pyinstaller/dist" Astrology.app
echo "macOS bundle: $APP"
echo "Archive:      $OUT"
echo "Open with:    open \"$APP\""
