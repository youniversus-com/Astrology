#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Install pysweph (Swiss Ephemeris Python bindings).
#
# MSYS2 UCRT64 uses a mingw Python fork: PyPI binary wheels are incompatible,
# so pysweph is compiled from source with pacman cmake/ninja/gcc.
set -euo pipefail

PYSWEPH_VERSION="${PYSWEPH_VERSION:-2.10.3.6}"

if [[ "${MSYSTEM:-}" == UCRT64 ]]; then
	export PATH="/ucrt64/bin:${PATH:-}"
	export PIP_NO_BUILD_ISOLATION=1
	for tool in gcc cmake ninja; do
		if ! command -v "$tool" >/dev/null 2>&1; then
			echo "Missing $tool. Install MSYS2 packages:" >&2
			echo "  pacman -S mingw-w64-ucrt-x86_64-{gcc,cmake,ninja,python-setuptools,python-build}" >&2
			exit 1
		fi
	done
	# Build deps normally pulled into pip's isolated env; install explicitly for MSYS2.
	python -m pip install --no-cache-dir setuptools-scm 'scikit-build-core>=0.9'
	python -m pip install --no-cache-dir --no-build-isolation "pysweph==${PYSWEPH_VERSION}"
else
	python -m pip install "pysweph==${PYSWEPH_VERSION}"
fi

python -c "import swisseph as swe; print('pysweph', swe.version)"
