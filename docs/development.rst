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

GitHub Actions is split by responsibility so routine pull requests, docs
updates, security analysis, and release tags can fail independently.

.. list-table::
   :header-rows: 1

   * - Workflow
     - Triggers
     - What it proves
   * - ``.github/workflows/tests.yml``
     - Pushes and pull requests targeting ``main`` or ``master``, ``v*`` tags,
       and manual dispatch
     - Lints ``tests`` and ``scripts`` with Ruff, then runs the Linux full test
       suite plus macOS and Windows unit/release smoke checks.
   * - ``.github/workflows/docs.yml``
     - Pushes and pull requests targeting ``main`` or ``master``, and manual
       dispatch
     - Installs the app and doc tools, verifies committed screenshot assets,
       builds Sphinx HTML, and uploads the HTML artifact.
   * - ``.github/workflows/codeql.yml``
     - Pushes and pull requests targeting ``main`` or ``master`` plus the
       weekly Monday schedule
     - Runs Python CodeQL with read-only repository permissions and
       ``security-events: write`` for alerts.
   * - ``.github/workflows/verify-release.yml``
     - ``v*`` tags
     - Imports ``.github/gpg/release-signing.asc`` and rejects lightweight,
       unsigned, unknown-key, or bad-signature release tags.
   * - ``.github/workflows/packages.yml``
     - ``v*`` tags and manual dispatch
     - Builds Debian, RPM, macOS, and Windows packages. Tag pushes also create
       or reuse the GitHub Release, upload package assets, and check that the
       release has at least as many assets as the build produced.

Local parity commands:

.. code-block:: bash

   ./install.sh
   make dev-check       # Ruff plus unit tests; closest fast PR gate
   make test-ci         # Linux full suite: unit, GUI/golden, release smoke
   make test-screenshots
   make docs

Useful troubleshooting constraints:

- GTK 4, PyGObject, and librsvg come from system packages. Recreate ``.venv``
  with ``./install.sh`` after installing them so ``--system-site-packages`` is
  set correctly.
- Linux GUI and screenshot checks need Xvfb; ``scripts/run_gui_tests.sh`` will
  stop with ``Install Xvfb: sudo apt install xvfb`` when it is missing.
- macOS and Windows workflow jobs are smoke checks, not full GUI parity. They
  configure platform-specific GTK lookup paths before running unit and release
  smoke tests.
- Manual ``packages.yml`` runs are package-build smoke tests only. Release
  creation and asset upload happen only for pushed ``v*`` tags.

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
