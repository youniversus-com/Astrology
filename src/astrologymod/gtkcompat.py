# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK 4 compatibility helpers for Astrology.

This module centralizes API differences between GTK 3 (original Astrology) and
GTK 4 (current port). Call sites use these helpers instead of deprecated
constructors such as positional ``Gtk.Label(text)`` or ``Gtk.Dialog(title=...)``.

Longer term, migrate ``Gtk.ComboBox``/``ListStore`` to ``Gtk.DropDown`` and
``Gtk.TreeView`` to ``Gtk.ListView``/``ColumnView`` as GTK 4 deprecations are
removed upstream.

Docstring style follows `Google Python Style Guide`_ conventions.

.. _Google Python Style Guide: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
"""

import os

from gi import require_version

require_version('Gdk', '4.0')
require_version('Gtk', '4.0')
from gi.repository import Gdk, Gio, GLib, Gtk


class AttachOptions:
    """GTK 3 ``Gtk.AttachOptions`` stand-in for grid attach expand flags."""

    SHRINK = 0
    EXPAND = 1
    FILL = 2


if not hasattr(Gtk, 'AttachOptions'):
    Gtk.AttachOptions = AttachOptions

# Mnemonic button labels (GTK 3 stock identifiers; leading '_' marks accelerator).
STOCK_OK = '_OK'
STOCK_CANCEL = '_Cancel'
STOCK_OPEN = '_Open'
STOCK_SAVE = '_Save'
STOCK_SAVE_AS = '_Save As'
STOCK_QUIT = '_Quit'
STOCK_NEW = '_New'
STOCK_EDIT = '_Edit'
STOCK_DELETE = '_Delete'
STOCK_CLOSE = '_Close'
STOCK_APPLY = '_Apply'
STOCK_HELP = '_Help'
STOCK_INFO = '_Info'
STOCK_HOME = '_Home'
STOCK_PREFERENCES = '_Preferences'
STOCK_SELECT_COLOR = '_Color'
STOCK_HARDDISK = '_Database'
STOCK_ZOOM_100 = '_100%'


def ensure_display():
    """Open the default GDK display or return None.

    Tries ``DISPLAY``, then ``WAYLAND_DISPLAY``. Call before ``Gtk.Application.run``.

    Returns:
        Gdk.Display | None: Active display, or None if no GUI session is available.
    """
    if not Gtk.is_initialized():
        Gtk.init()
    display = Gdk.Display.get_default()
    if display is not None:
        return display
    for var in ('DISPLAY', 'WAYLAND_DISPLAY'):
        name = os.environ.get(var, '').strip()
        if not name:
            continue
        try:
            display = Gdk.Display.open(name)
        except (TypeError, GLib.Error):
            display = None
        if display is not None:
            return display
    return None


def screen_size():
    """Return primary monitor width and height in pixels.

    Returns:
        tuple[int, int]: ``(width, height)``. Falls back to 1920×1080 when no
        display is available (e.g. headless CI without Xvfb).
    """
    display = Gdk.Display.get_default()
    if display is None and os.environ.get('DISPLAY'):
        display = Gdk.Display.open(os.environ['DISPLAY'])
    if display is None:
        return 1920, 1080
    monitors = display.get_monitors()
    monitor = monitors.get_item(0) if monitors.get_n_items() else None
    if monitor is None:
        return 1920, 1080
    geom = monitor.get_geometry()
    return geom.width, geom.height


def new_vbox(spacing=0):
    """Create a vertical ``Gtk.Box``.

    Args:
        spacing: Pixels between children.

    Returns:
        Gtk.Box: Vertical box.
    """
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)


def new_hbox(spacing=0):
    """Create a horizontal ``Gtk.Box``.

    Args:
        spacing: Pixels between children.

    Returns:
        Gtk.Box: Horizontal box.
    """
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)


def new_label(text='', **kwargs):
    """Create a ``Gtk.Label`` (GTK 4 requires keyword ``label=``).

    Args:
        text: Label text.
        **kwargs: Forwarded to ``Gtk.Label`` after ``label`` is applied.

    Returns:
        Gtk.Label: New label widget.
    """
    if 'label' in kwargs:
        text = kwargs.pop('label')
    return Gtk.Label(label=text, **kwargs)


def new_button(label='', **kwargs):
    """Create a ``Gtk.Button`` (GTK 4 requires keyword ``label=``).

    Args:
        label: Button text.
        **kwargs: Forwarded to ``Gtk.Button``.

    Returns:
        Gtk.Button: New button widget.
    """
    if 'label' in kwargs:
        label = kwargs.pop('label')
    return Gtk.Button(label=label, **kwargs)


def button_set_can_default(button, can_default=True):
    """Set default activation on a button when supported by the toolkit."""
    if hasattr(button, 'set_can_default'):
        button.set_can_default(can_default)


def button_grab_default(button):
    """Grab default keyboard focus on a button when supported."""
    if hasattr(button, 'grab_default'):
        button.grab_default()


def new_dialog(transient_for=None, title=None):
    """Create a ``Gtk.Dialog`` using GTK 4 property setters.

    Args:
        transient_for: Parent window, or None.
        title: Window title string.

    Returns:
        Gtk.Dialog: Empty dialog; add content and buttons separately.
    """
    dialog = Gtk.Dialog()
    if transient_for is not None:
        dialog.set_transient_for(transient_for)
    if title:
        dialog.set_title(title)
    dialog.set_modal(True)
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)
    dialog._oa_content = content
    dialog.get_content_area().append(content)
    return dialog


def combo_set_wrap_width(combo, width):
    """Set combo popup wrap width on GTK 3 ``Gtk.ComboBox`` only (no-op on GTK 4)."""
    if hasattr(combo, 'set_wrap_width'):
        combo.set_wrap_width(width)


def new_table(rows, cols, homogeneous=False):
    """Create a ``Gtk.Grid`` (replacement for GTK 3 ``Gtk.Table``).

    Args:
        rows: Ignored; kept for API compatibility with legacy call sites.
        cols: Ignored.
        homogeneous: Ignored.

    Returns:
        Gtk.Grid: Empty grid with zero row/column spacing.
    """
    grid = Gtk.Grid()
    grid.set_row_spacing(0)
    grid.set_column_spacing(0)
    return grid


def grid_attach(grid, child, left, right, top, bottom, xoptions=None, yoptions=None,
                xpadding=0, ypadding=0):
    """Attach a child to a grid using GTK 3 Table-style edge indices.

    Args:
        grid: Target ``Gtk.Grid``.
        child: Widget to attach.
        left: Left column index (inclusive).
        right: Right column index (exclusive).
        top: Top row index (inclusive).
        bottom: Bottom row index (exclusive).
        xoptions: ``AttachOptions`` for horizontal expand; default shrink.
        yoptions: ``AttachOptions`` for vertical expand; default shrink.
        xpadding: Margin applied to start/end of child.
        ypadding: Margin applied to top/bottom of child.
    """
    expand = xoptions != AttachOptions.SHRINK if xoptions is not None else False
    vexpand = yoptions != AttachOptions.SHRINK if yoptions is not None else False
    child.set_margin_start(xpadding)
    child.set_margin_end(xpadding)
    child.set_margin_top(ypadding)
    child.set_margin_bottom(ypadding)
    child.set_hexpand(expand)
    child.set_vexpand(vexpand)
    grid.attach(child, left, top, max(1, right - left), max(1, bottom - top))


def box_pack(box, child, expand=False, fill=True, padding=0):
    """Append a child to a box (GTK 3 ``pack_start`` semantics).

    Args:
        box: ``Gtk.Box`` container.
        child: Widget to add.
        expand: Whether child should expand along box orientation.
        fill: Treated like expand for Gtk.Box.
        padding: Uniform margin on all sides of child.
    """
    child.set_margin_start(padding)
    child.set_margin_end(padding)
    child.set_margin_top(padding)
    child.set_margin_bottom(padding)
    if box.get_orientation() == Gtk.Orientation.HORIZONTAL:
        child.set_hexpand(bool(expand or fill))
    else:
        child.set_vexpand(bool(expand or fill))
    box.append(child)


def box_pack_end(box, child, expand=False, fill=True, padding=0):
    """Prepend a child to a box (GTK 3 ``pack_end`` semantics)."""
    child.set_margin_start(padding)
    child.set_margin_end(padding)
    child.set_margin_top(padding)
    child.set_margin_bottom(padding)
    if box.get_orientation() == Gtk.Orientation.HORIZONTAL:
        child.set_hexpand(bool(expand or fill))
    else:
        child.set_vexpand(bool(expand or fill))
    box.prepend(child)


def new_treeview(model=None):
    """Create a ``Gtk.TreeView`` and optionally attach a model.

    Args:
        model: ``Gtk.TreeModel`` or None.

    Returns:
        Gtk.TreeView: New tree view.
    """
    treeview = Gtk.TreeView()
    if model is not None:
        treeview.set_model(model)
    return treeview


def new_treeview_column(title):
    """Create a ``Gtk.TreeViewColumn`` with a title (GTK 4 keyword API)."""
    return Gtk.TreeViewColumn(title=title)


def treeview_column_pack_start(column, cell, expand=True):
    """Add a cell renderer to a tree view column."""
    if hasattr(column, 'pack_start'):
        column.pack_start(cell, expand)
    else:
        column.append(cell)


def treeview_column_set_attributes(column, cell, **attrs):
    """Bind list-store columns to cell renderer attributes."""
    column.set_attributes(cell, **attrs)


def color_parse(spec):
    """Parse a color string into ``Gdk.RGBA``.

    Args:
        spec: CSS-style color (e.g. ``'#ff8040'``).

    Returns:
        Gdk.RGBA or None: Parsed color, or None if parsing fails.
    """
    rgba = Gdk.RGBA()
    if not rgba.parse(spec):
        return None
    return rgba


def entry_modify_base(entry, state, color):
    """Set entry background color on GTK 3 only (no-op on GTK 4)."""
    if hasattr(entry, 'modify_base'):
        entry.modify_base(state, color)


def scrolled_set_child(scrolled, child):
    """Set the child of a ``Gtk.ScrolledWindow`` (GTK 4 ``set_child``)."""
    scrolled.set_child(child)


def button_new_stock(stock_label, label=None):
    """Create a button with stock-style mnemonic label.

    Args:
        stock_label: Stock id (e.g. ``STOCK_OK``); leading ``_`` enables underline.
        label: Explicit label; defaults to stock text without ``_``.

    Returns:
        Gtk.Button: New button.
    """
    text = label if label is not None else stock_label.lstrip('_')
    btn = Gtk.Button(label=text)
    btn.set_use_underline(True)
    return btn


def dialog_run(dialog, test_auto_cancel=False, close_on_response=True):
    """Run a dialog modally until ``response`` is emitted.

    When ``ASTROLOGY_TEST=1`` or ``test_auto_cancel`` is True, auto-emits
    ``CANCEL`` so automated tests do not block on user input.

    Args:
        dialog: ``Gtk.Dialog`` instance.
        test_auto_cancel: Force auto-cancel regardless of environment.
        close_on_response: If False, the caller must close the dialog after
            reading widget state (e.g. ``Entry.get_text()``).

    Returns:
        Gtk.ResponseType: Last response id.
    """
    result = [Gtk.ResponseType.NONE]
    auto = test_auto_cancel or os.environ.get('ASTROLOGY_TEST') == '1'

    def on_response(dlg, response):
        result[0] = response
        if close_on_response:
            dlg.close()

    dialog.connect('response', on_response)

    def auto_respond():
        if result[0] == Gtk.ResponseType.NONE:
            dialog.emit('response', Gtk.ResponseType.CANCEL)
        return False

    dialog.present()
    if auto:
        GLib.idle_add(auto_respond)
    while result[0] == Gtk.ResponseType.NONE:
        GLib.MainContext.default().iteration(True)
    return result[0]


def window_set_icon(window, path):
    """Set a window icon from a filesystem path; ignores errors."""
    try:
        window.set_icon(Gio.FileIcon.new(Gio.File.new_for_path(path)))
    except Exception:
        pass


def dialog_content(dialog):
    """Return the vertical content box for dialog fields."""
    return getattr(dialog, '_oa_content', dialog.get_content_area())


def dialog_action_area(dialog):
    """Return (and lazily create) a horizontal button box below dialog content."""
    area = getattr(dialog, '_oa_button_box', None)
    if area is not None:
        return area
    area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    area.set_halign(Gtk.Align.END)
    area.set_margin_top(6)
    dialog._oa_button_box = area
    content = dialog.get_content_area()
    content.append(area)
    return area


def grid_set_row_spacing(grid, row_or_spacing, spacing=None):
    """Set grid row spacing; per-row spacing from GTK 3 Table is ignored."""
    if spacing is None:
        grid.set_row_spacing(row_or_spacing)


def file_chooser_dialog(parent, title, action, ok_label, cancel_label=STOCK_CANCEL):
    """Create a ``Gtk.FileChooserDialog`` with OK and Cancel buttons."""
    d = Gtk.FileChooserDialog(transient_for=parent, title=title or '', action=action)
    d.add_button(cancel_label, Gtk.ResponseType.CANCEL)
    d.add_button(ok_label, Gtk.ResponseType.OK)
    return d


def chooser_get_path(chooser):
    """Return the selected file path from a file chooser, or None."""
    f = None
    try:
        f = chooser.get_save_file()
    except (AttributeError, TypeError):
        pass
    if f is None:
        f = chooser.get_file()
    if f is None:
        return None
    path = f.get_path()
    if path:
        return path
    uri = f.get_uri()
    if uri and uri.startswith('file://'):
        return Gio.File.new_for_uri(uri).get_path()
    return None


def file_chooser_run(chooser, test_auto_cancel=False):
    """Run a file chooser modally and return ``(response, path)``.

    The dialog is closed only after reading the path so GTK 4 does not clear
    the selection on ``close()`` (which would leave ``path`` as None).
    """
    response = dialog_run(
        chooser, test_auto_cancel=test_auto_cancel, close_on_response=False)
    path = chooser_get_path(chooser) if response == Gtk.ResponseType.OK else None
    chooser_close(chooser)
    return response, path


def chooser_set_folder(chooser, path):
    """Set initial folder for a file chooser."""
    try:
        chooser.set_initial_folder(Gio.File.new_for_path(path))
    except AttributeError:
        chooser.set_current_folder(Gio.File.new_for_path(path))


def chooser_close(chooser):
    """Close a native file chooser dialog."""
    chooser.close()


def message_dialog(parent, title, message, buttons=Gtk.ButtonsType.OK):
    """Create an informational message dialog."""
    return Gtk.MessageDialog(
        transient_for=parent,
        message_type=Gtk.MessageType.INFO,
        buttons=buttons,
        text=title,
        secondary_text=message,
    )


def question_dialog(parent, title, message):
    """Create an OK/Cancel question dialog."""
    return Gtk.MessageDialog(
        transient_for=parent,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text=title,
        secondary_text=message,
    )


def new_code_dropdown():
    """Create a ``Gtk.DropDown`` for labelled code rows (GTK 4; replaces ``ComboBox``)."""
    dropdown = Gtk.DropDown()
    dropdown._oa_rows = []
    return dropdown


def picker_connect_changed(dropdown, callback):
    """Connect ``callback(dropdown)`` when the selected row changes."""
    def _on_selected(_w, _p):
        if getattr(dropdown, '_oa_loading', False):
            return
        callback(dropdown)

    dropdown.connect('notify::selected', _on_selected)


def picker_set_rows(dropdown, rows, active=0):
    """Fill a code dropdown; ``rows`` is a list of tuples (label first)."""
    dropdown._oa_loading = True
    try:
        dropdown._oa_rows = list(rows)
        strings = Gtk.StringList()
        for row in rows:
            strings.append(str(row[0]))
        dropdown.set_model(strings)
        if not getattr(dropdown, '_oa_expr_set', False):
            dropdown.set_expression(
                Gtk.PropertyExpression.new(Gtk.StringObject, None, 'string'),
            )
            dropdown._oa_expr_set = True
        if rows and 0 <= active < len(rows):
            dropdown.set_selected(active)
        elif not rows:
            dropdown.set_selected(Gtk.INVALID_LIST_POSITION)
    finally:
        dropdown._oa_loading = False


def cascade_geonames_pickers(cont, country, prov, city, on_cont, on_country, on_prov, on_city):
    """Fill country/province/city after continent (DropDown has no initial ``changed``)."""
    on_cont(cont)
    on_country(country)
    on_prov(prov)
    on_city(city)


def picker_selected_index(dropdown):
    """Return the selected row index, or -1 if none."""
    sel = dropdown.get_selected()
    invalid = getattr(Gtk, 'INVALID_LIST_POSITION', 0xFFFFFFFF)
    if sel == invalid or sel < 0:
        return -1
    return sel


def picker_selected_row(dropdown):
    """Return the full tuple for the selected row, or None."""
    idx = picker_selected_index(dropdown)
    if idx < 0 or idx >= len(dropdown._oa_rows):
        return None
    return dropdown._oa_rows[idx]


def picker_get_rows(dropdown):
    """Return the row tuples last passed to ``picker_set_rows``."""
    return list(dropdown._oa_rows)


def picker_set_selected(dropdown, index):
    """Select row by index without changing the row list."""
    if 0 <= index < len(dropdown._oa_rows):
        dropdown.set_selected(index)


def combo_bind_text_column(combo, text_column=0):
    """Bind a ``Gtk.ComboBox`` text column to a ``CellRendererText``.

    Replaces GTK 3 ``pack_start`` + ``add_attribute('text', n)``. GTK 4 still
    requires ``pack_start``/``add_attribute``; ``set_cell_data_func`` alone leaves
    the popup empty.

    Args:
        combo: ``Gtk.ComboBox`` with a text ``Gtk.ListStore``.
        text_column: Model column index for display text.

    Returns:
        Gtk.CellRendererText: Renderer bound to the combo.
    """
    renderer = Gtk.CellRendererText()
    if hasattr(combo, 'pack_start') and hasattr(combo, 'add_attribute'):
        combo.pack_start(renderer, True)
        combo.add_attribute(renderer, 'text', text_column)
        return renderer

    def cell_data_func(*args):
        model = combo.get_model()
        tree_iter = None
        for arg in args:
            if isinstance(arg, Gtk.TreeIter):
                tree_iter = arg
            elif hasattr(arg, 'get_iter') and hasattr(arg, 'get_value'):
                model = arg
        if model is not None and tree_iter is not None:
            renderer.set_property('text', model.get_value(tree_iter, text_column))

    combo.set_cell_data_func(renderer, cell_data_func, None, True)
    return renderer


def window_set_child(window, child):
    """Set the single child of a window (GTK 4 ``set_child``)."""
    window.set_child(child)


def grid_set_spacing(grid, spacing):
    """Set uniform row and column spacing on a ``Gtk.Grid``."""
    grid.set_column_spacing(spacing)
    grid.set_row_spacing(spacing)
