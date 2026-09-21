HTTP API backend
================

YoUniverse Astrology includes an optional FastAPI backend in ``astrology_api``.
It exposes the same chart math, settings database, saved charts, and bundled
geonames atlas that the GTK desktop application uses. The backend is intended
for local development and trusted clients; it does not add authentication.

Running locally
---------------

Install the desktop application first so the virtual environment, bundled data,
and Swiss Ephemeris files are present:

.. code-block:: bash

   ./install.sh
   make api

``make api`` runs ``scripts/run-api.sh``. The script:

1. Requires an existing ``.venv``.
2. Installs ``requirements-api.txt``.
3. Reinstalls ``./src`` into the virtual environment.
4. Starts ``python -m astrology_api``.

By default the server binds to loopback on port ``8765``:

.. code-block:: bash

   ASTROLOGY_API_HOST=127.0.0.1 ASTROLOGY_API_PORT=8765 make api

OpenAPI documentation is served by FastAPI at ``/docs``. The application also
registers permissive CORS middleware (``allow_origins=['*']``), so do not expose
the development server directly to untrusted networks without adding deployment
controls outside this repository.

Runtime architecture
--------------------

FastAPI runs the synchronous route handlers in a worker thread pool, while the
legacy chart engine stores active configuration, database, and chart objects in
module globals. ``astrology_api.bootstrap.api_context()`` serializes API
operations with a process-wide lock and binds per-thread chart state before each
request.

That design keeps the API compatible with the desktop code, but it has
operational consequences:

- Requests are effectively serialized inside one process.
- Saved charts and settings use the same user data directory as the desktop app
  (``~/.config/com.youniverse.astrology/`` by default).
- Western SVG rendering requires GTK 4 and PyGObject. Headless JSON endpoints
  and Vedic SVG rendering do not require a GTK window.
- Run ``./install.sh`` first; otherwise bundled SQL data and ephemeris files may
  be missing.

Endpoint map
------------

.. list-table::
   :header-rows: 1

   * - Endpoint
     - Purpose
     - Notes
   * - ``GET /api/health``
     - Service version and GTK availability
     - Returns ``status``, ``version``, ``gtk_available``, and ``tradition``.
   * - ``POST /api/charts/data``
     - Structured ephemeris arrays
     - No SVG rendering; suitable for headless environments.
   * - ``POST /api/charts/compute``
     - Chart wheel SVG
     - ``tradition='western'`` requires GTK; ``tradition='vedic'`` returns Vedic SVG.
   * - ``POST /api/charts/vedic``
     - Vedic snapshot JSON plus SVG
     - Supports ``layout`` values ``north``, ``south``, and ``wheel``.
   * - ``GET /api/charts/saved``
     - List saved charts
     - Reads the user chart database.
   * - ``POST /api/charts/saved``
     - Save a chart
     - Accepts the ``SavedChart`` schema.
   * - ``DELETE /api/charts/saved/{chart_id}``
     - Delete a saved chart
     - Deletes by integer chart id.
   * - ``GET /api/settings``
     - Read chart settings
     - Returns astrocfg, planet/aspect settings, colors, and labels.
   * - ``PATCH /api/settings/astrocfg``
     - Update astrocfg keys
     - Accepts a JSON object of string keys and string values.
   * - ``POST /api/geonames/search``
     - Search the bundled geonames atlas
     - Uses the offline SQLite data installed with the application.

Request examples
----------------

The ``ChartEvent.hour`` field is a decimal UTC hour. Latitude and longitude are
validated by Pydantic as ``[-90, 90]`` and ``[-180, 180]`` respectively.

Health check:

.. code-block:: bash

   curl http://127.0.0.1:8765/api/health

Headless ephemeris data:

.. code-block:: bash

   curl -X POST http://127.0.0.1:8765/api/charts/data \
     -H 'Content-Type: application/json' \
     -d '{
       "event": {
         "name": "Example",
         "year": 1990,
         "month": 1,
         "day": 1,
         "hour": 12.0,
         "geolat": 48.8566,
         "geolon": 2.3522,
         "location": "Paris",
         "timezonestr": "UTC"
       }
     }'

Vedic SVG without western GTK rendering:

.. code-block:: bash

   curl -X POST http://127.0.0.1:8765/api/charts/compute \
     -H 'Content-Type: application/json' \
     -d '{
       "tradition": "vedic",
       "vedic_layout": "south",
       "event": {
         "name": "Example",
         "year": 1990,
         "month": 1,
         "day": 1,
         "hour": 12.0,
         "geolat": 48.8566,
         "geolon": 2.3522
       }
     }'

Maintaining API dependencies
----------------------------

The FastAPI runtime stack is optional and intentionally isolated from the GTK
desktop install. ``requirements-api.txt`` is the dependency file used by
``scripts/run-api.sh`` and, on non-MSYS2 platforms, by
``scripts/install-test-deps.sh``. The installable package also advertises an
``api`` extra in ``src/pyproject.toml``; review that metadata when raising
backend dependency bounds for published packages.

When updating FastAPI, Pydantic, or Uvicorn:

1. Check request and response contracts in ``astrology_api.schemas``. Pydantic
   validation currently enforces decimal UTC hours in ``[0, 24)``, coordinate
   ranges, chart image dimensions between 200 and 4000 pixels, non-empty
   geonames search queries, and geonames limits from 1 to 100.
2. Run the API-focused unit tests after installing the desktop app and test
   dependencies:

   .. code-block:: bash

      ./install.sh
      source .venv/bin/activate
      bash scripts/install-test-deps.sh
      python -m pytest tests/unit/api -m unit -q

3. Start the development server with ``make api`` and verify ``/api/health`` and
   ``/docs`` still load. Use ``POST /api/charts/data`` for a headless smoke test
   and ``POST /api/charts/compute`` to confirm western SVG rendering when GTK is
   available.
4. Preserve the threading model in ``astrology_api.bootstrap``. Synchronous
   FastAPI handlers run in a worker thread pool, while the legacy chart engine
   uses module globals, so requests must continue to pass through
   ``api_context()``.
5. On MSYS2 UCRT64, CI installs FastAPI through pacman instead of pip because
   some Python wheels are unavailable for the mingw runtime. Keep that platform
   path in mind when changing minimum versions.

Common failures
---------------

``Run ./install.sh first.``
  ``scripts/run-api.sh`` exits early when ``.venv`` does not exist.

``503`` from ``POST /api/charts/compute``
  Western chart SVG generation could not import GTK 4. Install the system GTK
  and PyGObject packages, or call ``/api/charts/data`` for JSON output or use
  ``tradition='vedic'``.

``422 Unprocessable Entity``
  The request body failed Pydantic validation. Check required ``event`` fields,
  decimal UTC ``hour``, coordinate ranges, and width/height limits.

Testing
-------

API unit tests live under ``tests/unit/api/`` and exercise service bootstrap
without starting an HTTP server:

.. code-block:: bash

   make test-unit
