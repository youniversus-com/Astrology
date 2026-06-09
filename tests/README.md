# Tests

Pytest suite for YoUniverse Astrology. Configuration: `pytest.ini` at the repository root.

## Layout

| Directory | Marker | Description |
|-----------|--------|-------------|
| `unit/` | `unit` | Pure logic tests — no GTK window (default CI) |
| `unit/api/` | `unit` | FastAPI service and bootstrap tests |
| `gui/` | `gui`, `golden` | Headless GTK tests (requires Xvfb) |
| `release/` | `release` | Post-install smoke checks |
| `helpers/` | — | Shared loaders and SVG normalization |

## Running

```bash
make test-unit      # unit tests only
make test-gui       # GUI integration
make test-ci        # CI-equivalent suite
make test-all       # includes slow property tests
```

Or directly:

```bash
./scripts/run_unit_tests.sh
./scripts/run_tests.sh
```

## Markers

Defined in `pytest.ini`: `unit`, `gui`, `golden`, `release`, `slow`. Default `addopts` excludes `slow`.
