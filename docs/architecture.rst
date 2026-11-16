Architecture
============

Overview
--------

YoUniverse Astrology is a GTK 4 desktop application with an optional FastAPI
backend. Runtime code is split across three Python packages:

``astrology_app``
  Application shell, chart state, SQLite databases, SVG generation, and the main window.

``astrologymod``
  Shared libraries: Swiss Ephemeris wrapper, timezone helpers, geonames lookup,
  chart file import, essential dignities, and GTK compatibility shims.

``astrology_api``
  Optional HTTP backend that exposes chart computation, settings, saved charts,
  and offline geonames search to trusted local clients.

Data flow
---------

1. **User input** (date, time, place) enters :class:`astrology_app.chart.AstrologyInstance`
   from the GTK window or arrives as Pydantic models in ``astrology_api.schemas``.
2. **Ephemeris** positions are computed by :class:`astrologymod.swiss.ephData` via ``pysweph``.
3. **Aspects** and chart metadata are derived in ``chart.py`` or converted to
   JSON by ``astrology_api.services.ephemeris_service``.
4. **SVG** wheel/table files are rendered from XML templates and displayed in GTK
   or returned by the HTTP API.

Configuration
-------------

Runtime settings and chart databases live in the user config directory
(``astrologymod.paths.user_data_dir``), backed by SQLite.

Persistence and settings databases
----------------------------------

The desktop application and optional HTTP API share the same local persistence
layer. ``AstrologyCfg`` creates the user data directory,
``~/.config/<USER_CONFIG_DIR>/`` (currently
``~/.config/com.youniverse.astrology/``), then resolves writable database,
temporary SVG, and local ephemeris override paths.

.. list-table::
   :header-rows: 1

   * - File
     - Owner
     - Purpose
   * - ``astrodb.sql``
     - ``astrology_app.db.AstrologySqlite``
     - Application settings: ``astrocfg`` key/value rows, recent chart history,
       planet/aspect visibility and colors, custom labels, and home-location
       defaults.
   * - ``peopledb.sql``
     - ``astrology_app.db.AstrologySqlite``
     - Saved natal chart records in ``event_natal``. Desktop database screens
       and ``GET/POST/DELETE /charts/saved`` read and update this file.
   * - ``geonames.sql`` and ``famous.sql``
     - Bundled data under ``share/astrology/data/``
     - Read by separate SQLite connections for offline location lookup and
       famous-chart import/search. They are resolved with packaged-data helpers,
       not created in the user config directory.

Initialization is intentionally self-healing. ``AstrologySqlite.__init__``
opens ``astrodb.sql`` and ``peopledb.sql``, creates missing tables, applies
schema additions for older installs, seeds default rows, commits, and closes the
connections. A stored ``astrocfg.version`` mismatch automatically enables the
schema check path. Developers can force that path from the launcher with
``--dbcheck``; ``--purge`` also enables it but replaces seeded settings rows,
so use it only when intentionally resetting defaults.

The API reuses the desktop persistence code through
``astrology_api.bootstrap.api_context()``. FastAPI sync endpoints may run in
different worker threads, while ``astrology_app`` still relies on module
globals, so the API keeps thread-local ``AstrologyCfg``/``AstrologySqlite``/
``AstrologyInstance`` objects and serializes request handling with an
``_api_lock``. Endpoint code should enter ``api_context()`` before touching
``g.cfg``, ``g.db``, or ``g.astrology_chart``.

When adding settings or saved-chart fields:

1. Update the table definition and migration/default block in
   ``astrology_app.db``.
2. Keep Pydantic models and routers aligned when the field is exposed through
   ``astrology_api``.
3. Add or update isolated-HOME tests under ``tests/unit/db/`` so migrations do
   not depend on a developer's real ``~/.config`` directory.

Bundled assets
--------------

Packaged under ``share/astrology/`` at install time:

- ``data/geonames.sql``, ``data/famous.sql``
- ``locale/*/LC_MESSAGES/astrology.mo``
- ``swisseph/*.se1`` ephemeris files
- SVG/XML chart templates and aspect icons

Extension points
----------------

- **Import formats:** ``astrologymod.importfile``
- **House/planet settings:** SQLite tables via ``astrology_app.db``
- **Branding:** ``astrologymod.branding`` (app id, homepage, config dir name)

Diagrams
--------

For **Mermaid** component, sequence, and class diagrams, see ``ARCHITECTURE.md`` in the
repository root (renders on GitHub). A publishing checklist lives in ``PUBLISHING.md``.
Third-party licenses are summarized in ``THIRD_PARTY_NOTICES.md``.
