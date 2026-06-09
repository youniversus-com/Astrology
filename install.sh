#!/usr/bin/env bash
# Install Astrology and dependencies into .venv (Python 3.12+).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Preflight must use system Python: an activated .venv without system-site-packages
# cannot import PyGObject (gi) even when apt packages are installed.
if [[ -x /usr/bin/python3 ]]; then
	SYS_PYTHON=/usr/bin/python3
else
	SYS_PYTHON="$(command -v python3)"
fi

if [[ -d .venv ]] && grep -q '^include-system-site-packages = false' .venv/pyvenv.cfg 2>/dev/null; then
	sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' .venv/pyvenv.cfg
fi

need_apt=false
if ! "$SYS_PYTHON" -c "from gi import require_version; require_version('Gtk', '4.0'); require_version('Rsvg', '2.0')" 2>/dev/null; then
	need_apt=true
fi
if ! python3-config --includes >/dev/null 2>&1; then
	need_apt=true
fi
if $need_apt; then
	echo "Install system packages first:"
	echo "  sudo apt install python3-dev python3-gi python3-gi-cairo \\"
	echo "    gir1.2-gtk-4.0 gir1.2-rsvg-2.0 librsvg2-bin imagemagick"
	echo ""
	echo "If packages are already installed, deactivate the venv and retry:"
	echo "  deactivate && ./install.sh"
	exit 1
fi

if [[ ! -d .venv ]]; then
	"$SYS_PYTHON" -m venv --system-site-packages .venv
else
	if grep -q '^include-system-site-packages = false' .venv/pyvenv.cfg 2>/dev/null; then
		sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' .venv/pyvenv.cfg
	fi
fi

# shellcheck source=/dev/null
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt

echo "Installing pysweph (Swiss Ephemeris Python bindings)..."
pip install 'pysweph==2.10.3.6'

if [[ "${ASTROLOGY_SKIP_EPHE_UPDATE:-0}" != 1 ]]; then
	echo "Updating Swiss Ephemeris data (JPL DE441 .se1 files)..."
	bash scripts/update_ephemeris_de441.sh
fi

echo "Removing previous install artifacts from venv (if any)..."
pip uninstall -y astrology 2>/dev/null || true
for legacy_pkg in openastromod OpenAstro.org openastro.org astrology; do
	pip uninstall -y "$legacy_pkg" 2>/dev/null || true
done
for legacy_bin in openastro astrology; do
	rm -f ".venv/bin/$legacy_bin"
done
rm -f .venv/share/applications/openastro.desktop .venv/share/applications/OpenAstro.desktop
rm -rf .venv/share/openastro.org
find .venv/lib -maxdepth 4 -type d -name 'openastromod' -exec rm -rf {} + 2>/dev/null || true
find .venv/lib -maxdepth 2 -type d -name 'OpenAstro.org*.egg-info' -exec rm -rf {} + 2>/dev/null || true

echo "Installing Astrology (app, geonames, ephemeris data)..."
pip install --force-reinstall --no-deps -e ./src

if python3 -c "import run_astrology; run_astrology._bootstrap(); import astrology_app.chart as c; import pathlib; p=pathlib.Path(c.__file__); raise SystemExit(0 if 'dist-packages' not in str(p) else 1)" 2>/dev/null; then
	:
else
	echo ""
	echo "WARNING: Python is still loading astrology_app from the system package:"
	python3 -c "import run_astrology; run_astrology._bootstrap(); import astrology_app.chart as c; print('  ', c.__file__)" 2>/dev/null || true
	echo "  Remove it so this tree is used: sudo apt remove astrology"
	echo "  Or always run:  source .venv/bin/activate && astrology"
	echo ""
fi

pip install -q -r requirements-dev.txt 2>/dev/null || true

echo ""
echo "Done. Run:"
echo "  source .venv/bin/activate"
echo "  astrology"
echo ""
echo "Tests:"
echo "  make test-unit"
echo "  make test-gui     # needs: sudo apt install xvfb"
echo "  make test-ci"
