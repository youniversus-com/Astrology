Vedic (Jyotish) astrology
=========================

Enable **Settings → Configuration → Tradition: Vedic (Jyotish)**. The app uses
sidereal longitudes (Lahiri or other ayanamsa), whole-sign houses by default,
and seven grahas plus Rahu/Ketu.

**Main chart**

- **North Indian** or **South Indian** layout: the primary window shows a
  divisional D1 chart (not the Western wheel).
- **Western wheel** layout: sidereal wheel with graha drishti lines, Vedic
  planet/house tables, and filtered grahas.
- **Transit** charts always use the Western wheel (transit ring) even in
  Vedic mode.

**Tables → Vedic Report** (also under **Chart Type**) opens the full analysis:
panchanga, sixteen vargas, Vimshottari / Yogini / Ashtottari dashas, yogas,
simplified Shadbala and Ashtakavarga, muhurta slots, and chart tabs.

Configuration keys (``astrocfg``):

- ``tradition``: ``western`` or ``vedic``
- ``vedic_ayanamsa``, ``vedic_houses``, ``vedic_chart_layout``, ``vedic_dasha_system``
- ``vedic_varga_display``: comma-separated varga codes for the report

Implementation lives in ``astrologymod.vedic``.
