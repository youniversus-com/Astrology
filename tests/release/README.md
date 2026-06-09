# Release smoke tests

Verify the **installed** project layout after `./install.sh`:

- `.venv/bin/python` exists
- `astrology` module loads and exposes `VERSION`
- `swisseph` is importable in the venv

Run automatically in the full pipeline via `scripts/run_release_tests.sh` or `make test-release`.

Marked `release`.
