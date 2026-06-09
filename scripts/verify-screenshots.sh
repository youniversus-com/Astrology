#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Verify committed documentation screenshots exist.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	echo "Run ./install.sh first." >&2
	exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

exec pytest tests/gui/screenshots/test_doc_screenshots.py::test_documentation_screenshots_exist -q "$@"
