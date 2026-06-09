# Unit tests — GTK compatibility layer

Smoke tests for `astrologymod/gtkcompat.py` that need Gdk/Gtk types but **do not** start `AstrologyApplication` or `AstrologyMainWindow`.

## Why a subfolder?

Keeps “tiny GTK API checks” separate from:

- **`tests/unit/test_*.py`** — pure Python / Swiss Ephemeris / import parsers
- **`tests/gui/compat/`** — same helpers exercised **with** a display session and dialog run loop

## Run

Included in `make test-unit` (marker `unit`).

```bash
pytest tests/unit/gtk/
```
