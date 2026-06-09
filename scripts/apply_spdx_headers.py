# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Add REUSE-style SPDX headers to project source files (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPYRIGHT = "YoUniverse Astrology contributors"
SPDX = (
    f"# SPDX-FileCopyrightText: 2026 {COPYRIGHT}\n"
    "# SPDX-License-Identifier: GPL-3.0-or-later\n"
)
SPDX_SHELL = (
    f"# SPDX-FileCopyrightText: 2026 {COPYRIGHT}\n"
    "# SPDX-License-Identifier: GPL-3.0-or-later\n"
)

GLOBS = [
    "src/astrologymod/*.py",
    "src/astrology_app/**/*.py",
    "src/setup.py",
    "scripts/*.sh",
    "tests/**/*.py",
    "tests/conftest.py",
]


def targets() -> list[Path]:
    found: list[Path] = []
    for pattern in GLOBS:
        found.extend(ROOT.glob(pattern))
    return sorted({p for p in found if p.is_file() and "debian/astrology" not in str(p)})


def insert_spdx(path: Path, dry_run: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    if "SPDX-License-Identifier" in text.split("\n", 5)[0:5]:
        return False

    lines = text.splitlines(keepends=True)
    insert_at = 0

    if lines and lines[0].startswith("#!"):
        insert_at = 1
        prefix = SPDX_SHELL if path.suffix in {".sh", ""} else SPDX
    else:
        prefix = SPDX

    new_text = "".join(lines[:insert_at]) + prefix + ("" if prefix.endswith("\n") else "\n") + "".join(lines[insert_at:])
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    changed = 0
    for path in targets():
        if insert_spdx(path, dry_run=dry_run):
            changed += 1
            print(f"{'would update' if dry_run else 'updated'}: {path.relative_to(ROOT)}")
    print(f"{'Would update' if dry_run else 'Updated'} {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
