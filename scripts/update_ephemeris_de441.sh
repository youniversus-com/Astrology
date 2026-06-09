#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Download or copy Swiss Ephemeris .se1 files rebuilt with JPL DE441 (Apr 2026).
# See swisseph/readme.md and https://github.com/aloistr/swisseph/tree/master/ephe
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GITHUB_EPHE="${SWISSEPH_EPHE_URL:-https://raw.githubusercontent.com/aloistr/swisseph/master/ephe}"
DEST="${ASTROLOGY_EPHE_DIR:-$ROOT/src/swisseph}"
VENDOR_EPHE="$ROOT/swisseph/ephe"
PROFILE="astrology"
FROM_DIR=""
SYNC_VENV=1
SYNC_VENDOR=0
DRY_RUN=0
DOWNLOAD_JPL=0
FORCE=0

usage() {
	cat <<'EOF'
Usage: scripts/update_ephemeris_de441.sh [options]

Fetch Swiss Ephemeris compressed planet files (.se1) built with JPL DE441
and install them for Astrology (src/swisseph/, used by setup.py).

Options:
  --profile astrology|extended   File set (default: astrology)
  --from-dir PATH                Copy from local directory instead of downloading
  --sync-vendor                  Also refresh swisseph/ephe/ (vendor checkout)
  --no-venv-sync                 Do not copy into .venv/share/swisseph
  --jpl                          Download de441.eph (~2.6 GB) for SEFLG_JPLEPH use
  --force                        Re-download even if file size matches upstream
  --dry-run                      Print actions only
  -h, --help                     Show this help

Environment:
  SWISSEPH_EPHE_URL   Base URL for .se1 files (default: GitHub aloistr/swisseph ephe)
  ASTROLOGY_EPHE_DIR  Install directory (default: src/swisseph)

After updating, reinstall into the venv:
  (cd src && python setup.py install)
  # or: ./install.sh
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--profile)
			PROFILE="${2:?}"
			shift 2
			;;
		--from-dir)
			FROM_DIR="${2:?}"
			shift 2
			;;
		--sync-vendor)
			SYNC_VENDOR=1
			shift
			;;
		--no-venv-sync)
			SYNC_VENV=0
			shift
			;;
		--jpl)
			DOWNLOAD_JPL=1
			shift
			;;
		--force)
			FORCE=1
			shift
			;;
		--dry-run)
			DRY_RUN=1
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

case "$PROFILE" in
	astrology|extended) ;;
	*)
		echo "Invalid profile: $PROFILE (use astrology or extended)" >&2
		exit 1
		;;
esac

manifest_files() {
	local manifest="$ROOT/scripts/ephemeris-de441-astrology.txt"
	grep -v '^[[:space:]]*#' "$manifest" | grep -v '^[[:space:]]*$' || true
	if [[ "$PROFILE" == "extended" ]]; then
		local extra="$ROOT/scripts/ephemeris-de441-extended.txt"
		grep -v '^[[:space:]]*#' "$extra" | grep -v '^[[:space:]]*$' || true
	fi
}

remote_size() {
	local name="$1"
	local url="${GITHUB_EPHE}/${name}"
	curl -fsSLI "$url" 2>/dev/null | awk 'tolower($1)=="content-length:" {print $2; exit}'
}

same_path() {
	[[ -e "$1" && -e "$2" && "$1" -ef "$2" ]]
}

file_size() {
	local path="$1"
	local size
	size="$(stat -c '%s' "$path" 2>/dev/null || true)"
	if [[ -n "$size" ]]; then
		echo "$size"
		return 0
	fi
	size="$(stat -f '%z' "$path" 2>/dev/null || true)"
	if [[ -n "$size" ]]; then
		echo "$size"
		return 0
	fi
	echo 0
}

safe_cp() {
	local src="$1"
	local dest="$2"
	if same_path "$src" "$dest"; then
		echo "  OK (in place) $(basename "$dest")"
		return 0
	fi
	cp -f "$src" "$dest"
}

fetch_one() {
	local name="$1"
	local dest_dir="$2"
	local src=""
	local dest="$dest_dir/$name"
	mkdir -p "$dest_dir"

	if [[ -n "$FROM_DIR" ]]; then
		src="$FROM_DIR/$name"
		if [[ ! -f "$src" ]]; then
			echo "Missing in --from-dir: $src" >&2
			return 1
		fi
	elif [[ -f "$VENDOR_EPHE/$name" && "$FORCE" -eq 0 ]]; then
		src="$VENDOR_EPHE/$name"
	else
		local url="${GITHUB_EPHE}/${name}"
		local remote
		remote="$(remote_size "$name" || true)"
		if [[ "$FORCE" -eq 0 && -f "$dest" && -n "$remote" && "$(file_size "$dest")" == "$remote" ]]; then
			echo "  OK (cached) $name"
			return 0
		fi
		echo "  GET $url"
		if [[ "$DRY_RUN" -eq 1 ]]; then
			return 0
		fi
		curl -fL --retry 3 --retry-delay 2 -o "$dest.part" "$url"
		mv "$dest.part" "$dest"
		return 0
	fi

	echo "  CP $src -> $dest"
	if [[ "$DRY_RUN" -eq 1 ]]; then
		return 0
	fi
	safe_cp "$src" "$dest"
}

