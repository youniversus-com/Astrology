# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK 4 application menu built with Gio.Menu and Gio.SimpleAction.

Replaces the legacy ``Gtk.UIManager`` + XML UI description. ``MainMenu`` registers
actions on the ``Gtk.ApplicationWindow`` and builds a menubar model consumed by
``Gtk.Application.set_menubar``.
"""

from astrologymod.branding import PROJECT_HOMEPAGE
from gi.repository import Gio, GLib, Gtk


class MainMenu:
    """Menubar and action wiring for the primary Astrology window.

    Attributes:
        window: ``Gtk.ApplicationWindow`` that owns actions (``win.*`` targets).
        main: ``AstrologyMainWindow`` instance receiving menu callbacks.
    """

    def __init__(self, window, main_win):
        """Attach menu controller to a window and main window handler.

        Args:
            window: ``Gtk.ApplicationWindow`` for action registration.
            main_win: ``AstrologyMainWindow`` instance implementing menu handlers.
        """
        self.window = window
        self.main = main_win
        self._static_registered = False
        self._dynamic_actions = []

    def _simple(self, name, callback):
        """Register a parameterless ``Gio.SimpleAction`` on the window."""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', lambda a, p, n=name, cb=callback: cb(n))
        self.window.add_action(action)

    def _remove_dynamic_actions(self):
        """Remove history and quick-open actions before rebuilding the menu."""
        for name in self._dynamic_actions:
            try:
                self.window.remove_action(name)
            except GLib.Error:
                pass
        self._dynamic_actions.clear()

    def register_static_actions(self):
        """Register all fixed menu actions once (idempotent)."""
        if self._static_registered:
            return
        self._static_registered = True
        m = self.main
        actions = [
            ('quit', m.quit_cb),
            ('new-chart', m.eventDataNew),
            ('import-xml', m.doImport),
            ('export-xml', m.doExport),
            ('export-png', m.doExport),
            ('export-svg', m.doExport),
            ('export-jpg', m.doExport),
            ('export-pdf', m.doPrint),
            ('import-oroboros', m.doImport),
            ('import-astrolog32', m.doImport),
            ('import-skylendar', m.doImport),
            ('import-zet8', m.doImport),
            ('edit-event', m.eventData),
            ('open-database', m.openDatabase),
            ('open-database-famous', m.openDatabaseFamous),
            ('settings-planets', m.settingsPlanets),
            ('settings-aspects', m.settingsAspects),
            ('settings-colors', m.settingsColors),
            ('settings-labels', m.settingsLabel),
            ('settings-location', m.settingsLocation),
            ('settings-configuration', m.settingsConfiguration),
            ('chart-radix', m.specialRadix),
            ('chart-transit', m.specialTransit),
            ('chart-synastry', lambda w: m.openDatabaseSelect(m._menu_tr('Select for Synastry'), 'Synastry')),
            ('chart-composite', lambda w: m.openDatabaseSelect(m._menu_tr('Select for Composite'), 'Composite')),
            ('chart-combine', lambda w: m.openDatabaseSelect(m._menu_tr('Select for Combine'), 'Combine')),
            ('chart-solar', m.specialSolar),
            ('chart-secondary', m.specialSecondaryProgression),
            ('table-monthly', m.tableMonthlyTimeline),
            ('table-cusp', m.tableCuspAspects),
            ('vedic-report', m.showVedicReport),
            ('export-db', m.extraExportDB),
            ('import-db', m.extraImportDB),
            ('about-info', m.aboutInfo),
            ('about-support', lambda w: __import__('webbrowser').open_new(
                PROJECT_HOMEPAGE)),
        ]
        for name, cb in actions:
            self._simple(name, cb)

        zoom = Gio.SimpleAction.new_stateful(
            'zoom', GLib.VariantType.new('i'), GLib.Variant.new_int32(1))
        zoom.connect('change-state', self._on_zoom_change)
        self.window.add_action(zoom)

    def _on_zoom_change(self, action, value):
        """Handle zoom level change from the View menu."""
        action.set_state(value)
        self.main.set_zoom_from_menu(value.get_int32())

    def _register_history(self, i, chart_list):
        """Register a dynamic action for a history menu entry."""
        name = 'history-%d' % i
        action = Gio.SimpleAction.new(name, None)
        action.connect(
            'activate', lambda a, p, lst=chart_list: self.main.updateChartList(None, lst))
        self.window.add_action(action)
        self._dynamic_actions.append(name)

    def _register_quickopen(self, i, row):
        """Register a dynamic action for a quick-open database row."""
        name = 'quickopen-%d' % i
        action = Gio.SimpleAction.new(name, None)
        action.connect(
            'activate', lambda a, p, r=row: self.main.updateChartList(None, r))
        self.window.add_action(action)
        self._dynamic_actions.append(name)

    def build_menu_model(self, history_items, db_items, _gettext):
        """Build the full ``Gio.Menu`` tree for the application menubar.

        Args:
            history_items: Sequence of ``(label, chart_list)`` for recent charts.
            db_items: Rows from the people database for quick-open submenu.
            _gettext: Translation callable (typically ``gettext.gettext``).

        Returns:
            Gio.Menu: Root menu model.
        """
        _ = _gettext
        menu = Gio.Menu()

        file_menu = Gio.Menu()
        file_menu.append(_('New Chart'), 'win.new-chart')
        file_menu.append(_('Open Chart'), 'win.import-xml')
        file_menu.append(_('Save Chart…'), 'win.export-xml')
        imp = Gio.Menu()
        imp.append(_('Oroboros (*.xml)'), 'win.import-oroboros')
        imp.append(_('Astrolog (*.dat)'), 'win.import-astrolog32')
        imp.append(_('Skylendar (*.skif)'), 'win.import-skylendar')
        imp.append(_('Zet8 Dbase (*.zbs)'), 'win.import-zet8')
        file_menu.append_submenu(_('Import'), imp)
        exp = Gio.Menu()
        exp.append(_('PNG Image'), 'win.export-png')
        exp.append(_('SVG Image'), 'win.export-svg')
        exp.append(_('JPG Image'), 'win.export-jpg')
        exp.append(_('PDF File'), 'win.export-pdf')
        file_menu.append_submenu(_('Export'), exp)
        hist = Gio.Menu()
        for i, (label, chart_list) in enumerate(history_items[:10]):
            if chart_list:
                self._register_history(i, chart_list)
                hist.append(label, 'win.history-%d' % i)
            else:
                hist.append(label, 'win.quit')
        file_menu.append_submenu(_('History'), hist)
        file_menu.append(_('Quit!'), 'win.quit')
        menu.append_submenu(_('Chart'), file_menu)

        event_menu = Gio.Menu()
        event_menu.append(_('Edit Event'), 'win.edit-event')
        event_menu.append(_('Open Database'), 'win.open-database')
        qdb = Gio.Menu()
        for i, row in enumerate(db_items):
            self._register_quickopen(i, row)
            qdb.append(row['name'], 'win.quickopen-%d' % i)
        event_menu.append_submenu(_('Quick Open Database'), qdb)
        event_menu.append(_('Open Famous People Database'), 'win.open-database-famous')
        menu.append_submenu(_('Event'), event_menu)

        settings_menu = Gio.Menu()
        settings_menu.append(_('Planets & Angles'), 'win.settings-planets')
        settings_menu.append(_('Aspects'), 'win.settings-aspects')
        settings_menu.append(_('Colors'), 'win.settings-colors')
        settings_menu.append(_('Labels'), 'win.settings-labels')
        settings_menu.append(_('Set Home Location'), 'win.settings-location')
        settings_menu.append(_('Configuration'), 'win.settings-configuration')
        menu.append_submenu(_('Settings'), settings_menu)

        chart_menu = Gio.Menu()
        chart_menu.append(_('Radix Chart'), 'win.chart-radix')
        chart_menu.append(_('Transit Chart'), 'win.chart-transit')
        chart_menu.append(_('Synastry Chart'), 'win.chart-synastry')
        chart_menu.append(_('Composite Chart'), 'win.chart-composite')
        chart_menu.append(_('Combine Chart'), 'win.chart-combine')
        chart_menu.append(_('Solar Return'), 'win.chart-solar')
        chart_menu.append(_('Secondary Progressions'), 'win.chart-secondary')
        chart_menu.append(_('Vedic Report'), 'win.vedic-report')
        menu.append_submenu(_('Chart Type'), chart_menu)

        tables_menu = Gio.Menu()
        tables_menu.append(_('Monthly Timeline'), 'win.table-monthly')
        tables_menu.append(_('Cusp Aspects'), 'win.table-cusp')
        tables_menu.append(_('Vedic Report'), 'win.vedic-report')
        menu.append_submenu(_('Tables'), tables_menu)

        zoom_menu = Gio.Menu()
        zoom_menu.append('80%', 'win.zoom(0)')
        zoom_menu.append('100%', 'win.zoom(1)')
        zoom_menu.append('150%', 'win.zoom(2)')
        zoom_menu.append('200%', 'win.zoom(3)')
        menu.append_submenu(_('Zoom'), zoom_menu)

        extra_menu = Gio.Menu()
        extra_menu.append(_('Export Database'), 'win.export-db')
        extra_menu.append(_('Import Database'), 'win.import-db')
        menu.append_submenu(_('Extra'), extra_menu)

        about_menu = Gio.Menu()
        about_menu.append(_('Info'), 'win.about-info')
        about_menu.append(_('Support'), 'win.about-support')
        menu.append_submenu(_('About'), about_menu)

        return menu

    def apply(self, history, db_rows, _gettext):
        """Rebuild menubar: static actions, dynamic entries, and attach to app.

        Args:
            history: History list for File → History submenu.
            db_rows: Database rows for Event → Quick Open.
            _gettext: Translation callable.
        """
        self.register_static_actions()
        self._remove_dynamic_actions()
        model = self.build_menu_model(history, db_rows, _gettext)
        app = self.window.get_application()
        if app is not None:
            app.set_menubar(model)
        self.window.set_show_menubar(True)
