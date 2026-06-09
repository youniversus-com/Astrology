# Third-party notices

This application bundles or depends on the following third-party components.

## Swiss Ephemeris / pysweph

- **Use:** planetary positions, houses, nodes, lunar phase
- **License:** GPL (see [Swiss Ephemeris](https://www.astro.com/swisseph/))
- **Python bindings:** [pysweph](https://pypi.org/project/pysweph/) (installed at runtime, bundled in Debian/RPM packages)
- **Data files:** `src/swisseph/*.se1`, `fixstars.cat` (JPL DE441 set; refreshed via `scripts/update_ephemeris_de441.sh`)

## Geonames database

- **File:** `src/data/geonames.sql` (~30 MB, derived from geonames.org cities dump)
- **License:** [Geonames terms of use](https://www.geonames.org/export/)
- **Attribution:** geonames.org contributors

## Famous people database

- **File:** `src/data/famous.sql`
- **Origin:** shipped with the application; verify provenance before redistribution if you fork

## GTK / GNOME stack

- **Components:** GTK 4, PyGObject, librsvg, Cairo (system packages)
- **License:** LGPL-2.1+ (typical for GNOME libraries; see your distribution)

## Translation files

- **Location:** `src/locale/*/LC_MESSAGES/astrology.mo`
- **Origin:** community translations from the application lineage; update `.pot` with `xgettext` when adding strings

## Optional vendor ephemeris cache

- **Path:** `swisseph/ephe/` (local mirror, **not required** in git — created by `scripts/update_ephemeris_de441.sh`)
- **Purpose:** avoid re-downloading `.se1` files during development
