# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export chart SVG to PNG/JPEG via librsvg and Cairo (no ImageMagick)."""

import os
import re
import subprocess

from gi import require_version

require_version('Rsvg', '2.0')
require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf, Rsvg
import cairo


def safe_chart_basename(name):
    """Return a filesystem-safe base name for export defaults."""
    base = (name or 'chart').strip() or 'chart'
    return re.sub(r'[/\\<>:"|?*\x00-\x1f]', '_', base)


def _svg_dimensions(handle):
    try:
        size = handle.get_intrinsic_size_in_pixels()
        w = max(1, int(size.out_width))
        h = max(1, int(size.out_height))
    except (AttributeError, TypeError, ValueError):
        w, h = 1920, 1080
    return w, h


def export_svg_to_png(svg_path, png_path):
    """Render ``svg_path`` to a PNG file at ``png_path``."""
    handle = Rsvg.Handle.new_from_file(svg_path)
    width, height = _svg_dimensions(handle)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    handle.render_cairo(cr)
    surface.write_to_png(png_path)


def export_svg_to_jpeg(svg_path, jpg_path, quality=90):
    """Render ``svg_path`` to a JPEG file at ``jpg_path``."""
    png_path = jpg_path + '.export-tmp.png'
    try:
        export_svg_to_png(svg_path, png_path)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(png_path)
        pixbuf.savev(jpg_path, 'jpeg', ['quality'], [str(quality)])
    finally:
        if os.path.isfile(png_path):
            os.remove(png_path)


def export_svg_to_raster(svg_path, out_path):
    """Export SVG to PNG or JPEG based on ``out_path`` extension."""
    ext = os.path.splitext(out_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        export_svg_to_jpeg(svg_path, out_path)
    elif ext == '.png':
        export_svg_to_png(svg_path, out_path)
    else:
        raise ValueError('unsupported raster extension: %s' % ext)


def try_convert_cli(svg_path, out_path):
    """Fallback: ImageMagick ``convert`` if installed and explicitly allowed."""
    if os.environ.get('ASTROLOGY_ALLOW_IMAGEMAGICK', '').strip() not in ('1', 'yes', 'true'):
        return False
    proc = subprocess.run(
        ['convert', svg_path, out_path],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0 and os.path.isfile(out_path) and os.path.getsize(out_path) > 0
