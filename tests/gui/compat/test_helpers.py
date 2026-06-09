# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK 4 compatibility helpers (headless display)."""
import pytest

pytestmark = [pytest.mark.gui, pytest.mark.usefixtures('gtk_env')]


def test_screen_size():
    from astrologymod import gtkcompat as g4
    w, h = g4.screen_size()
    w, h = g4.screen_size()
    assert w > 0 and h > 0


def test_grid_and_box():
    from gi.repository import Gtk
    from astrologymod import gtkcompat as g4
    grid = g4.new_table(2, 2)
    label = Gtk.Label(label='x')
    g4.grid_attach(grid, label, 0, 1, 0, 1)
    box = g4.new_vbox()
    g4.box_pack(box, grid, True, True, 0)
    assert box.get_first_child() is not None


def test_dialog_run_auto_cancel():
    from gi.repository import Gtk
    from astrologymod import gtkcompat as g4
    d = Gtk.Dialog()
    d.add_button('Cancel', Gtk.ResponseType.CANCEL)
    r = g4.dialog_run(d, test_auto_cancel=True)
    assert int(r) < 0  # any dialog close response
