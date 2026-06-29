Development
===========

Environment setup
-----------------

.. code-block:: bash

   ./install.sh
   source .venv/bin/activate
   pip install -r requirements-dev.txt

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
