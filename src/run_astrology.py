# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Console entry: load this repo before any distro ``astrology_app`` shadow."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> None:
    root = Path(__file__).resolve().parent
    root_s = str(root)
    if sys.path[0] != root_s:
        if root_s in sys.path:
            sys.path.remove(root_s)
        sys.path.insert(0, root_s)

    try:
        import importlib.util

        py_ver = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
        site = Path(sys.prefix) / 'lib' / py_ver / 'site-packages'
        for finder_py in site.glob('__editable___*_finder.py'):
            spec = importlib.util.spec_from_file_location(
                '_astrology_editable_finder', finder_py)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            editable_finder = getattr(mod, '_EditableFinder', None)
            if editable_finder is not None:
                sys.meta_path[:] = [
                    editable_finder,
                    *(f for f in sys.meta_path if f is not editable_finder),
                ]
            break
    except Exception:
        pass

    for name in list(sys.modules):
        if name == 'astrology_app' or name.startswith('astrology_app.'):
            mod = sys.modules.get(name)
            mod_file = getattr(mod, '__file__', None) or ''
            if mod_file and root_s not in mod_file and 'dist-packages' in mod_file:
                del sys.modules[name]


def main() -> int:
    _bootstrap()
    from astrology_app.application import main as app_main

    return app_main()


if __name__ == '__main__':
    raise SystemExit(main())
