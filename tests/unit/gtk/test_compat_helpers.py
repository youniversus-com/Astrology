# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK helper unit tests that do not need a running application window."""
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(scope='module')
def gtkcompat():
    from gi import require_version
    require_version('Gdk', '4.0')
    require_version('Gtk', '4.0')
    from astrologymod import gtkcompat as g4
    g4.ensure_display()
    return g4


def test_color_parse_valid(gtkcompat):
    rgba = gtkcompat.color_parse('#ff8040')
    assert rgba is not None
    assert rgba.red == pytest.approx(1.0, abs=0.01)
    assert rgba.green == pytest.approx(0.5, abs=0.05)


def test_color_parse_invalid(gtkcompat):
    assert gtkcompat.color_parse('not-a-color') is None


def test_new_label_accepts_label_kwarg(gtkcompat):
    from gi.repository import Gtk
    label = gtkcompat.new_label(label='Hello')
    assert isinstance(label, Gtk.Label)
    assert label.get_text() == 'Hello'


def test_new_button_label(gtkcompat):
    from gi.repository import Gtk
    btn = gtkcompat.new_button('OK')
    assert isinstance(btn, Gtk.Button)
    assert btn.get_label() == 'OK'


def test_grid_set_row_spacing_single_arg(gtkcompat):
    from gi.repository import Gtk
    grid = Gtk.Grid()
    gtkcompat.grid_set_row_spacing(grid, 8)
    assert grid.get_row_spacing() == 8


def test_entry_modify_base_no_op_on_gtk4(gtkcompat):
    from gi.repository import Gtk
    entry = Gtk.Entry()
    rgba = gtkcompat.color_parse('#336699')
    gtkcompat.entry_modify_base(entry, Gtk.StateFlags.NORMAL, rgba)
