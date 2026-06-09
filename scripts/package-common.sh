#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Shared helpers for distribution package builds (sourced, not executed).
set -euo pipefail

: "${ROOT:?ROOT must be set by caller}"

read_version() {
	tr -d '[:space:]' <"$ROOT/src/VERSION"
}

require_ephemeris() {
	local dir="$1"
	local list="$ROOT/scripts/ephemeris-de441-astrology.txt"
	local missing=0
	if [[ ! -d "$dir" ]]; then
		echo "Ephemeris directory missing: $dir" >&2
		exit 1
	fi
	while IFS= read -r line || [[ -n "$line" ]]; do
		line="${line%%#*}"
		line="${line//[[:space:]]/}"
		[[ -z "$line" ]] && continue
		if [[ ! -f "$dir/$line" ]]; then
			echo "Missing ephemeris file: $dir/$line" >&2
			missing=1
		fi
	done <"$list"
	if ((missing)); then
		cat >&2 <<EOF
Swiss Ephemeris .se1 files are required before building packages.
Run from the repository root:
  bash scripts/update_ephemeris_de441.sh
Or set ASTROLOGY_SKIP_EPHE_UPDATE=0 and use scripts/build-packages.sh (updates automatically).
EOF
		exit 1
	fi
}

ensure_packages_dir() {
	mkdir -p "$ROOT/dist/packages"
}
