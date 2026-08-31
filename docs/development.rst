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

GitHub Actions uses the same scripts as local development where practical.
When a hosted check fails, start with the matching local command below, then
compare any platform-specific setup in the workflow file.

.. list-table::
   :header-rows: 1

   * - Workflow
     - Trigger
     - What it checks
     - Local parity
   * - ``.github/workflows/tests.yml``
     - Pushes and pull requests for ``main``/``master``, ``v*`` tags, and
       manual dispatch
     - Ruff over ``tests/`` and ``scripts/``; Linux runs the full unit, GUI,
       golden, and release suite; macOS and Windows run unit plus release
       smoke checks after installing native GTK/PyGObject dependencies.
     - ``make dev-check`` for the fast gate, or ``make test-ci`` for the
       Linux full suite.
   * - ``.github/workflows/docs.yml``
     - Pushes and pull requests for ``main``/``master``, and manual dispatch
     - Installs GTK/PyGObject and doc tooling, verifies committed screenshots,
       builds Sphinx HTML, and uploads the ``astrology-docs`` artifact.
     - ``make test-screenshots`` followed by ``make docs``.
   * - ``.github/workflows/codeql.yml``
     - Pushes and pull requests for ``main``/``master`` plus a weekly Monday
       schedule
     - Initializes and analyzes the Python codebase with CodeQL using
       read-only repository permissions plus ``security-events: write``.
     - No exact local equivalent; keep generated files out of analysis and
       prefer small, reviewable security-model changes.
   * - ``.github/workflows/verify-release.yml``
     - ``v*`` tags
     - Fetches full tag history, imports ``.github/gpg/release-signing.asc``,
       and requires the release tag to be a signed annotated tag.
     - See :doc:`signing`; verify locally with ``git tag -v vX.Y.Z``.
   * - ``.github/workflows/packages.yml``
     - Manual dispatch and ``v*`` tags
     - Builds Debian, RPM, macOS, and Windows artifacts. On tag pushes it also
       creates the GitHub Release when missing and uploads package assets.
     - ``make package-deb``, ``make package-rpm``, ``make package-macos``,
       or ``make package-windows`` on the matching operating system.

Common CI pitfalls:

- Linux GUI and screenshot jobs need GTK 4, PyGObject, librsvg, ImageMagick,
  and Xvfb. If a local GUI check fails before tests run, install those system
  packages and rerun ``./install.sh`` so the virtual environment can see
  system site packages.
- ``make docs`` and ``make test-screenshots`` both require an existing
  ``.venv``. The docs workflow creates it with ``./install.sh`` before running
  ``scripts/build-docs.sh``.
- Windows tests run under MSYS2 UCRT64. ``scripts/install-test-deps.sh`` skips
  pip installation of the optional API stack there because FastAPI and related
  packages are installed by pacman in the workflow.
- Tag releases are split across ``verify-release.yml`` and ``packages.yml``:
  a ``v*`` tag must be signed and annotated before package artifacts are
  published. Follow ``PUBLISHING.md`` for the complete release checklist.

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
