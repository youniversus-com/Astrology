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

Chart rendering pipeline
------------------------

``AstrologyMainWindow.updateChart()`` is the desktop refresh boundary. It records
the current drawing-area allocation with ``AstrologyInstance.set_chart_viewport()``,
calls ``AstrologyInstance.makeSVG()``, loads the returned SVG path into
``AstrologyDrawSVG.setSVG()``, then queues a GTK redraw. ``AstrologyDrawSVG``
renders the loaded file through librsvg and Cairo, letterboxing it inside the GTK
allocation and debouncing resize callbacks so ``makeSVG()`` is not rerun for
every frame.

Western charts use ``src/astrology-svg.xml`` as a ``string.Template`` source.
``makeSVG()`` builds the substitution dictionary from the active chart state,
SQLite settings, aspect rules, colors, and Swiss Ephemeris output, then writes to
``g.cfg.tempfilename``. Print/export paths pass a ``printing`` dictionary and
write ``g.cfg.tempfilenameprint`` instead. The template keeps a fixed
``772.2 x 546.0`` viewBox; runtime ``width`` and ``height`` come from the drawing
pane or print context. Text inserted into the SVG is escaped with
``_escape_svg_text()``, and SVG symbol references use ``svgSafeHref()``.

Vedic rendering branches before the Western template is filled. When
``astrocfg['tradition']`` is ``'vedic'``, a Vedic snapshot is available, the
layout is ``'north'`` or ``'south'``, and the chart is not a transit chart,
``makeSVG()`` writes a full-canvas D1 chart through
``astrologymod.vedic.chart_svg.render_vedic_chart_svg_on_canvas()``. The
``'wheel'`` Vedic layout and transit charts continue to use the Western wheel,
with Vedic graha drishti lines and Vedic planet/house grids.

Exports reuse the same generated SVG files:

- ``Export -> SVG`` copies ``g.cfg.tempfilename`` after a fresh ``makeSVG()``.
- ``Export -> PNG/JPEG`` rasterizes that SVG with ``astrology_app.export_image``
  through librsvg and Cairo. ImageMagick is only a fallback when
  ``ASTROLOGY_ALLOW_IMAGEMAGICK`` is explicitly enabled.
- ``Export chart as PDF`` calls ``makeSVG(printing=...)`` from the GTK print
  operation and renders ``g.cfg.tempfilenameprint`` at print resolution.
- Table/report windows use ``astrology_app.ui.chart_table_io.write_table_svg()``
  with ``src/astrology-svg-table.xml`` and separate screen/print temp files.

When changing this path, keep generated SVG deterministic enough for snapshot
tests. Run ``make test-gui`` for the GTK/librsvg path and update
``tests/gui/golden/baselines/`` with ``make update-golden`` only when an
intentional visual change alters the normalized chart SVG. Vedic canvas changes
are covered by ``tests/unit/vedic/test_chart_svg.py`` as part of ``make test-unit``.

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
