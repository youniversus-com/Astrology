#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Install pytest + optional API test deps for the active venv.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python -m pip install -q -r "$ROOT/requirements-test.txt"

# MSYS2 UCRT64: pydantic-core/ruff have no pip wheels for mingw; API stack comes
# from pacman (see .github/workflows/tests.yml) into system-site-packages.
if [[ "${MSYSTEM:-}" != UCRT64 ]]; then
	python -m pip install -q -r "$ROOT/requirements-api.txt"
fi
