#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Fast developer gate: lint + unit tests (no GUI/Xvfb required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

bash "$ROOT/scripts/lint.sh"
bash "$ROOT/scripts/run_unit_tests.sh"

echo "dev-check passed."
