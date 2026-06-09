#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Build Sphinx HTML documentation into docs/_build/html/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	echo "Run ./install.sh first." >&2
	exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements-dev.txt

echo "Building documentation..."
sphinx-build -b html docs docs/_build/html "$@"

echo ""
echo "Documentation ready: docs/_build/html/index.html"
