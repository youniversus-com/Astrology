#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Run Ruff on tests/ and scripts/ (CI scope). Pass extra args to ruff.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	./install.sh
fi

# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements-dev.txt

echo "Ruff: tests/ scripts/"
ruff check tests scripts "$@"
