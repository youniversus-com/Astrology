#!/usr/bin/env bash
# Start the YoUniverse Astrology HTTP API (optional; desktop uses GTK directly).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	echo "Run ./install.sh first."
	exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

pip install -q -r requirements-api.txt
pip install -q --force-reinstall --no-deps ./src

HOST="${ASTROLOGY_API_HOST:-127.0.0.1}"
PORT="${ASTROLOGY_API_PORT:-8765}"

echo "YoUniverse API → http://${HOST}:${PORT}"
echo "OpenAPI docs → http://${HOST}:${PORT}/docs"
exec python -m astrology_api
