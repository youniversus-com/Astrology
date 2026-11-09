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

Chart SVG rendering contract
----------------------------

``AstrologyMainWindow`` owns the rendered chart viewport. It embeds
``AstrologyDrawSVG`` in a GTK scrolled window and registers
``draw.on_viewport_changed`` so resize events flow back into
``AstrologyInstance.set_chart_viewport(width, height)`` before the next
``makeSVG()`` call.

``AstrologyInstance.makeSVG()`` is the single writer for the active chart SVG:

- Desktop refreshes write ``g.cfg.tempfilename`` and load it with
  ``Rsvg.Handle.new_from_file()`` in ``AstrologyDrawSVG.setSVG()``.
- Print/export refreshes pass a ``printing`` size and write the print variant
  instead of using the live GTK allocation.
- Non-printing chart SVG uses the remembered viewport when both dimensions are
  at least 200 pixels; otherwise it falls back to the screen-size estimate.
- Vedic North/South Indian layouts bypass the Western XML template and render
  directly through ``astrologymod.vedic.chart_svg``. The ``wheel`` Vedic layout
  stays on the Western template and swaps the planet/house grids.

``AstrologyDrawSVG.draw_func()`` does not mutate chart data. It letterboxes the
current SVG into the GTK allocation with librsvg/Cairo, applies the chart zoom,
and debounces viewport notifications so resizing does not regenerate SVG on
every draw frame.

When adjusting glyph placement, keep the OpenAstro-style zodiac transform and
the ``zodiac-glyphs:openastro-org-s90`` marker in sync with
``tests/unit/test_zodiac_placement.py``. Broader rendering regressions are
covered by the GUI SVG smoke tests and the golden SVG digest tests.

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
