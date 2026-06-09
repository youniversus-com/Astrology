# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tempfile

import pytest

from astrology_app.export_image import safe_chart_basename


def test_safe_chart_basename_strips_unsafe_chars():
    assert safe_chart_basename('John/Doe: test') == 'John_Doe_ test'
    assert safe_chart_basename('') == 'chart'
    assert safe_chart_basename('  ') == 'chart'


@pytest.mark.skipif(
    os.environ.get('ASTROLOGY_TEST') == '1',
    reason='needs display for librsvg raster export',
)
def test_export_svg_to_png_writes_file():
    from astrology_app.export_image import export_svg_to_png

    svg = (
        '<?xml version="1.0"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="white"/>'
        '</svg>'
    )
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = os.path.join(tmp, 't.svg')
        png_path = os.path.join(tmp, 't.png')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        export_svg_to_png(svg_path, png_path)
        assert os.path.isfile(png_path)
        assert os.path.getsize(png_path) > 0
