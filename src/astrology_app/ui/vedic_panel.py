# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK dialog for Vedic chart report (vargas, dashas, panchanga, yogas)."""

from __future__ import annotations

from gi import require_version

require_version('Gtk', '4.0')
from gi.repository import Gtk

from astrologymod import gtkcompat as g4
from astrologymod.swiss import sign_index
from astrologymod.vedic.constants import RASHI_NAMES, VARGA_CODES, VARGA_NAMES
from astrologymod.vedic.chart_svg import render_vedic_chart_svg
from astrologymod.vedic.graha import parse_varga_display

import astrology_app.globals as g


def _format_dasha_section(title: str, periods) -> list[str]:
    lines = ['', title]
    for p in periods[:12]:
        lines.append(
            '%s %s — %s to %s' % (
                p.lord_label,
                p.level,
                p.start.strftime('%Y-%m-%d'),
                p.end.strftime('%Y-%m-%d'),
            )
        )
    return lines


def _format_report() -> str:
    snap = getattr(g.astrology_chart, 'vedic', None)
    if snap is None:
        return _('No Vedic data. Set Tradition to Vedic in Settings → Configuration.')

    lines = [
        _('=== Vedic Chart (Jyotish) ==='),
        '',
        _('Ayanamsa: %s') % snap.ayanamsa_mode,
        _('Lagna: %s (%s)') % (snap.lagna_rashi.name, snap.lagna_rashi.name_en),
        _('Lagna lord: %s') % snap.lagna_rashi.lord_label,
        '',
        _('--- Panchanga ---'),
        _('Tithi: %s (%s)') % (snap.panchanga.tithi, snap.panchanga.tithi_name),
        _('Nakshatra: %s') % snap.panchanga.nakshatra,
        _('Yoga: %s (%s)') % (snap.panchanga.yoga, snap.panchanga.yoga_name),
        _('Karana: %s (%s)') % (snap.panchanga.karana, snap.panchanga.karana_name),
        _('Vara: %s') % snap.panchanga.vara_name,
        '',
        _('--- Grahas (D1) ---'),
    ]
    for gr in snap.grahas:
        flags = []
        if gr.retrograde:
            flags.append('R')
        if gr.combust:
            flags.append(_('combust'))
        flag_s = ' [' + ', '.join(flags) + ']' if flags else ''
        drishti_s = ''
        if gr.drishti_from:
            drishti_s = ' — ' + _('drishti from') + ': ' + ', '.join(gr.drishti_from)
        lines.append(
            '%s: %s %s° — %s / %s (pada %s) — House %s%s%s' % (
                gr.label,
                gr.rashi.name,
                '%.2f' % gr.rashi.degree_in_sign,
                gr.nakshatra.name,
                gr.nakshatra.lord_label,
                gr.nakshatra.pada,
                gr.house,
                flag_s,
                drishti_s,
            )
        )

    dasha_title = {
        'vimshottari': _('--- Vimshottari Mahadasha (primary) ---'),
        'yogini': _('--- Yogini Dasha (primary) ---'),
        'ashtottari': _('--- Ashtottari Dasha (primary) ---'),
    }.get(snap.dasha_system, _('--- Dasha ---'))
    lines.extend(_format_dasha_section(dasha_title, snap.primary_dasha))

    if snap.dasha_system != 'vimshottari':
        lines.extend(_format_dasha_section(_('--- Vimshottari Mahadasha ---'), snap.vimshottari))
    if snap.dasha_system != 'yogini':
        lines.extend(_format_dasha_section(_('--- Yogini Dasha ---'), snap.yogini))
    if snap.dasha_system != 'ashtottari':
        lines.extend(_format_dasha_section(_('--- Ashtottari Dasha ---'), snap.ashtottari))

    if snap.vimshottari_antar:
        lines.extend(['', _('--- Antardasha (first Mahadasha) ---')])
        for p in snap.vimshottari_antar[:9]:
            lines.append(
                '%s: %s — %s' % (
                    p.lord_label,
                    p.start.strftime('%Y-%m-%d'),
                    p.end.strftime('%Y-%m-%d'),
                )
            )

    lines.extend(['', _('--- Yogas ---')])
    if snap.yogas:
        for y in sorted(snap.yogas, key=lambda x: -x.strength):
            lines.append('%s (%.0f%%): %s' % (y.name, y.strength * 100, y.description))
    else:
        lines.append(_('(none detected)'))

    lines.extend(['', _('--- Shadbala (simplified) ---')])
    for sb in snap.shadbala:
        lines.append('%s: %.1f' % (
            {0: 'Surya', 1: 'Chandra', 2: 'Budha', 3: 'Shukra', 4: 'Mangal',
             5: 'Guru', 6: 'Shani'}.get(sb.planet_id, '?'),
            sb.total,
        ))

    lines.extend(['', _('--- Ashtakavarga (simplified bindus) ---')])
    for pid, bindus in snap.ashtakavarga.items():
        lines.append('%s: %s (SAV %s)' % (
            {0: 'Surya', 1: 'Chandra', 2: 'Budha', 3: 'Shukra', 4: 'Mangal',
             5: 'Guru', 6: 'Shani'}.get(pid, str(pid)),
            bindus,
            sum(bindus),
        ))

    display_codes = parse_varga_display(g.db.astrocfg.get('vedic_varga_display', ','.join(VARGA_CODES)))
    lines.extend(['', _('--- Shodashvarga (sign placements) ---')])
    for code in display_codes:
        if code not in snap.varga_chart:
            continue
        name = VARGA_NAMES.get(code, code)
        lines.append('%s (%s):' % (code, name))
        for gr in snap.grahas:
            if gr.index > 6 and gr.index not in (10, 29):
                continue
            lon = snap.varga_chart[code].get(gr.index, 0)
            lines.append('  %s → %s' % (gr.label, RASHI_NAMES[sign_index(lon)]))

    lines.extend(['', _('--- Muhurta (top slots, birth day) ---')])
    for slot in snap.muhurta_slots[:8]:
        lines.append(
            '%s — %s: %.0f — %s' % (
                slot.start.strftime('%H:%M'),
                slot.end.strftime('%H:%M'),
                slot.score,
                slot.notes,
            )
        )
    return '\n'.join(lines)


