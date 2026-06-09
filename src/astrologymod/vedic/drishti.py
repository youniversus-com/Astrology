# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Graha drishti (sign-based aspects)."""

from __future__ import annotations

from astrologymod.swiss import sign_index

# Offsets from graha sign (0-based): 4th house = +3, etc.
DRISHTI_OFFSETS: dict[int, tuple[int, ...]] = {
    4: (3, 6, 7),   # Mars: 4th, 7th, 8th
    5: (4, 6, 8),   # Jupiter: 5th, 7th, 9th
    6: (2, 6, 9),   # Saturn: 3rd, 7th, 10th
}


def drishti_target_signs(graha_id: int, graha_sign: int) -> set[int]:
    """Sign indices aspected by a graha (whole-sign)."""
    targets: set[int] = set()
    offsets = DRISHTI_OFFSETS.get(graha_id, (6,))
    for off in offsets:
        targets.add((graha_sign + off) % 12)
    return targets


def has_drishti(graha_id: int, from_sign: int, to_sign: int) -> bool:
    """True if ``from_sign`` planet aspects ``to_sign``."""
    return to_sign in drishti_target_signs(graha_id, from_sign)
