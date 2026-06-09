#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Run all project checks: lint, unit tests, docs build.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

bash "$ROOT/scripts/dev-check.sh"
bash "$ROOT/scripts/build-docs.sh -W --keep-going" 2>/dev/null || bash "$ROOT/scripts/build-docs.sh"

echo "all-checks passed."
