#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Full release test suite (unit + golden + GUI + release smoke).
# Usage:
#   ./scripts/run_tests.sh              # default CI suite (excludes slow)
#   ./scripts/run_tests.sh --all        # include slow/benchmark tests
#   ./scripts/run_tests.sh unit|gui|release
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EXTRA=()
case "${1:-}" in
  unit)
    shift
    exec "$ROOT/scripts/run_unit_tests.sh" "$@"
    ;;
  gui)
    shift
    exec "$ROOT/scripts/run_gui_tests.sh" "$@"
    ;;
  release)
    shift
    exec "$ROOT/scripts/run_release_tests.sh" "$@"
    ;;
  --all)
    shift
    EXTRA=(-m '')
    ;;
esac

if [[ ! -d .venv ]]; then
  ./install.sh
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements-dev.txt

"$ROOT/scripts/run_unit_tests.sh" "${EXTRA[@]}" "$@"
"$ROOT/scripts/run_gui_tests.sh" "${EXTRA[@]}" "$@"
"$ROOT/scripts/run_release_tests.sh" "${EXTRA[@]}" "$@"
