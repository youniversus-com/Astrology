#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Release smoke tests (venv layout, imports). Run after install.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Run ./install.sh first."
  exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate
bash "$ROOT/scripts/install-test-deps.sh"

export ASTROLOGY_TEST=1
exec pytest tests/release -m release "$@"
