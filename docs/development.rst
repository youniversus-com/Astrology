Development
===========

Environment setup
-----------------

.. code-block:: bash

   ./install.sh
   source .venv/bin/activate
   pip install -r requirements-dev.txt

Dependency maintenance
----------------------

Python dependency updates are split by workflow so reviewers can validate only
the affected surface area:

.. list-table::
   :header-rows: 1

   * - File
     - Purpose
     - Review notes
   * - ``requirements.txt``
     - Base packages installed by ``./install.sh``
     - GTK 4, PyGObject, and Cairo are system packages, not pip packages.
   * - ``requirements-test.txt``
     - Unit, GUI, release, and property-test dependencies
     - Run at least ``make test-unit`` after test-framework changes.
   * - ``requirements-api.txt``
     - Optional FastAPI backend dependencies
     - Used by ``make api`` and included by ``requirements-dev.txt``.
   * - ``requirements-dev.txt``
     - Test, API, lint, type-check, and Sphinx tooling
     - Install explicitly after dependency bumps so pip failures are visible.
   * - ``src/pyproject.toml``
     - Installable package metadata, console scripts, and optional extras
     - Review API extras when API package minimums intentionally change.
   * - Root ``pyproject.toml``
     - Repository metadata plus Ruff, Pyright, and mypy configuration
     - Tool config changes should be validated with ``make dev-check``.

Dependabot runs monthly for pip files and GitHub Actions
(``.github/dependabot.yml``). The pip configuration groups common development
tools such as ``pytest*``, ``ruff``, ``sphinx``, ``pyright``, ``mypy``, and
``hypothesis`` into one PR; API runtime packages may arrive separately.

Validation examples:

.. code-block:: bash

   ./install.sh
   source .venv/bin/activate
   pip install -r requirements-dev.txt  # explicit check; install.sh is lenient
   make dev-check                       # lint + unit tests
   make docs                            # Sphinx after Sphinx/autodoc changes

For API runtime changes, start ``make api`` in one terminal and confirm the
health endpoint from another:

.. code-block:: bash

   curl http://127.0.0.1:8765/api/health

If ``./install.sh`` reports missing GTK or Rsvg imports, install the apt
packages it prints and rerun from outside any active virtual environment. The
project venv is created with ``--system-site-packages`` so Python can see those
system bindings.

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
