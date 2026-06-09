# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK drawing area that renders chart SVG via librsvg."""

from gi import require_version

require_version('Rsvg', '2.0')
require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk, Rsvg, cairo

from astrology_app.debug import dprint
import astrology_app.globals as g

class AstrologyDrawSVG(Gtk.DrawingArea):
	"""GTK 4 drawing area that renders an SVG chart via librsvg/Cairo."""

	def __init__(self):
		super().__init__()
		self.svg = None
		self._intrinsic_w = 0.0
		self._intrinsic_h = 0.0
		self._last_viewport = (0, 0)
		self.on_viewport_changed = None
		self._viewport_idle_id = 0
		self.set_draw_func(self.draw_func, None)

	def setSVG(self, svg):
		"""Load an SVG file; size follows the parent allocation (not intrinsic pixels)."""
		self.svg = Rsvg.Handle.new_from_file(svg)
		try:
			size = self.svg.get_intrinsic_size_in_pixels()
			self._intrinsic_w = float(size.out_width)
			self._intrinsic_h = float(size.out_height)
		except (AttributeError, TypeError, ValueError):
			self._intrinsic_w = float(self.svg.props.width)
			self._intrinsic_h = float(self.svg.props.height)
		dprint('AstrologyDrawSVG.setSVG file %s (%.0fx%.0f)' % (
			svg, self._intrinsic_w, self._intrinsic_h))

	def _schedule_viewport_notify(self, width, height):
		"""Debounce viewport callbacks so makeSVG is not run on every frame."""
		if self.on_viewport_changed is None:
			return
		last_w, last_h = self._last_viewport
		if abs(width - last_w) < 12 and abs(height - last_h) < 12:
			return
		self._last_viewport = (width, height)
		if self._viewport_idle_id:
			GLib.source_remove(self._viewport_idle_id)
		self._viewport_idle_id = GLib.idle_add(
			self._emit_viewport_changed, width, height, priority=GLib.PRIORITY_LOW)

	def _emit_viewport_changed(self, width, height):
		self._viewport_idle_id = 0
		if self.on_viewport_changed is not None:
			self.on_viewport_changed(int(width), int(height))
		return False

	def draw_func(self, widget, cr, width, height, data):
		"""GTK draw callback; paints the loaded SVG letterboxed in the allocation."""
		if self.svg is None or width < 1 or height < 1:
			return
		if self._intrinsic_w < 1 or self._intrinsic_h < 1:
			return
		self._schedule_viewport_notify(width, height)
		zoom = g.astrology_chart.zoom
		# Letterbox in the pane (SVG uses preserveAspectRatio xMidYMid + fixed viewBox).
		fit = min(width / self._intrinsic_w, height / self._intrinsic_h)
		scale = fit * zoom
		paint_w = self._intrinsic_w * scale
		paint_h = self._intrinsic_h * scale
		x_off = (width - paint_w) / 2.0
		y_off = (height - paint_h) / 2.0
		cr.translate(x_off, y_off)
		cr.scale(scale, scale)
		self.svg.render_cairo(cr)
