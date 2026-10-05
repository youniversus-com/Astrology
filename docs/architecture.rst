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

Bundled assets
--------------

Packaged under ``share/astrology/`` at install time:

- ``data/geonames.sql``, ``data/famous.sql``
- ``locale/*/LC_MESSAGES/astrology.mo``
- ``swisseph/*.se1`` ephemeris files
- SVG/XML chart templates and aspect icons

Location lookup and timezones
-----------------------------

Location selection is shared by the GTK app and the optional HTTP API:

- The bundled ``data/geonames.sql`` atlas is the default source of places.
  ``astrology_app.config.AstrologyCfg`` resolves it, and
  ``astrology_app.db.AstrologySqlite.gquery()`` opens short-lived SQLite
  connections for read-only atlas queries.
- ``astrology_app.ui.geonames_picker.attach_offline_picker()`` builds the
  continent, country, province, and city drop-downs used by the home-location
  and event-editor dialogs. ``GeonamesHandlersMixin`` cascades selections,
  supports text search such as ``London, GB``, and writes the selected
  latitude, longitude, country code, geoname id, and IANA timezone into the
  chart state.
- ``AstrologySqlite.gnearest()`` maps imported or manually entered coordinates
  to the nearest bundled city within about half a degree of latitude/longitude.
  If no nearby row is found, the returned country, admin, geoname id, and
  timezone fields are ``None``; callers should preserve existing chart data or
  ask the user to choose a location.
- ``astrology_api.services.geonames_service.search_geonames()`` exposes the
  same atlas through ``POST /api/geonames/search``. Requests require a non-empty
  ``query``, may pass an ISO-2 ``country`` filter, and clamp ``limit`` to
  ``1..100`` via ``GeonameSearchRequest``.

Online lookup is opt-in. ``MainWindow.checkInternetConnection()`` only enables
geonames.org when the ``use_geonames.org`` astrocfg value is ``"1"`` and an
HTTPS probe to ``https://api.geonames.org/`` succeeds. The settings dialog then
calls ``astrologymod.geoname.search()``, which searches populated places with
``maxRows=1`` and resolves the timezone with a second geonames.org request. The
username defaults to ``astrology`` and can be overridden with
``ASTROLOGY_GEONAMES_USER`` or the ``geonames_username`` astrocfg key.

Timezone handling stores both the legacy numeric UTC offset and the IANA
``timezonestr``. New code should prefer ``astrologymod.timezone_utils`` for
``zoneinfo`` conversion and only derive numeric offsets for legacy chart fields.
``astrologymod.zonetab`` remains a fallback helper for nearest-timezone lookups
from the system ``/usr/share/zoneinfo/zone.tab`` file.

Useful checks while changing this area:

.. code-block:: bash

   make test-unit
   pytest tests/unit/test_geonames_picker.py tests/unit/zonetab/test_zonetab.py
   pytest tests/unit/api/test_api_services.py

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
