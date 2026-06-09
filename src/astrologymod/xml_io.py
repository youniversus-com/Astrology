# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded, safe XML parsing for chart import and geonames responses."""

from xml.dom.minidom import parseString

MAX_XML_BYTES = 10 * 1024 * 1024


def parse_xml_bytes(data: bytes):
    """Parse XML bytes with a size cap (mitigates decompression/entity bombs)."""
    if len(data) > MAX_XML_BYTES:
        raise ValueError('XML payload exceeds %d bytes' % MAX_XML_BYTES)
    text = data.decode('utf-8', errors='replace')
    return parseString(text)


def parse_xml_file(path: str, max_bytes: int = MAX_XML_BYTES):
    """Read a file and parse XML with a size cap."""
    with open(path, 'rb') as f:
        data = f.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError('XML file exceeds %d bytes: %s' % (max_bytes, path))
    return parse_xml_bytes(data)
