# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Map Gio.SimpleAction names to legacy handler keys used by import/export dialogs."""

# Gio menubar actions use kebab-case (e.g. export-png); handlers use camelCase (exportPNG).
EXPORT_KIND = {
    'export-xml': 'exportXML',
    'export-png': 'exportPNG',
    'export-svg': 'exportSVG',
    'export-jpg': 'exportJPG',
}

IMPORT_KIND = {
    'import-xml': 'importXML',
    'import-oroboros': 'importOroboros',
    'import-astrolog32': 'importAstrolog32',
    'import-skylendar': 'importSkylendar',
    'import-zet8': 'importZet8',
}


def resolve_export_kind(action_name, default='exportXML'):
    """Return handler key for :meth:`AstrologyMainWindow.doExport`."""
    if action_name is None:
        return default
    if isinstance(action_name, str) and action_name in EXPORT_KIND:
        return EXPORT_KIND[action_name]
    if isinstance(action_name, str) and action_name.startswith('export'):
        return action_name
    return default


def resolve_import_kind(action_name, default='importXML'):
    """Return handler key for :meth:`AstrologyMainWindow.doImport`."""
    if action_name is None:
        return default
    if isinstance(action_name, str) and action_name in IMPORT_KIND:
        return IMPORT_KIND[action_name]
    if isinstance(action_name, str) and action_name.startswith('import'):
        return action_name
    return default
