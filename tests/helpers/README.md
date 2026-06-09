# Test helpers

Shared utilities used across test layers.

| Module | Purpose |
|--------|---------|
| `loader.py` | Load `astrology_app.application` and sync runtime globals for tests |
| `svg_normalize.py` | Normalize chart SVG for golden-file comparison |

Not collected as tests — import from tests via `from helpers.svg_normalize import ...` (tests root is on `sys.path`).
