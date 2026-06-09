#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Shared GTK / display environment for test scripts (sourced, not executed).

configure_test_gtk_env() {
	export ASTROLOGY_TEST=1

	if [[ "${MSYSTEM:-}" == UCRT64 ]]; then
		export GI_TYPELIB_PATH="/ucrt64/lib/girepository-1.0:${GI_TYPELIB_PATH:-}"
		export PATH="/ucrt64/bin:${PATH:-}"
		return 0
	fi

	if [[ "$(uname -s)" == Darwin ]]; then
		if command -v brew >/dev/null 2>&1; then
			local brew_prefix
			brew_prefix="$(brew --prefix)"
			export GI_TYPELIB_PATH="${brew_prefix}/lib/girepository-1.0:${GI_TYPELIB_PATH:-}"
			export DYLD_LIBRARY_PATH="${brew_prefix}/lib:${DYLD_LIBRARY_PATH:-}"
			local py_site="${brew_prefix}/lib/python3.12/site-packages"
			if [[ -d "$py_site" ]]; then
				export PYTHONPATH="${py_site}${PYTHONPATH:+:${PYTHONPATH}}"
			fi
		fi
		return 0
	fi

	export GDK_BACKEND=x11
	if [[ -n "${DISPLAY:-}" ]]; then
		return 0
	fi
	export DISPLAY=:99
	if command -v Xvfb >/dev/null 2>&1; then
		Xvfb :99 -screen 0 1280x720x24 >/dev/null 2>&1 &
		XVFB_PID=$!
		trap 'kill "$XVFB_PID" 2>/dev/null || true' EXIT
		sleep 0.5
	else
		echo "Warning: DISPLAY unset and Xvfb not installed; GTK tests may fail." >&2
	fi
}
