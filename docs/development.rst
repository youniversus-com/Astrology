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

Local input safety checks
-------------------------

Chart imports, geonames searches, settings dialogs, and export defaults accept
local user-controlled strings. Keep the checks close to the boundary that first
normalizes the value, then rely on parameterized database calls or GTK file
choosers for the final operation.

.. list-table::
   :header-rows: 1

   * - Code path
     - Constraint
     - Focused tests
   * - ``astrologymod.xml_io.parse_xml_file()``
     - Reads at most ``MAX_XML_BYTES`` plus one byte before parsing chart XML;
       oversized files raise ``ValueError`` before ``minidom`` sees the payload.
     - ``tests/unit/test_xml_io.py`` and
       ``tests/unit/importfile/test_security.py``
   * - ``astrologymod.validation.normalize_iso2()``
     - Accepts exactly two alphabetic country-code characters and returns upper
       case; invalid values return ``None`` and are omitted from geonames SQL
       filters.
     - ``tests/unit/test_validation.py``
   * - ``validate_color_key()``, ``validate_hex_color()``, and
       ``validate_label_key()``
     - Settings writes only use known identifier shapes and six-digit hex
       colors, while SQL values still travel as parameters.
     - ``tests/unit/test_validation.py``
   * - ``astrology_app.export_image.safe_chart_basename()``
     - Export dialog defaults replace path separators, Windows-reserved
       filename characters, and control characters with ``_``; empty names fall
       back to ``chart``.
     - ``tests/unit/test_export_image.py``

Examples:

.. code-block:: python

   normalize_iso2("nl") == "NL"
   normalize_iso2("NLD") is None
   validate_hex_color("#AABBCC")
   not validate_hex_color("red")
   safe_chart_basename("John/Doe: test") == "John_Doe_ test"

Common pitfalls:

- XML chart imports still surface parser errors such as ``ExpatError`` and
  schema-shape errors from the importers; do not convert those to successful
  partial imports without documenting the compatibility tradeoff.
- ``safe_chart_basename()`` only prepares a default filename. The selected
  destination still comes from GTK's save dialog and the export format branch
  appends or normalizes the extension.
- Add or update focused unit tests whenever widening a validator. The helpers
  intentionally reject unrecognized forms instead of silently preserving them.

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
