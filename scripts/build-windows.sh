#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build a native Windows folder bundle with PyInstaller (run inside MSYS2 UCRT64).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${MSYSTEM:-}" != "UCRT64" ]]; then
	cat >&2 <<'EOF'
build-windows.sh must run in MSYS2 UCRT64 (64-bit).

Install MSYS2 from https://www.msys2.org/ then:

  pacman -Syu
  pacman -S mingw-w64-ucrt-x86_64-{python,python-pip,gcc,cmake,ninja,gtk4,python-gobject,
    python-cairo,pango,librsvg,gettext,tools} zip
  # open "UCRT64" shell from Start Menu
  cd /path/to/astrology
  bash scripts/build-windows.sh
EOF
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

VENV="$ROOT/build/windows-venv"
if [[ ! -d "$VENV" ]]; then
	python -m venv --system-site-packages "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install -U pip wheel
bash "$ROOT/scripts/install-pysweph.sh"
python -m pip install pyinstaller

export GI_TYPELIB_PATH="/ucrt64/lib/girepository-1.0:${GI_TYPELIB_PATH:-}"
export PATH="/ucrt64/bin:$PATH"
export ASTROLOGY_ROOT="$ROOT"

echo "Running PyInstaller..."
pyinstaller --noconfirm --clean \
	--distpath "$ROOT/build/pyinstaller/dist" \
	--workpath "$ROOT/build/pyinstaller/work" \
	"$ROOT/packaging/pyinstaller/astrology.spec"

DIST="$ROOT/build/pyinstaller/dist/Astrology"
if [[ ! -d "$DIST" ]]; then
	echo "Expected output not found: $DIST" >&2
	exit 1
fi

ZIP="$ROOT/dist/packages/Astrology-${VERSION}-windows-ucrt64.zip"
rm -f "$ZIP"
(
	cd "$ROOT/build/pyinstaller/dist"
	zip -r "$ZIP" Astrology
)
echo "Windows bundle: $DIST"
echo "Archive:        $ZIP"
echo "Run:            \"$DIST/Astrology.exe\""
