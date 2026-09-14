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

Chart import and export flow
----------------------------

Chart file actions are owned by the GTK shell and update the shared chart
instance directly:

1. ``astrologymod.appmenu.AppMenuManager`` registers ``win.import-*`` and
   ``win.export-*`` actions. ``astrology_app.menu_actions`` translates the Gio
   action names into the legacy handler keys used by the main window.
2. ``astrology_app.ui.main_window.AstrologyMainWindow.doImport()`` opens a GTK
   file chooser, filters by the selected format, and dispatches to
   ``AstrologyInstance.importOAC()``, ``importOroboros()``,
   ``importSkylendar()``, ``importAstrolog32()``, or ``importZet8()``.
3. Native ``.yac`` files and most third-party chart formats are parsed by
   ``astrologymod.importfile``. XML inputs go through
   ``astrologymod.xml_io.parse_xml_file()``, which caps reads at 10 MiB before
   handing data to ``xml.dom.minidom``.
4. Imported single-chart formats replace the current ``AstrologyInstance``
   fields and then the main window redraws. Third-party imports normalize local
   time to UTC and look up the nearest bundled geonames row for timezone and
   geonames metadata.
5. Zet8 ``.zbs`` imports are database imports: ``AstrologyInstance.importZet8()``
   parses every row and calls ``AstrologySqlite.importZet8()`` to append records
   to the natal chart database with duplicate-name suffixes.

Exports follow a separate rendering path. ``doExport()`` regenerates the chart
SVG with ``AstrologyInstance.makeSVG()``; native ``.yac`` output is written by
``exportOAC()``, SVG export copies the generated SVG, and PNG/JPEG export uses
``astrology_app.export_image`` to render through librsvg and Cairo. PDF export
uses ``AstrologyMainWindow.doPrint()`` and GTK's print operation rather than the
raster helper. Full database export/import lives under the **Extra** menu:
``extraExportDB()`` copies the people database, while ``extraImportDB()`` backs
it up and merges a compatible ``event_natal`` schema.

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