def show_vedic_panel(parent_window) -> None:
    """Open modal Vedic report dialog."""
    dialog = Gtk.Window()
    dialog.set_transient_for(parent_window)
    dialog.set_modal(True)
    dialog.set_title(_('Vedic Astrology'))
    dialog.set_default_size(720, 560)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)

    notebook = Gtk.Notebook()
    textview = Gtk.TextView()
    textview.set_editable(False)
    textview.set_monospace(True)
    buf = textview.get_buffer()
    buf.set_text(_format_report())
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
    scroll.set_child(textview)
    scroll.set_vexpand(True)
    notebook.append_page(scroll, Gtk.Label(label=_('Report')))

    snap = getattr(g.astrology_chart, 'vedic', None)
    if snap is not None:
        layout = g.db.astrocfg.get('vedic_chart_layout', 'north')
        if layout == 'wheel':
            layout = 'north'
        chart_vargas = ('D1', 'D9')
        if 'D10' in parse_varga_display(g.db.astrocfg.get('vedic_varga_display', 'D1,D9,D10')):
            chart_vargas = ('D1', 'D9', 'D10')
        for varga in chart_vargas:
            label = _('Rashi') if varga == 'D1' else VARGA_NAMES.get(varga, varga)
            svg_data = render_vedic_chart_svg(snap, layout, varga=varga)
            path = g.cfg.tempfilename.replace('.svg', f'-vedic-{varga}.svg')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(svg_data)
            try:
                from gi.repository import Rsvg
                handle = Rsvg.Handle.new_from_file(path)
                pix = handle.get_pixbuf()
                img = Gtk.Image.new_from_pixbuf(pix)
            except Exception:
                img = Gtk.Label(label=_('Chart: %s') % varga)
            sc = Gtk.ScrolledWindow()
            sc.set_child(img)
            notebook.append_page(sc, Gtk.Label(label=label))

    box.append(notebook)

    close_btn = g4.button_new_stock(g4.STOCK_CLOSE)
    close_btn.connect('clicked', lambda w: dialog.close())
    box.append(close_btn)

    dialog.set_child(box)
    dialog.present()
