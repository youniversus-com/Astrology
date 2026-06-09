# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later

# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath('../src'))

from astrologymod.branding import COPYRIGHT_HOLDER

project = 'YoUniverse Astrology'
author = COPYRIGHT_HOLDER
copyright = f'2026, {COPYRIGHT_HOLDER}'
release = open('../src/VERSION').read().strip()
version = release

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_mock_imports = [
    'gi',
    'gi.repository',
    'swisseph',
    'cairo',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

todo_include_todos = False
