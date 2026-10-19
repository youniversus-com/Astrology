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

Location and timezone normalization
-----------------------------------

Chart calculations use UTC internally, but most user workflows start from a
local civil time and a place name. The GTK home-location dialog
(``astrology_app.ui.location_dialog``) resolves a city either through the online
``geoname.search()`` helper or the offline picker backed by the bundled
geonames SQLite data. The selected location, coordinates, country code, and
IANA timezone name are persisted through ``AstrologySqlite.setSettingsLocation()``
as ``home_*`` keys in ``astrocfg``.

``AstrologyInstance`` keeps two timezone fields for compatibility:

- ``timezonestr`` stores an IANA zone such as ``Europe/Amsterdam``. New local
  datetimes are localized with ``astrologymod.timezone_utils.localize_naive()``
  and converted to naive UTC with ``naive_utc()`` before ephemeris calculation.
- ``timezone`` stores the legacy numeric UTC offset in decimal hours. It is used
  to derive display-only ``*_loc`` fields in ``utcToLocal()`` and to format chart
  labels with ``decTzStr()``.

Import paths preserve the best timezone source available. Native ``.yac`` files
round-trip both fields; Oroboros and Skylendar imports use the timezone ID from
the file; Astrolog32 imports fall back to the nearest row in the system
``zone.tab`` via ``astrologymod.zonetab.nearest_tz()``. The legacy import paths
also look up the nearest bundled geonames row so saved charts retain
``geonameid`` and ``timezonestr`` metadata.

For API clients, ``ChartEvent.hour`` is already a decimal UTC hour. Send
``timezonestr`` as descriptive metadata unless the client has converted a local
time before calling the API.

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
