#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build Debian and RPM packages for Astrology into dist/packages/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ASTROLOGY_UPDATE_EPHE="${ASTROLOGY_UPDATE_EPHE:-1}"

build_deb=1
build_rpm=1
for arg in "$@"; do
	case "$arg" in
		--deb-only) build_rpm=0 ;;
		--rpm-only) build_deb=0 ;;
		-h|--help)
			cat <<'EOF'
Usage: scripts/build-packages.sh [--deb-only | --rpm-only]

Build distribution packages into dist/packages/.
Ephemeris files are refreshed unless ASTROLOGY_UPDATE_EPHE=0.

Environment:
  ASTROLOGY_UPDATE_EPHE=0   Skip scripts/update_ephemeris_de441.sh
EOF
			exit 0
			;;
		*)
			echo "Unknown option: $arg" >&2
			exit 1
			;;
	esac
done

mkdir -p "$ROOT/dist/packages"

if ((build_deb)); then
	if command -v dpkg-buildpackage >/dev/null 2>&1; then
		bash "$ROOT/scripts/build-deb.sh"
	else
		echo "Skipping .deb: dpkg-buildpackage not found (install dpkg-dev, debhelper, dh-python)." >&2
	fi
fi

if ((build_rpm)); then
	bash "$ROOT/scripts/build-rpm.sh"
fi

echo "Artifacts in: $ROOT/dist/packages/"
