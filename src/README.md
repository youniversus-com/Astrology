# Source tree

Python packages and bundled runtime data live under `src/`. This follows the [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) recommended for installable Python projects.

## Packages

| Package | Path | Role |
|---------|------|------|
| **astrologymod** | `astrologymod/` | Core chart math: Swiss Ephemeris, Vedic (Jyotish), import/export, geonames, validation. No UI. |
| **astrology_app** | `astrology_app/` | GTK 4 desktop application: windows, menus, SQLite persistence, SVG rendering. |
| **astrology_api** | `astrology_api/` | Optional FastAPI HTTP backend (chart services over HTTP). |

## Bundled data

| Path | Installed to | Contents |
|------|--------------|----------|
| `data/` | `share/astrology/data/` | Geonames SQL, famous charts, Vedic yogas JSON |
| `icons/` | `share/astrology/icons/` | App icon and aspect glyphs |
| `locale/` | `share/astrology/locale/` | gettext translations (`.mo`) |
| `swisseph/` | `share/swisseph/` | JPL DE441 ephemeris `.se1` files |
| `*.xml` | `share/astrology/` | SVG chart templates |

## Entry points

- `run_astrology.py` + `astrology` script — desktop launcher (`astrology` console command)
- `astrology_api/` — API server (`astrology-api` console command)

## Install

From the repository root:

```bash
./install.sh
# or: pip install -e ./src
```

Packaging metadata: `pyproject.toml` and `setup.py` in this directory.
