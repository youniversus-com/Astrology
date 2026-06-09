# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Import parsers — malformed or hostile inputs."""
import pytest
from xml.parsers.expat import ExpatError

from astrologymod import importfile

pytestmark = pytest.mark.unit


def test_get_yac_invalid_xml(tmp_path):
    path = tmp_path / 'bad.yac'
    path.write_text('not xml at all', encoding='utf-8')
    with pytest.raises(ExpatError):
        importfile.getYAC(str(path))


def test_get_yac_wrong_root_tag(tmp_path):
    path = tmp_path / 'empty.yac'
    path.write_text('<?xml version="1.0"?><root></root>', encoding='utf-8')
    assert importfile.getYAC(str(path)) == []


def test_get_yac_missing_fields(tmp_path):
    path = tmp_path / 'partial.yac'
    path.write_text(
        '<?xml version="1.0"?><astrologychart><name>X</name></astrologychart>',
        encoding='utf-8',
    )
    with pytest.raises(IndexError):
        importfile.getYAC(str(path))


def test_get_astrolog32_empty_file(tmp_path):
    path = tmp_path / 'empty.dat'
    path.write_text('', encoding='utf-8')
    charts = importfile.getAstrolog32(str(path))
    assert isinstance(charts, list)
    assert len(charts) >= 1
