# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from astrologymod.xml_io import MAX_XML_BYTES, parse_xml_bytes


def test_parse_xml_bytes_rejects_oversized():
    with pytest.raises(ValueError, match='exceeds'):
        parse_xml_bytes(b'<x/>' + b' ' * (MAX_XML_BYTES + 1))
