#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build astrology Debian binary package (.deb).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/package-common.sh
source "$ROOT/scripts/package-common.sh"

UPDATE_EPHE="${ASTROLOGY_UPDATE_EPHE:-1}"
if [[ "$UPDATE_EPHE" == 1 ]]; then
	echo "Refreshing Swiss Ephemeris data (DE441)..."
	bash "$ROOT/scripts/update_ephemeris_de441.sh"
fi

require_ephemeris "$ROOT/src/swisseph"

VERSION="$(read_version)"
if ! head -n1 "$ROOT/src/debian/changelog" | grep -qF "astrology (${VERSION}"; then
	echo "debian/changelog top entry does not match src/VERSION (${VERSION})." >&2
	echo "Update debian/changelog before building (e.g. dch --newversion ${VERSION}-1)." >&2
	exit 1
fi

ensure_packages_dir

echo "Building Debian package (native source in src/)..."
(
	cd "$ROOT/src"
	dpkg-buildpackage -us -uc -b
)

shopt -s nullglob
debs=( "$ROOT"/astrology_"${VERSION}"*_all.deb )
if ((${#debs[@]} == 0)); then
	echo "No .deb produced in $ROOT (expected astrology_${VERSION}*_all.deb)" >&2
	exit 1
fi

for deb in "${debs[@]}"; do
	cp -a "$deb" "$ROOT/dist/packages/"
	echo "  -> dist/packages/$(basename "$deb")"
done

echo "Debian package build complete."
