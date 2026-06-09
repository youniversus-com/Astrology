# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.62] - 2026-06-09

### Added

- Automated GitHub Release publishing: Linux, macOS, and Windows packages attach to signed tags.

### Changed

- Debug logging redacts user-identifying data before stderr output.
- Release CI creates the GitHub Release and uploads distribution packages in one workflow.

## [1.1.60] - 2026-06-08

### Added

- GitHub open-source publishing infrastructure: CI workflows, community templates, REUSE/SPDX compliance, and contributor documentation.

### Changed

- Version bump and packaging metadata aligned for first public release.

## [1.1.59] - 2026-05-26

### Added

- GTK 4 desktop application with natal, transit, synastry, composite, solar, and progression charts.
- Swiss Ephemeris calculations via `pysweph` with bundled DE441 ephemeris data.
- Geonames offline atlas, chart import/export, and multi-language UI.
- Debian and RPM packaging scripts; GitHub Actions CI for tests and `.deb` builds.

### Changed

- Rebranded from legacy OpenAstro.org lineage to YoUniverse Astrology.
- Modernized timezone handling (`zoneinfo`), ephemeris wrapper, and project packaging.

[1.1.62]: https://github.com/youniversus-com/Astrology/releases/tag/v1.1.62
[1.1.60]: https://github.com/youniversus-com/Astrology/releases/tag/v1.1.60
[1.1.59]: https://github.com/YOUR_ORG/astrology/releases/tag/v1.1.59
