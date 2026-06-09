# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gtk picker widgets for geonames UI."""

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from astrologymod import gtkcompat as g4


def test_code_dropdown_rows_and_selection():
    dropdown = g4.new_code_dropdown()
    g4.picker_set_rows(dropdown, [('Europe', 'EU'), ('Asia', 'AS')], 1)
    assert g4.picker_selected_row(dropdown) == ('Asia', 'AS')
    g4.picker_set_selected(dropdown, 0)
    assert g4.picker_selected_row(dropdown) == ('Europe', 'EU')


def test_combo_bind_text_column_attaches_renderer():
    combo = Gtk.ComboBox()
    g4.combo_bind_text_column(combo, 0)
    assert len(combo.get_cells()) == 1
