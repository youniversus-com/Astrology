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

## Automated security scanning

GitHub Actions runs Python CodeQL through `.github/workflows/codeql.yml` on
pushes and pull requests targeting `main` or `master`, plus a weekly Monday
schedule at 06:00 UTC. The workflow checks out the repository, initializes
CodeQL for Python, and uploads alerts with `security-events: write`.

The repository also carries a local CodeQL data-extension pack at
`.github/codeql/extensions/astrology-python-models/`. Its current model marks
`astrology_app.debug._redact_sensitive()` as a barrier for the
`clear-text-logging-sensitive-data` query, matching the runtime contract of
`astrology_app.debug.dprint()`.

Debug output is opt-in (`--debug` or a local `DEBUG = True` build) and should
route through `dprint()` instead of direct stderr writes. Before a line is
written, the helper redacts home paths, common runtime paths, coordinates,
timezones, datetimes, and known place/person-name message shapes. Keep
`tests/unit/test_debug_redaction.py` aligned with any new sensitive debug
message shape.

When triaging a CodeQL alert:

1. Confirm the reported source, sink, and path against the current code.
2. If the output is legitimately sanitized, verify that the call goes through
   `dprint()`, the redaction behavior is covered by unit tests, and the CodeQL
   model still points at the sanitizer.
3. If a new kind of sensitive value can reach logs, update the redactor and add
   a regression test before closing the alert.
4. Do not paste raw user logs, locations, chart file paths, or birth/event data
   into public issues while investigating.

The CodeQL model is intentionally narrow: it only describes
`_redact_sensitive()` for clear-text logging analysis. Add separate tests and a
separate model entry before treating any other sanitizer as equivalent.
