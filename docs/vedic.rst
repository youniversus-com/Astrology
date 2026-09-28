Vedic (Jyotish) astrology
=========================

Enable **Settings -> Configuration -> Tradition: Vedic (Jyotish)**. Switching
from Western mode applies a Vedic preset: sidereal zodiac, Lahiri ayanamsa,
whole-sign houses, North Indian D1 layout, Vimshottari dashas, and visibility
for the seven classical grahas plus Rahu/Ketu. Leaving Vedic mode restores the
Western planet visibility defaults.

Chart layouts
-------------

``Vedic Chart Layout`` controls how the main window is rendered:

``North Indian``
   Replaces the Western wheel with a diamond-style D1 chart. House 1 is anchored
   at the top and each house includes the rashi name, sign lord, and graha
   abbreviations with degree, retrograde, and combustion markers.

``South Indian``
   Replaces the Western wheel with a fixed-sign South Indian D1 chart. Lagna is
   marked in the sign cell and the chart center summarizes panchanga details.

``Western Wheel``
   Keeps the normal sidereal wheel but changes tables and aspect lines to Vedic
   data. Graha drishti replaces the Western aspect grid.

Transit charts always use the Western wheel so the natal/transit rings remain
available, even when Vedic mode is enabled.

Vedic report workflow
---------------------

Open **Tables -> Vedic Report** (also available under **Chart Type**) after
entering the chart date, time, and location. The dialog rebuilds the chart SVG
first, then reads the in-memory ``VedicChartSnapshot`` produced from final
ephemeris longitudes.

The report includes:

- lagna, ayanamsa, panchanga, graha placements, nakshatra/pada, house, drishti,
  retrograde, and combustion status;
- the selected primary dasha system plus the other supported systems
  (Vimshottari, Yogini, and Ashtottari);
- Vimshottari antardashas for the first mahadasha;
- detected yogas, simplified Shadbala totals, simplified Ashtakavarga bindus,
  and birth-day muhurta slots;
- chart tabs for D1 and D9, plus D10 when ``vedic_varga_display`` includes
  ``D10``.

The Shadbala and Ashtakavarga values are intentionally simplified scoring
helpers, not full traditional calculations. The source labels these paths as
``simplified``/``stub`` and tests currently verify structural output rather than
authoritative astrological equivalence.

Configuration keys
------------------

Vedic preferences live in the ``astrocfg`` SQLite table:

.. list-table::
   :header-rows: 1

   * - Key
     - Values
     - Effect
   * - ``tradition``
     - ``western`` or ``vedic``
     - Master switch for Vedic-specific settings and rendering.
   * - ``vedic_ayanamsa``
     - ``LAHIRI``, ``RAMAN``, ``KRISHNAMURTI``, ``SURYASIDDHANTA``,
       ``SURYASIDDHANTA_MSUN``, ``ARYABHATA``, ``SS_CITRA``, ``TRUE_CITRA``,
       ``YUKTESHWAR``, ``JN_BHASIN``
     - Copied to ``siderealmode`` while Vedic mode is active.
   * - ``vedic_houses``
     - ``whole_sign`` or ``equal``
     - Maps to Swiss Ephemeris house system ``W`` or ``A``.
   * - ``vedic_chart_layout``
     - ``north``, ``south``, or ``wheel``
     - Selects North Indian, South Indian, or Western-wheel rendering.
   * - ``vedic_dasha_system``
     - ``vimshottari``, ``yogini``, or ``ashtottari``
     - Chooses the primary dasha section in the report.
   * - ``vedic_varga_display``
     - Comma-separated varga codes such as ``D1,D9,D10``
     - Controls report varga rows and whether the dialog adds a D10 chart tab.

If older user databases do not have these keys, startup inserts defaults in
``astrology_app.db.AstrologySqlite``.

Developer touchpoints
---------------------

- ``astrologymod.vedic.preset.effective_astrocfg()`` applies sidereal and house
  overrides before ephemeris calculation.
- ``astrology_app.chart.AstrologyInstance._refresh_vedic_snapshot()`` builds a
  ``VedicChartSnapshot`` after planet and house longitudes are finalized.
- ``astrologymod.vedic.snapshot.build_snapshot()`` aggregates graha placement,
  panchanga, dashas, vargas, yogas, strengths, Ashtakavarga, and muhurta.
- ``astrologymod.vedic.chart_svg`` renders North/South Indian SVG charts and the
  centered main-window canvas wrapper.
- ``astrology_app.ui.vedic_panel.show_vedic_panel()`` formats the report dialog
  and chart tabs.

Focused tests live under ``tests/unit/vedic/``. For Vedic-only changes, run:

.. code-block:: bash

   pytest tests/unit/vedic
