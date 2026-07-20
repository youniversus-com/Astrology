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

Debug logging and redaction
---------------------------

Runtime diagnostics should go through ``astrology_app.debug.dprint()`` instead of
writing directly to stderr. Debug output is opt-in: it is emitted only when the
application sees ``--debug`` in ``sys.argv`` or when ``astrology_app.constants.DEBUG``
is set to ``True`` for a local development build.

Before each line is written, ``dprint()`` redacts user-identifying values. This is
especially important because debug calls appear in chart conversion, database,
file export/import, and geonames lookup paths.

.. list-table::
   :header-rows: 1

   * - Input kind
     - Replacement
   * - Home-directory paths, such as ``/home/alice/charts/natal.svg``
     - ``<user-data>``
   * - Other common absolute runtime paths under ``/tmp``, ``/var``, ``/run``,
       ``/mnt``, ``/opt``, ``/usr``, ``/Users``, or ``/private``
     - ``<path>``
   * - IANA timezone names, such as ``Europe/Amsterdam``
     - ``<timezone>``
   * - Date or datetime strings in ``YYYY-MM-DD`` form
     - ``<datetime>``
   * - Explicit latitude/longitude labels and coordinate tuples
     - ``<coord>`` or ``<coords>``
   * - Place or person names after known debug prefixes, such as
       ``known home location:``, ``loc=``, or ``saved to database:``
     - ``<place>``

Low-precision astronomical values are intentionally preserved. For example,
``localToSolar: first sun 285.123456`` remains useful for chart math debugging
and is covered by the redaction unit tests.

When adding a new debug call:

1. Keep the message narrow and avoid embedding complete objects.
2. Prefer stable prefixes when logging locations or saved records so the
   redactor can match them.
3. Add or update ``tests/unit/test_debug_redaction.py`` when a new sensitive
   message shape is introduced.
4. If changing the redaction helper itself, keep the CodeQL barrier model in
   ``.github/codeql/extensions/astrology-python-models/models/`` aligned so
   clear-text logging analysis still treats sanitized output correctly.

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
