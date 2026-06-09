#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build astrology RPM package (Fedora/RHEL). Uses rpmbuild; optional mock.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/package-common.sh
source "$ROOT/scripts/package-common.sh"

if ! command -v rpmbuild >/dev/null 2>&1; then
	echo "rpmbuild not found. On Fedora: sudo dnf install rpm-build rpmdevtools" >&2
	echo "On RHEL: sudo dnf install rpm-build" >&2
	exit 1
fi

UPDATE_EPHE="${ASTROLOGY_UPDATE_EPHE:-1}"
if [[ "$UPDATE_EPHE" == 1 ]]; then
	echo "Refreshing Swiss Ephemeris data (DE441)..."
	bash "$ROOT/scripts/update_ephemeris_de441.sh"
fi

require_ephemeris "$ROOT/src/swisseph"

VERSION="$(read_version)"
ensure_packages_dir

TARBALL="$ROOT/dist/packages/astrology-${VERSION}.tar.gz"
echo "Creating source tarball: $TARBALL"
tar czf "$TARBALL" \
	--exclude='__pycache__' \
	--exclude='*.py[cod]' \
	--exclude='build' \
	--exclude='.pytest_cache' \
	--exclude='astrology.egg-info' \
	--transform 's,^,astrology/,' \
	-C "$ROOT/src" \
	.

RPMTOP="${RPMTOP:-$ROOT/build/rpm}"
mkdir -p "$RPMTOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
cp -f "$TARBALL" "$RPMTOP/SOURCES/"
cp -f "$ROOT/packaging/rpm/astrology.spec" "$RPMTOP/SPECS/"

echo "Running rpmbuild (topdir: $RPMTOP)..."
rpmbuild -ba \
	--define "_topdir $RPMTOP" \
	--define "oa_version $VERSION" \
	"$RPMTOP/SPECS/astrology.spec"

shopt -s nullglob
rpms=( "$RPMTOP/RPMS"/*/*.rpm )
if ((${#rpms[@]} == 0)); then
	echo "No RPM produced under $RPMTOP/RPMS" >&2
	exit 1
fi

for rpm in "${rpms[@]}"; do
	cp -a "$rpm" "$ROOT/dist/packages/"
	echo "  -> dist/packages/$(basename "$rpm")"
done

echo "RPM package build complete."
