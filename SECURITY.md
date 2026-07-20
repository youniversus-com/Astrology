# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| latest release on `main` | yes |
| older releases | best effort |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive reports.

Instead, contact the repository maintainer via GitHub **Private vulnerability reporting** if enabled on the repository, or the contact method listed in the repository **About** section.

Include:

- Description of the issue and impact
- Steps to reproduce
- Affected version or commit
- Suggested fix (if any)

We aim to acknowledge reports within 7 days and provide a fix or mitigation plan as soon as practical.

## Scope

In scope: this application, bundled scripts, and packaging. Out of scope: third-party services (geonames.org API), upstream Swiss Ephemeris, and GTK/PyGObject themselves—though we will track relevant upstream advisories.

## Debug output

Debug logging is opt-in (`--debug` or a local `DEBUG = True` build) and routes through `astrology_app.debug.dprint()`, which redacts home paths, common runtime paths, coordinates, timezones, datetimes, and known place/person-name message shapes before writing to stderr. Treat debug logs as potentially sensitive in reports anyway, and see `docs/development.rst` for the maintained redaction contract and test expectations.
