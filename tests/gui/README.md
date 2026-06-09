# GUI integration tests

Headless tests that boot `AstrologyApplication` and `AstrologyMainWindow` on **Xvfb**.

Requires: `sudo apt install xvfb`, `ASTROLOGY_TEST=1`, `DISPLAY=:99`.

## Subfolders

| Folder | Focus |
|--------|--------|
| `chart/` | `makeSVG`, chart types, zoom; optional benchmark (`slow`) |
| `compat/` | `gtkcompat` with a real Gdk display |
| `menus/` | Menu handlers and file dialogs |
| `settings/` | Settings dialogs |
| `render/` | librsvg load of generated SVG |

Golden snapshot tests live in `tests/gui/golden/` and use the same fixtures (`app_context`).

Run: `make test-gui`
