# Unit tests

Fast tests that do **not** start the GTK main window. Safe to run without Xvfb.

## Subfolders

| Folder | Focus |
|--------|--------|
| `ephemeris/` | Known-date Sun/Moon longitudes via Swiss Ephemeris |
| `db/` | `AstrologySqlite` settings and `astrocfg` |
| `importfile/` | Valid chart files and malformed XML |
| `property/` | Hypothesis round-trips (`slow` marker) |
| `zonetab/` | Timezone coordinate parsing |
| `dignities/` | Essential dignities |
| `swisseph/` | Binding import smoke |
| `unit/astrology/` | `decHour` / timezone helpers |
| `gtk/` | `astrologymod.gtkcompat` without a display |
| `i18n/` | gettext / `_()` smoke |
| `smoke/` | Module import and `py_compile` |

Run: `pytest tests/unit/ -m unit` or `make test-unit` (also runs `tests/release/` in the full pipeline).
