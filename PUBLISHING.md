# Publishing checklist

Use this before the first public GitHub push and for each release.

## Repository hygiene

- [ ] **Do not commit:** `.venv/`, `.venv-check/`, `docs/_build/`, `dist/`, `build/rpm/`, `build/macos-venv/`, `build/windows-venv/`, `build/pyinstaller/`
- [ ] **Do not commit:** `src/debian/astrology/` (debhelper staging tree)
- [ ] **Do not commit:** legacy `openastro.org_*.deb` or other local `.deb` artifacts
- [ ] **Optional:** keep `swisseph/ephe/` out of git (vendor cache; script repopulates it)
- [ ] Run `git status` and confirm only source, docs, tests, and minimal bundled data are staged

## Legal & attribution

- [ ] `LICENSE` (GPL-3.0-or-later) present
- [ ] `LICENSES/` + `REUSE.toml` (SPDX/REUSE compliance)
- [ ] `make spdx` run after adding new source files
- [ ] Optional: `pip install reuse && make reuse-lint`
- [ ] `THIRD_PARTY_NOTICES.md` reviewed (Swiss Ephemeris, geonames)
- [ ] `src/debian/copyright` matches maintainer branding
- [ ] Geonames redistribution acceptable under [their license](https://www.geonames.org/export/)

## Branding

- [ ] `src/astrologymod/branding.py` — set `GITHUB_REPO`; verify `APP_NAME`, `APP_ID`, `USER_CONFIG_DIR`
- [ ] Replace placeholders `YOUR_ORG`, `YOUR_GITHUB_USERNAME`, `YOUR_NAME` in docs, README, and `.github/`
- [ ] `AUTHORS.md` — add maintainer name(s)
- [ ] `.github/CODEOWNERS` and `.github/FUNDING.yml` — uncomment/customize if used
- [ ] README badges URL matches your GitHub repo
- [ ] `debian/changelog` maintainer updated

## Quality gates

```bash
./install.sh
make dev-check      # lint + unit tests
make test-ci        # full CI (needs xvfb for GUI)
make docs           # Sphinx HTML
make spdx           # refresh REUSE headers if needed
make package-deb    # optional local package smoke test
# Native desktop (on target OS only):
# make package-macos   # macOS + Homebrew
# make package-windows # MSYS2 UCRT64
```

## GitHub setup

- [ ] Create repository `github.com/YOUR_ORG/astrology` (or your org)
- [ ] Enable **Issues**
- [ ] Enable **Discussions** (Settings → General → Features) — templates in `.github/DISCUSSION_TEMPLATE/`
- [ ] Enable **Sponsors** if using `.github/FUNDING.yml`
- [ ] Enable **Private vulnerability reporting** (Settings → Security)
- [ ] Add repository topics: `astrology`, `gtk4`, `python`, `swiss-ephemeris`, `desktop-app`, `gpl-3`
- [ ] Set **About** description and link to Read the Docs
- [ ] Optional: enable **Code scanning** (CodeQL workflow in `.github/workflows/codeql.yml`)
- [ ] Push `main` branch

## Read the Docs

- [ ] Import project at https://readthedocs.org (uses `.readthedocs.yaml`)
- [ ] Enable PR preview builds
- [ ] Update README docs badge with your RTD project slug (see `docs/hosting.rst`)

## Branch protection & signing

- [ ] Require CI checks on `main` before merge
- [ ] Optional: require signed commits on `main`
- [ ] Configure GPG signing locally (see `docs/signing.rst`)
- [ ] Release tags **must** be signed: `git tag -s vX.Y.Z -m "..."` (CI enforces via `verify-release.yml`)

## First release

1. Confirm `src/VERSION`, root `pyproject.toml`, and `debian/changelog` match
2. Update `CHANGELOG.md`
3. Create **signed** tag and push:

```bash
git tag -s v1.1.60 -m "Release 1.1.60"
git push origin v1.1.60
```

4. GitHub Actions: verify signature, tests, docs, `.deb`, `.rpm`, GitHub Release
5. Attach `.deb` / `.rpm` from workflow artifacts to the Release if not automated
6. Build and attach macOS `.app` / Windows zip from a machine on each platform (`make package-macos` / `make package-windows`; see `docs/packaging.rst`)
7. Add screenshots to README (`docs/screenshots/`)

## Ongoing

- Dependabot PRs (`.github/dependabot.yml`) — review dev dependency updates
- Keep CI green on `main`
- Document user-visible changes in `CHANGELOG.md`
- Use **Discussions** for Q&A; **Issues** for bugs and feature tracking
