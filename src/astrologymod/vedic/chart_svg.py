# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""North and South Indian Vedic chart SVG generation."""

from __future__ import annotations

import math
from xml.sax.saxutils import escape as xml_escape

from astrologymod.swiss import sign_index
from astrologymod.vedic.constants import LORD_LABELS, RASHI_LORDS, RASHI_NAMES, VARGA_NAMES
from astrologymod.vedic.snapshot import VedicChartSnapshot

GRAHA_SHORT = {
    0: 'Su', 1: 'Mo', 2: 'Me', 3: 'Ve', 4: 'Ma', 5: 'Ju', 6: 'Sa',
    10: 'Ra', 29: 'Ke',
}

# How far along the house bisector labels sit (0=center, 1=rim).
NORTH_LABEL_FRAC = 0.76


def _diamond_edge(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    """Point where a ray from the center meets the diamond boundary."""
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    denom = abs(cos_a) + abs(sin_a)
    if denom < 1e-9:
        return cx, cy
    t = r / denom
    return cx + t * cos_a, cy + t * sin_a


def _north_wedge_label_pos(
    cx: float, cy: float, r: float, house_index: int,
) -> tuple[float, float, float]:
    """(x, y, bisector_angle) for house label — outer wedge, away from center."""
    a_mid = -90 + house_index * 30 + 15
    ex, ey = _diamond_edge(cx, cy, r, a_mid)
    frac = NORTH_LABEL_FRAC
    return cx + (ex - cx) * frac, cy + (ey - cy) * frac, a_mid


def _text_anchor_for_angle(angle_deg: float) -> str:
    """Avoid labels drifting into neighbours on left/right houses."""
    a = (angle_deg + 360) % 360
    if 45 <= a < 135:
        return 'start'
    if 225 <= a < 315:
        return 'end'
    return 'middle'


def _degree_in_sign(lon: float) -> int:
    return int(round(lon % 30.0)) % 30


def _scale_font(base: int, size: float) -> int:
    return max(base, int(size / 7))


def _sign_lord_short(sign: int) -> str:
    lord_id = RASHI_LORDS[sign]
    return LORD_LABELS.get(lord_id, '?')[:2]


def _planets_in_sign(
    snapshot: VedicChartSnapshot,
    sign: int,
    varga: str = 'D1',
) -> list[str]:
    lons = snapshot.varga_chart.get(varga, {})
    lines: list[str] = []
    for g in snapshot.grahas:
        lon = lons.get(g.index, g.longitude)
        if sign_index(lon) != sign:
            continue
        short = GRAHA_SHORT.get(g.index, str(g.index))
        deg = _degree_in_sign(lon)
        marks = ''
        if g.retrograde:
            marks += 'R'
        if g.combust and g.index <= 6:
            marks += 'c'
        lines.append(f'{short}{deg}{marks}')
    return lines


def _north_house_header(house_num: int, sign: int) -> str:
    lord = _sign_lord_short(sign)
    head = f'{house_num} {RASHI_NAMES[sign][:3]} {lord}'
    if house_num == 1:
        head += ' Lg'
    return head


def _svg_text_block(
    x: float,
    y: float,
    rows: list[str],
    *,
    font_size: int = 10,
    fill: str = '#000000',
    bold_rows: frozenset[int] | None = None,
    line_height: int = 11,
    anchor: str = 'middle',
) -> str:
    if not rows:
        return ''
    bold_rows = bold_rows or frozenset()
    ax = x
    parts = [
        f'<text x="{ax:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{font_size}" fill="{fill}">',
    ]
    for i, row in enumerate(rows):
        if not row:
            continue
        weight = ' font-weight="bold"' if i in bold_rows else ''
        dy = '0' if i == 0 else str(line_height)
        parts.append(
            f'<tspan x="{ax:.1f}" dy="{dy}"{weight}>{xml_escape(row)}</tspan>',
        )
    parts.append('</text>')
    return ''.join(parts)


def _north_grid_lines(cx: float, cy: float, r: float, line_color: str) -> list[str]:
    top = f'{cx},{cy - r}'
    right = f'{cx + r},{cy}'
    bottom = f'{cx},{cy + r}'
    left = f'{cx - r},{cy}'
    lines = [
        f'<polygon points="{top} {right} {bottom} {left}" fill="none" '
        f'stroke="{line_color}" stroke-width="2"/>',
        f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" '
        f'stroke="{line_color}" stroke-width="1"/>',
        f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" '
        f'stroke="{line_color}" stroke-width="1"/>',
        f'<line x1="{cx - r * 0.707}" y1="{cy - r * 0.707}" x2="{cx + r * 0.707}" y2="{cy + r * 0.707}" '
        f'stroke="{line_color}" stroke-width="1"/>',
        f'<line x1="{cx + r * 0.707}" y1="{cy - r * 0.707}" x2="{cx - r * 0.707}" y2="{cy + r * 0.707}" '
        f'stroke="{line_color}" stroke-width="1"/>',
    ]
    for h in range(12):
        ex, ey = _diamond_edge(cx, cy, r, -90 + h * 30)
        lines.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{line_color}" stroke-width="0.75" opacity="0.85"/>',
        )
    return lines


