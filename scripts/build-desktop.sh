#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build native desktop bundles for the current platform (or both on CI matrix).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

case "$(uname -s)" in
	Darwin)
		bash "$ROOT/scripts/build-macos.sh"
		;;
	Linux)
		echo "For Linux use: make package-deb / make package-rpm" >&2
		echo "For cross-platform desktop bundles, run build-macos.sh or build-windows.sh on target OS." >&2
		exit 1
		;;
	MINGW*|MSYS*)
		bash "$ROOT/scripts/build-windows.sh"
		;;
	*)
		echo "Unsupported platform: $(uname -s)" >&2
		exit 1
		;;
esac
