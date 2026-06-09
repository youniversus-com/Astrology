.PHONY: install lint test test-unit test-gui test-golden test-screenshots test-release test-all test-ci \
	clean update-golden update-screenshots update-ephemeris package package-deb package-rpm \
	package-macos package-windows package-desktop \
	docs dev-check all-checks run api spdx reuse-lint

install:
	./install.sh

run:
	@. .venv/bin/activate && pip install -q --force-reinstall --no-deps ./src && astrology

api:
	bash scripts/run-api.sh

update-ephemeris:
	bash scripts/update_ephemeris_de441.sh
	@if [ -d .venv ]; then \
		. .venv/bin/activate; \
		( cd src && python setup.py install ); \
	fi

lint:
	bash scripts/lint.sh

dev-check:
	bash scripts/dev-check.sh

all-checks:
	bash scripts/all-checks.sh

docs:
	bash scripts/build-docs.sh

docs-open: docs
	@xdg-open docs/_build/html/index.html 2>/dev/null || open docs/_build/html/index.html 2>/dev/null || true

spdx:
	python3 scripts/apply_spdx_headers.py

reuse-lint:
	@command -v reuse >/dev/null || { echo "Install: pip install reuse"; exit 1; }
	reuse lint

test: test-ci

test-ci:
	./scripts/run_tests.sh

test-all:
	./scripts/run_tests.sh --all

test-unit:
	./scripts/run_unit_tests.sh

test-gui:
	./scripts/run_gui_tests.sh

test-golden:
	./scripts/run_gui_tests.sh tests/gui/golden/

test-release:
	./scripts/run_release_tests.sh

update-golden:
	./scripts/run_gui_tests.sh tests/gui/golden/ --update-golden -q

update-screenshots:
	bash scripts/update-screenshots.sh

test-screenshots:
	bash scripts/verify-screenshots.sh

package-deb:
	bash scripts/build-deb.sh

package-rpm:
	bash scripts/build-rpm.sh

package:
	bash scripts/build-packages.sh

package-macos:
	bash scripts/build-macos.sh

package-windows:
	bash scripts/build-windows.sh

package-desktop:
	bash scripts/build-desktop.sh

clean:
	rm -rf .pytest_cache build/rpm build/macos-venv build/windows-venv build/pyinstaller src/build
	rm -rf src/debian/astrology src/debian/.debhelper
	rm -f src/debian/files src/debian/debhelper-build-stamp
	rm -f src/debian/*.debhelper.* src/debian/*.substvars
	find tests -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f src/debian/openastro.org.* 2>/dev/null || true
	rm -rf src/debian/.debhelper/generated/openastro.org 2>/dev/null || true
