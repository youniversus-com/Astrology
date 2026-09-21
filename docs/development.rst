Development
===========

Environment setup
-----------------

.. code-block:: bash

   ./install.sh
   source .venv/bin/activate
   pip install -r requirements-dev.txt

Dependency files and checks
---------------------------

The project keeps Python dependency sets small and layered so desktop, API,
test, documentation, and package-build workflows can be updated independently.
GTK 4, PyGObject, and librsvg are intentionally installed by the operating
system; ``./install.sh`` creates ``.venv`` with ``--system-site-packages`` so
those bindings remain importable from the virtual environment.

.. list-table::
   :header-rows: 1

   * - File
     - Used by
     - Purpose
   * - ``requirements.txt``
     - ``./install.sh``, platform CI setup
     - Base Python packages for the desktop install. This file is intentionally
       minimal because GTK and PyGObject come from system packages.
   * - ``requirements-api.txt``
     - ``make api``, ``scripts/run-api.sh``, non-Windows test setup
     - Optional FastAPI backend runtime stack. ``make api`` installs it, then
       reinstalls ``./src`` before starting ``python -m astrology_api``.
   * - ``requirements-test.txt``
     - ``scripts/install-test-deps.sh``, unit and GUI test runners
     - Pytest, property-test, timeout, and benchmark dependencies.
   * - ``requirements-dev.txt``
     - ``make lint``, ``make dev-check``, ``make test-ci``, ``make docs``
     - Developer toolchain: test and API deps plus Ruff, Pyright, mypy, and
       Sphinx.
   * - ``requirements-packaging.txt``
     - Windows/macOS PyInstaller bundle work on the target OS
     - Optional native desktop bundle tooling; Linux packaging uses distro
       build tools instead.

When changing dependency bounds, update the file consumed by the relevant
script and check related package metadata under ``src/pyproject.toml``. The
install and test scripts are the source of truth for local and CI workflows.

Common pitfalls:

- ``make docs`` and ``make api`` require an existing ``.venv``; run
  ``./install.sh`` first.
- If ``gi`` or ``Gtk`` imports fail after installing system packages, deactivate
  any active virtual environment and rerun ``./install.sh`` so
  ``include-system-site-packages`` is enabled.
- On MSYS2 UCRT64, ``scripts/install-test-deps.sh`` skips pip installation of
  the API stack because packages such as Pydantic and FastAPI are supplied by
  pacman in CI.

Daily commands
--------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``make run``
     - Reinstall app and launch ``astrology``
   * - ``make api``
     - Install API extras and launch the optional FastAPI backend
   * - ``make dev-check``
     - Lint + unit tests (fast gate)
   * - ``make test-ci``
     - Full CI suite
   * - ``make docs``
     - Build Sphinx HTML under ``docs/_build/html/``
   * - ``make update-screenshots``
     - Regenerate PNGs under ``docs/screenshots/`` (headless GTK + Xvfb)
   * - ``make test-screenshots``
     - Verify committed documentation PNGs exist
   * - ``make package-deb``
     - Build Debian package

Continuous integration
----------------------

GitHub Actions workflows under ``.github/workflows/`` are the hosted version of
the local development gates. They intentionally keep packaging, docs, security
analysis, and release verification separate so failures point at one ownership
area.

.. list-table::
   :header-rows: 1

   * - Workflow
     - When it runs
     - What it verifies
     - Local parity
   * - ``tests.yml`` (``Release tests``)
     - Pull requests and pushes to ``main``/``master``; ``v*`` tags; manual runs
     - ``ruff check tests scripts`` followed by Linux full tests, macOS unit +
       release smoke tests, and Windows unit + release smoke tests.
     - ``make dev-check`` for the fast gate, then ``make test-ci`` before pushing
       behavior changes.
   * - ``docs.yml`` (``Documentation``)
     - Pull requests and pushes to ``main``/``master``; manual runs
     - Installs GTK/PyGObject system packages, runs ``./install.sh``, verifies
       committed documentation screenshots, builds Sphinx HTML, and uploads the
       ``astrology-docs`` artifact.
     - ``make test-screenshots`` and ``make docs`` after ``./install.sh``.
   * - ``codeql.yml`` (``CodeQL``)
     - Pull requests and pushes to ``main``/``master``; weekly scheduled scan
     - Python CodeQL analysis with ``security-events: write`` permissions.
     - No exact local equivalent; keep generated code and vendored data out of
       the analysis path unless a CodeQL model documents it.
   * - ``verify-release.yml`` (``Verify signed release tag``)
     - ``v*`` tag pushes
     - Imports ``.github/gpg/release-signing.asc`` and rejects unsigned,
       lightweight, unknown-key, or bad-signature tags.
     - Create release tags with ``git tag -s vX.Y.Z -m "Release X.Y.Z"``; see
       :doc:`signing`.
   * - ``packages.yml`` (``Distribution packages``)
     - Manual runs and ``v*`` tag pushes
     - Builds Debian, RPM, macOS, and Windows artifacts. On tag pushes it also
       creates or reuses the GitHub Release and uploads package assets.
     - ``make package-deb``, ``make package-rpm``, ``make package-macos``, or
       ``make package-windows`` for targeted checks.

Operational notes:

- Run ``./install.sh`` before local docs, screenshot, or test workflows. Several
  scripts exit with ``Run ./install.sh first.`` when ``.venv`` is missing.
- Linux jobs install GTK 4, PyGObject, librsvg, ImageMagick, and Xvfb through
  ``apt``. Local GUI and screenshot tests need the same stack.
- macOS and Windows CI are smoke gates. macOS relies on Homebrew GTK/PyGObject
  paths; Windows uses MSYS2 UCRT64 packages and skips pip-installing API wheels
  that are unavailable for mingw.
- Package jobs set ``ASTROLOGY_UPDATE_EPHE=1`` so release artifacts include the
  current DE441 ephemeris bundle. Set ``ASTROLOGY_UPDATE_EPHE=0`` locally only
  when reusing an already refreshed bundle.
- Tag-triggered packaging depends on ``verify-release.yml`` passing. If a
  release asset upload is stale, rerun the tag workflow after fixing the package
  job rather than attaching files by hand.

Documentation screenshots
-------------------------

User-interface PNGs for the README and this manual live in ``docs/screenshots/``.
They are captured headlessly from fixed chart data (same as golden tests).

.. code-block:: bash

   make update-ephemeris    # if src/swisseph/*.se1 are missing
   make update-screenshots  # regenerate all PNGs
   make test-screenshots    # CI gate: PNGs must exist

Requires Xvfb on Linux (``sudo apt install xvfb``). See ``docs/screenshots/README.md``.

Tests
-----

Markers are defined in ``pytest.ini``:

- ``unit`` — logic without GTK window
- ``gui`` — headless GTK (needs Xvfb)
- ``golden`` — SVG snapshot regression
- ``release`` — install smoke checks

.. code-block:: bash

   make test-unit
   make test-gui
   make test-all

Documentation strings
---------------------

Public modules under ``astrology_app``, ``astrologymod``, and ``astrology_api``
should include:

1. A **module docstring** describing purpose.
2. **Google-style docstrings** on public classes and functions.

Sphinx autodoc picks these up automatically (see :doc:`api/index`).

Type checking
-------------

``pyright`` and ``mypy`` configuration lives in the root ``pyproject.toml``.
GTK bindings are stubbed under ``typings/``.

Contributing
------------

See `CONTRIBUTING.md <https://github.com/YOUR_ORG/astrology/blob/main/CONTRIBUTING.md>`_
in the repository root.