def north_indian_chart(
    snapshot: VedicChartSnapshot,
    width: int = 400,
    height: int = 400,
    varga: str = 'D1',
    paper_color: str = '#ffffff',
    line_color: str = '#333333',
    text_color: str = '#000000',
    accent_color: str = '#8b4513',
) -> str:
    """Diamond North Indian chart (lagna house at top)."""
    lagna = snapshot.lagna_sign
    varga_title = VARGA_NAMES.get(varga, varga)
    margin_top = 52
    margin_bottom = 16
    cx = width / 2
    cy = margin_top + (height - margin_top - margin_bottom) / 2
    r = min(width * 0.46, (height - margin_top - margin_bottom) * 0.46)
    fs_head = _scale_font(9, r * 0.35)
    fs_body = max(8, fs_head - 1)
    lh_head = fs_head + 2
    lh_body = fs_body + 1

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{paper_color}"/>',
    ]
    lagna_deg = int(round(snapshot.lagna_longitude % 30.0)) % 30
    lines.append(
        f'<text x="{cx:.1f}" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="{text_color}">'
        f'{xml_escape(varga_title)} ({varga})</text>',
    )
    lines.append(
        f'<text x="{cx:.1f}" y="40" text-anchor="middle" font-size="11" fill="{text_color}">'
        f'Lagna {xml_escape(RASHI_NAMES[lagna])} {lagna_deg}° · '
        f'{xml_escape(snapshot.panchanga.nakshatra)}</text>',
    )
    lines.extend(_north_grid_lines(cx, cy, r, line_color))

    for h in range(12):
        sign = (lagna + h) % 12
        house_num = h + 1
        hx, hy, angle = _north_wedge_label_pos(cx, cy, r, h)
        anchor = _text_anchor_for_angle(angle)
        planets = _planets_in_sign(snapshot, sign, varga)
        header = _north_house_header(house_num, sign)
        fill = accent_color if house_num == 1 else text_color
        n_planets = len(planets)
        if n_planets == 0:
            lines.append(
                _svg_text_block(
                    hx, hy,
                    [header, '—'],
                    font_size=fs_head,
                    fill=fill,
                    bold_rows=frozenset({0}),
                    line_height=lh_head,
                    anchor=anchor,
                ),
            )
        elif n_planets <= 2:
            rows = [header] + planets
            lines.append(
                _svg_text_block(
                    hx, hy,
                    rows,
                    font_size=fs_head,
                    fill=fill,
                    bold_rows=frozenset({0}),
                    line_height=lh_head,
                    anchor=anchor,
                ),
            )
        else:
            lines.append(
                _svg_text_block(
                    hx, hy,
                    [header],
                    font_size=fs_head,
                    fill=fill,
                    bold_rows=frozenset({0}),
                    line_height=lh_head,
                    anchor=anchor,
                ),
            )
            planet_line = ' '.join(planets[:4])
            if len(planets) > 4:
                planet_line += ' …'
            lines.append(
                _svg_text_block(
                    hx, hy + lh_head + 1,
                    [planet_line],
                    font_size=fs_body,
                    fill=fill,
                    line_height=lh_body,
                    anchor=anchor,
                ),
            )

    lines.append('</svg>')
    return '\n'.join(lines)


