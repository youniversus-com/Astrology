# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Menu action name resolution for import/export dialogs."""

from astrology_app.menu_actions import resolve_export_kind, resolve_import_kind


def test_resolve_export_kind_from_gio_action():
    assert resolve_export_kind('export-png') == 'exportPNG'
    assert resolve_export_kind('export-svg') == 'exportSVG'
    assert resolve_export_kind('export-jpg') == 'exportJPG'
    assert resolve_export_kind('export-xml') == 'exportXML'


def test_resolve_export_kind_legacy_and_default():
    assert resolve_export_kind('exportPNG') == 'exportPNG'
    assert resolve_export_kind(None) == 'exportXML'


def test_resolve_import_kind_from_gio_action():
    assert resolve_import_kind('import-oroboros') == 'importOroboros'
    assert resolve_import_kind('import-astrolog32') == 'importAstrolog32'
    assert resolve_import_kind('import-skylendar') == 'importSkylendar'
    assert resolve_import_kind('import-zet8') == 'importZet8'
    assert resolve_import_kind('import-xml') == 'importXML'


def test_resolve_import_kind_default():
    assert resolve_import_kind(None) == 'importXML'
