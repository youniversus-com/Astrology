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

Western aspect rendering
------------------------

Western chart aspects are rendered as part of
``astrology_app.chart.AstrologyInstance.makeSVG()``. The renderer reads aspect
definitions from ``settings_aspect`` and planet visibility flags from
``settings_planet`` through ``astrology_app.db``:

- ``visible`` controls whether an aspect line is drawn inside the wheel.
- ``visible_grid`` controls whether the aspect symbol appears in the grid.
- ``orb`` is applied symmetrically around the configured aspect degree for radix
  charts.
- ``visible_aspect_line`` and ``visible_aspect_grid`` on each planet decide
  whether that body participates in lines and grid cells.

``makeAspects()`` draws radix aspect lines, and ``makeAspectGrid()`` writes the
radix grid into ``src/astrology-svg.xml``. Transit charts use
``makeAspectsTransit()`` and ``makeAspectTransitGrid()`` instead; their orb
window is intentionally narrower and depends on whether a personal planet is
involved. Vedic charts bypass the Western aspect grid and call
``makeVedicDrishti()`` for graha drishti overlays.

``makePatterns()`` is a legacy hook reserved in the SVG template for major
Western aspect patterns. It currently scans conjunctions, oppositions, squares,
trines, quincunxes, and sextiles for stelliums, grand trines, grand crosses,
T-squares, and yods, but the generated overlay is not emitted because the method
returns an empty string. Treat pattern display as disabled until that return
path and the corresponding golden SVG baseline are updated.

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