def south_indian_chart(
    snapshot: VedicChartSnapshot,
    width: int = 420,
    height: int = 360,
    varga: str = 'D1',
    paper_color: str = '#ffffff',
    line_color: str = '#333333',
    text_color: str = '#000000',
    accent_color: str = '#8b4513',
) -> str:
    """Fixed South Indian grid (Aries top-left; signs fixed), centered and scaled."""
    lagna = snapshot.lagna_sign
    varga_title = VARGA_NAMES.get(varga, varga)
    grid = (
        (11, 0, 1, 2),
        (10, -1, -1, 3),
        (9, -1, -1, 4),
        (8, 7, 6, 5),
    )
    title_h = 44
    margin = 10
    cols, rows = 4, 4
    avail_w = width - 2 * margin
    avail_h = height - title_h - margin
    cell = min(avail_w / cols, avail_h / rows)
    grid_w = cell * cols
    grid_h = cell * rows
    ox = (width - grid_w) / 2
    oy = title_h + (height - title_h - margin - grid_h) / 2
    fs = _scale_font(9, cell)
    fs_title = max(11, _scale_font(11, cell))
    fs_center = max(10, fs)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{paper_color}"/>',
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" font-size="{fs_title}" font-weight="bold" fill="{text_color}">'
        f'{xml_escape(varga_title)} ({varga}) — Lagna {xml_escape(RASHI_NAMES[lagna])}</text>',
    ]
    for row in range(4):
        for col in range(4):
            if grid[row][col] < 0:
                if row == 1 and col == 1:
                    cx = ox + cell
                    cy = oy + cell
                    lines.append(
                        f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell * 2:.1f}" height="{cell * 2:.1f}" '
                        f'fill="#f8f8f8" stroke="{line_color}" stroke-width="2"/>',
                    )
                    mid_x = cx + cell
                    mid_y = cy + cell
                    lines.append(
                        _svg_text_block(
                            mid_x, mid_y - fs_center,
                            [snapshot.panchanga.nakshatra],
                            font_size=fs_center,
                            fill=text_color,
                            bold_rows=frozenset({0}),
                            line_height=fs_center + 2,
                        ),
                    )
                    lines.append(
                        _svg_text_block(
                            mid_x, mid_y + fs_center,
                            [f'{snapshot.panchanga.tithi_name} · {snapshot.panchanga.vara_name}'],
                            font_size=max(8, fs_center - 1),
                            fill=text_color,
                            line_height=fs_center,
                        ),
                    )
                continue
            sign = grid[row][col]
            x, y = ox + col * cell, oy + row * cell
            is_lagna = sign == lagna
            fill = '#fff6e8' if is_lagna else 'none'
            stroke_w = 2.5 if is_lagna else 1
            stroke = accent_color if is_lagna else line_color
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="{stroke_w}"/>',
            )
            sign_lbl = f'{sign + 1} {RASHI_NAMES[sign][:3]} {_sign_lord_short(sign)}'
            if is_lagna:
                sign_lbl += ' Lg'
            planets = _planets_in_sign(snapshot, sign, varga)
            pad = max(10, int(cell * 0.14))
            if not planets:
                rows_txt = [sign_lbl, '—']
                lines.append(
                    _svg_text_block(
                        x + cell / 2, y + pad,
                        rows_txt,
                        font_size=fs,
                        fill=accent_color if is_lagna else text_color,
                        bold_rows=frozenset({0}),
                        line_height=fs + 2,
                    ),
                )
            elif len(planets) <= 3:
                lines.append(
                    _svg_text_block(
                        x + cell / 2, y + pad,
                        [sign_lbl] + planets,
                        font_size=fs,
                        fill=accent_color if is_lagna else text_color,
                        bold_rows=frozenset({0}),
                        line_height=fs + 2,
                    ),
                )
            else:
                lines.append(
                    _svg_text_block(
                        x + cell / 2, y + pad,
                        [sign_lbl],
                        font_size=fs,
                        fill=accent_color if is_lagna else text_color,
                        bold_rows=frozenset({0}),
                        line_height=fs + 2,
                    ),
                )
                pline = ' '.join(planets[:5])
                if len(planets) > 5:
                    pline += ' …'
                lines.append(
                    _svg_text_block(
                        x + cell / 2, y + pad + fs + 4,
                        [pline],
                        font_size=max(8, fs - 1),
                        fill=accent_color if is_lagna else text_color,
                        line_height=fs + 1,
                    ),
                )
    lines.append('</svg>')
    return '\n'.join(lines)


def render_vedic_chart_svg(
    snapshot: VedicChartSnapshot,
    layout: str,
    varga: str = 'D1',
    **kwargs: str,
) -> str:
    """Dispatch to north or south layout."""
    if layout == 'south':
        return south_indian_chart(snapshot, varga=varga, **kwargs)
    return north_indian_chart(snapshot, varga=varga, **kwargs)


def render_vedic_chart_svg_on_canvas(
    snapshot: VedicChartSnapshot,
    layout: str,
    canvas_width: int,
    canvas_height: int,
    varga: str = 'D1',
    **kwargs: str,
) -> str:
    """Render chart centered on a full window-sized SVG canvas."""
    paper = kwargs.get('paper_color', '#ffffff')
    footer_h = 28
    margin = 20
    avail_w = canvas_width - 2 * margin
    avail_h = canvas_height - 2 * margin - footer_h
    if layout == 'south':
        chart_w = int(min(avail_w, avail_h * 1.15, 960))
        chart_h = int(min(avail_h, chart_w * 0.82, 820))
    else:
        side = int(min(avail_w, avail_h, 920))
        chart_w = chart_h = max(400, side)
    chart_w = max(320, chart_w)
    chart_h = max(320, chart_h)

    inner = render_vedic_chart_svg(
        snapshot, layout, varga=varga, width=chart_w, height=chart_h, **kwargs,
    )
    start = inner.find('>', inner.find('<svg')) + 1
    end = inner.rfind('</svg>')
    body = inner[start:end].strip() if start > 0 and end > start else inner
    ox = (canvas_width - chart_w) / 2
    oy = margin + max(0.0, (avail_h - chart_h) / 2)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" '
        f'viewBox="0 0 {canvas_width} {canvas_height}">\n'
        f'<rect width="100%" height="100%" fill="{paper}"/>\n'
        f'<g transform="translate({ox:.1f},{oy:.1f})">{body}</g>\n'
        f'</svg>'
    )
