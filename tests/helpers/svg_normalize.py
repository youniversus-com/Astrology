# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize SVG chart output for golden-file comparison."""
import hashlib
import re


def normalize_svg(text: str) -> str:
    """Strip volatile whitespace/comments and normalize titles for stable diffs."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<title[^>]*>.*?</title>', '<title>NORMALIZED</title>', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def svg_digest(text: str) -> str:
    return hashlib.sha256(normalize_svg(text).encode('utf-8')).hexdigest()
