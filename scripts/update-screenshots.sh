#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Regenerate documentation PNGs under docs/screenshots/ (headless GTK + Xvfb).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	echo "Run ./install.sh first."
	exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate

if ! compgen -G "$ROOT/src/swisseph/"'*.se1' >/dev/null; then
	echo "Swiss Ephemeris files missing; running update_ephemeris_de441.sh..."
	bash "$ROOT/scripts/update_ephemeris_de441.sh"
fi

bash "$ROOT/scripts/install-test-deps.sh"

# shellcheck source=scripts/test-env.sh
source "$ROOT/scripts/test-env.sh"
configure_test_gtk_env

if ! command -v Xvfb >/dev/null 2>&1 && [[ "$(uname -s)" != Darwin ]]; then
	echo "Install Xvfb: sudo apt install xvfb"
	exit 1
fi

exec pytest tests/gui/screenshots/test_doc_screenshots.py::test_capture_documentation_screenshots \
	-m screenshot --update-screenshots -q "$@"
