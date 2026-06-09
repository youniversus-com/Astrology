# Documentation screenshots

PNG captures for the README and Sphinx docs (`getting-started.rst`).

| File | Source |
|------|--------|
| `natal-wheel-default.png` | Natal chart SVG (fixed Amsterdam 1990-06-15 chart) |
| `transit-view.png` | Transit overlay SVG |
| `main-window.png` | Main `Gtk.ApplicationWindow` |
| `event-editor.png` | Edit Event Details dialog |
| `settings-planets.png` | Planets & Angles settings dialog |

## Regenerate

```bash
./install.sh
make update-ephemeris      # if src/swisseph/*.se1 are missing
make update-screenshots
make test-screenshots
```

Uses headless GTK on Xvfb (`tests/gui/screenshots/test_doc_screenshots.py`).
Chart data matches `tests/gui/screenshots/chart_data.py` (same as golden tests).

Commit updated PNGs when UI or default theme changes.
