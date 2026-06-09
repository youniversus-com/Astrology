# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture GTK widgets and chart SVG as PNG for documentation."""

from __future__ import annotations

import io
import math
import os
import time

import cairo
from gi import require_version

require_version('Gdk', '4.0')
require_version('Gtk', '4.0')
require_version('Gsk', '4.0')
require_version('Graphene', '1.0')
from gi.repository import Gdk, GLib, Graphene, Gsk, Gtk

from astrology_app.export_image import export_svg_to_png


def pump_main_loop(ms=100):
    """Run pending GLib main-loop iterations for ``ms`` milliseconds."""
    ctx = GLib.MainContext.default()
    end = time.time() + ms / 1000.0
    while time.time() < end:
        while ctx.pending():
            ctx.iteration(False)


def _snapshot_node(widget):
    snapshot = Gtk.Snapshot()
    Gtk.Widget.do_snapshot(widget, snapshot)
    return snapshot.to_node()


def _capture_size(widget, node, padding=8):
    """Return PNG width/height large enough for the snapshot bounds."""
    bounds = node.get_bounds()
    width = int(math.ceil(bounds.origin.x + bounds.size.width)) + padding
    height = int(math.ceil(bounds.origin.y + bounds.size.height)) + padding
    width = max(width, widget.get_width(), 1)
    height = max(height, widget.get_height(), 1)
    return width, height


def _prepare_widget(widget, ms=120):
    if not widget.get_realized():
        widget.realize()
    widget.queue_resize()
    pump_main_loop(ms)


def _walk_widgets(widget, callback):
    callback(widget)
    child = widget.get_first_child()
    while child is not None:
        _walk_widgets(child, callback)
        child = child.get_next_sibling()


def _expand_scrolled_windows(widget):
    """Show full scrolled content instead of a clipped viewport."""

    def maybe_expand(w):
        if isinstance(w, Gtk.ScrolledWindow):
            w.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

    _walk_widgets(widget, maybe_expand)


def _preferred_window_size(window, padding=24):
    """Minimum window size to fit non-scrolling dialog content."""
    width = height = 0
    child = window.get_first_child()
    if child is not None:
        vsize = child.measure(Gtk.Orientation.VERTICAL, -1)
        height = max(height, vsize.natural, vsize.minimum)
        hsize = child.measure(Gtk.Orientation.HORIZONTAL, -1)
        width = max(width, hsize.natural, hsize.minimum)
    return max(width + padding, 1), max(height + padding, 1)


def prepare_dialog_screenshot(window, ms=150):
    """Resize a dialog so scrolled areas and action buttons fit in one capture."""
    _expand_scrolled_windows(window)
    width, height = _preferred_window_size(window)
    window.set_default_size(width, height)
    window.set_size_request(width, height)
    _prepare_widget(window, ms)


def _ensure_window_size(widget, width, height):
    """Grow a Gtk.Window before snapshot when content exceeds allocation."""
    if not isinstance(widget, Gtk.Window):
        return
    width = max(width, 1)
    height = max(height, 1)
    widget.set_default_size(width, height)
    widget.set_size_request(width, height)
    _prepare_widget(widget, 100)


def _render_node_to_texture(node, width, height):
    display = Gdk.Display.get_default()
    renderer = Gsk.CairoRenderer()
    renderer.realize_for_display(display)
    try:
        viewport = Graphene.Rect()
        viewport.init(0, 0, width, height)
        return renderer.render_texture(node, viewport)
    finally:
        renderer.unrealize()


def _texture_to_png(texture, png_path, background=(1.0, 1.0, 1.0)):
    width = texture.get_width()
    height = texture.get_height()
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    cr.set_source_rgb(*background)
    cr.paint()
    tex_surface = cairo.ImageSurface.create_from_png(
        io.BytesIO(texture.save_to_png_bytes().get_data())
    )
    cr.set_source_surface(tex_surface, 0, 0)
    cr.paint()
    os.makedirs(os.path.dirname(png_path) or '.', exist_ok=True)
    surface.write_to_png(png_path)


def save_widget_as_png(widget, png_path, background=(1.0, 1.0, 1.0)):
    """Render a realized GTK widget to a PNG file with an opaque background."""
    _prepare_widget(widget)

    node = _snapshot_node(widget)
    width, height = _capture_size(widget, node)
    if width > widget.get_width() or height > widget.get_height():
        _ensure_window_size(widget, width, height)
        node = _snapshot_node(widget)
        width, height = _capture_size(widget, node)

    texture = _render_node_to_texture(node, width, height)
    _texture_to_png(texture, png_path, background)


def save_chart_svg_as_png(svg_path, png_path):
    """Rasterize a chart SVG via librsvg (same path as the export menu)."""
    os.makedirs(os.path.dirname(png_path) or '.', exist_ok=True)
    export_svg_to_png(svg_path, png_path)


def assert_png(path, min_bytes=1024):
    assert os.path.isfile(path), 'missing screenshot: %s' % path
    size = os.path.getsize(path)
    assert size >= min_bytes, 'screenshot too small (%d B): %s' % (size, path)