copy_fixstars() {
	local dest="$DEST/fixstars.cat"
	if [[ -f "$dest" ]]; then
		echo "  OK fixstars.cat"
		return 0
	fi
	local candidates=(
		"$VENDOR_EPHE/fixstars.cat"
		"$ROOT/src/swisseph/fixstars.cat"
	)
	for src in "${candidates[@]}"; do
		if [[ -f "$src" ]]; then
			if [[ "$DRY_RUN" -eq 1 ]]; then
				echo "  CP fixstars.cat from $(dirname "$src")"
			else
				safe_cp "$src" "$dest"
				echo "  fixstars.cat from $src"
			fi
			return 0
		fi
	done
	echo "  warn: fixstars.cat not found (fixed-star features may be limited)" >&2
}

sync_tree() {
	local src_dir="$1"
	local dest_dir="$2"
	mkdir -p "$dest_dir"
	while IFS= read -r name; do
		[[ -z "$name" ]] && continue
		if [[ ! -f "$src_dir/$name" ]]; then
			echo "Missing: $src_dir/$name" >&2
			return 1
		fi
		if [[ "$DRY_RUN" -eq 1 ]]; then
			echo "  CP $src_dir/$name -> $dest_dir/$name"
		else
			safe_cp "$src_dir/$name" "$dest_dir/$name"
		fi
	done < <(manifest_files)
}

echo "Swiss Ephemeris DE441 update (profile=$PROFILE)"
echo "  dest: $DEST"
if [[ -n "$FROM_DIR" ]]; then
	echo "  from: $FROM_DIR"
elif [[ -d "$VENDOR_EPHE" ]]; then
	echo "  vendor cache: $VENDOR_EPHE (used when present, else download)"
fi

FILES=()
while IFS= read -r name; do
	[[ -z "$name" ]] && continue
	FILES+=("$name")
done < <(manifest_files)
if [[ ${#FILES[@]} -eq 0 ]]; then
	echo "No files listed in manifest." >&2
	exit 1
fi

for name in "${FILES[@]}"; do
	fetch_one "$name" "$DEST"
done
copy_fixstars

if [[ "$DRY_RUN" -eq 0 ]]; then
	mkdir -p "$VENDOR_EPHE"
	for name in "${FILES[@]}"; do
		safe_cp "$DEST/$name" "$VENDOR_EPHE/$name"
	done
	echo "  vendor: $VENDOR_EPHE"
fi

if [[ "$SYNC_VENDOR" -eq 1 && -n "$FROM_DIR" && "$FROM_DIR" != "$VENDOR_EPHE" ]]; then
	echo "  syncing vendor from $FROM_DIR"
	sync_tree "$FROM_DIR" "$VENDOR_EPHE"
fi

if [[ "$SYNC_VENV" -eq 1 && -d "$ROOT/.venv" ]]; then
	VEPH="$ROOT/.venv/share/swisseph"
	echo "  venv: $VEPH"
	if [[ "$DRY_RUN" -eq 1 ]]; then
		echo "  (would sync ${#FILES[@]} files to venv)"
	else
		mkdir -p "$VEPH"
		for name in "${FILES[@]}"; do
			safe_cp "$DEST/$name" "$VEPH/$name"
		done
		[[ -f "$DEST/fixstars.cat" ]] && safe_cp "$DEST/fixstars.cat" "$VEPH/fixstars.cat"
	fi
fi

if [[ "$DOWNLOAD_JPL" -eq 1 ]]; then
	JPL_URL="${SWISSEPH_JPL_URL:-https://ssd.jpl.nasa.gov/ftp/eph/planets/Linux/de441/linux_m13000p17000.441}"
	JPL_DEST="${ASTROLOGY_JPL_DIR:-$HOME/.config/com.youniverse.astrology/swiss_ephemeris}/de441.eph"
	echo "  JPL DE441: $JPL_URL"
	echo "  -> $JPL_DEST (~2.6 GB)"
	if [[ "$DRY_RUN" -eq 1 ]]; then
		:
	else
		mkdir -p "$(dirname "$JPL_DEST")"
		if [[ -f "$JPL_DEST" && "$FORCE" -eq 0 ]]; then
			echo "  JPL file already present"
		else
			curl -fL --retry 3 --retry-delay 5 -o "$JPL_DEST.part" "$JPL_URL"
			mv "$JPL_DEST.part" "$JPL_DEST"
		fi
		echo "  expected md5: a7b2a5b8b2ebed52ea4da2304958053b"
		if command -v md5sum >/dev/null 2>&1; then
			md5sum "$JPL_DEST"
		fi
	fi
fi

echo "Done. Reinstall Astrology if the venv was already set up:"
echo "  ./install.sh   # or: (cd src && python setup.py install)"
