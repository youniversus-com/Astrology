# Contributing

Thank you for helping improve **YoUniverse Astrology**. This document explains how to set up a development environment, run checks, and submit changes.

## Prerequisites

- **Python** 3.12+
- GTK 4, PyGObject, librsvg (see [README.md](README.md))
- Optional: `xvfb` for GUI tests, `debhelper` / `rpmbuild` for packaging

Dev dependencies (including optional HTTP API test deps) install via `requirements-dev.txt`.

## Quick start

```bash
git clone https://github.com/YOUR_ORG/astrology.git
cd astrology
./install.sh
source .venv/bin/activate
astrology
```

## Development workflow

1. Create a branch from `main`.
2. Make focused changes with tests where behavior changes.
3. Run the pre-push checklist:

```bash
make dev-check    # lint (tests/scripts) + unit tests
make test-ci      # full CI suite (needs Xvfb for GUI)
make docs         # build Sphinx API docs
```

4. Open a pull request using the provided template.

## Tests

| Command | Purpose |
|---------|---------|
| `make test-unit` | Fast logic tests |
| `make test-gui` | Headless GTK tests (requires `xvfb-run` or display) |
| `make test-ci` | Default CI gate |
| `make test-all` | Includes slow/benchmark tests |

See [tests/README.md](tests/README.md) for layout and markers.

## Documentation

- User-facing: [README.md](README.md), [docs/](docs/)
- API reference: generated from docstrings via Sphinx

```bash
make docs
# output: docs/_build/html/index.html
```

When adding public modules or functions, include a module docstring and Google-style docstrings on public APIs so `autodoc` can pick them up.

## Packaging

```bash
make package-deb
make package-rpm
make package
```

Ensure `src/debian/changelog` matches `src/VERSION` before building `.deb` packages.

## Code style

- Match surrounding file conventions (legacy code uses tabs in some modules).
- CI runs `ruff` on `tests/` and `scripts/`; expand coverage gradually.
- Type checking: `pyright` / `mypy` configs live in root `pyproject.toml`.

## Releases

1. Bump `src/VERSION` and `debian/changelog`.
2. Update `CHANGELOG.md`.
3. Create a **signed** tag and push (required by CI):

```bash
git tag -s vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z
```

See [docs/signing.rst](docs/signing.rst) for GPG setup.

## REUSE / SPDX

Source files include SPDX headers. After adding modules:

```bash
make spdx
make reuse-lint   # optional; pip install reuse
```

See `REUSE.toml` and `LICENSES/`.

## Community

- [GitHub Discussions](https://github.com/YOUR_ORG/astrology/discussions) — questions and ideas (enable in repo settings)
- [GitHub Sponsors](https://github.com/sponsors/YOUR_GITHUB_USERNAME) — configure in `.github/FUNDING.yml`

## Questions

Open a [discussion](https://github.com/YOUR_ORG/astrology/discussions) or [issue](https://github.com/YOUR_ORG/astrology/issues) before large architectural changes (ephemeris layer, UI rewrite, etc.).
