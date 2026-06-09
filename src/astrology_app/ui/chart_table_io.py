# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write astrology table SVG from XML templates."""

from string import Template


def write_table_svg(template_path, screen_path, print_path, printing, substitutions):
	"""Substitute ``substitutions`` into template and write the table SVG."""
	with open(template_path, encoding='utf-8') as f:
		content = Template(f.read()).safe_substitute(substitutions)
	out_path = print_path if printing else screen_path
	with open(out_path, 'w', encoding='utf-8') as f:
		f.write(content)
	return out_path
