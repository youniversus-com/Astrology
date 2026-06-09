#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Fast unit tests (logic + lightweight GTK helper checks).
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

# shellcheck source=scripts/test-env.sh
source "$ROOT/scripts/test-env.sh"
configure_test_gtk_env

exec pytest tests/unit -m unit "$@"
