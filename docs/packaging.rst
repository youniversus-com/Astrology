Packaging
=========

Debian / Ubuntu
---------------

Requirements:

.. code-block:: bash

   sudo apt install debhelper dh-python dpkg-dev python3-all python3-dev \
     python3-setuptools gir1.2-gtk-4.0 gir1.2-rsvg-2.0 python3-gi \
     python3-gi-cairo imagemagick librsvg2-bin

Build:

.. code-block:: bash

   make package-deb

Output: ``dist/packages/astrology_<version>_all.deb``

The top entry in ``src/debian/changelog`` must match ``src/VERSION``.

Fedora / RHEL
-------------

Requirements:

.. code-block:: bash

   sudo dnf install rpm-build rpmdevtools

Build:

.. code-block:: bash

   make package-rpm

Output: ``dist/packages/astrology-<version>-*.rpm``

GitHub Actions release flow
---------------------------

Publishing is driven by signed version tags. Pushing ``v*`` starts:

1. ``verify-release.yml``: imports ``.github/gpg/release-signing.asc`` and
   requires an annotated OpenPGP-signed tag.
2. ``packages.yml``: creates the GitHub Release, builds every package target,
   downloads the build artifacts, uploads release assets, and verifies that
   assets were attached.

``packages.yml`` also supports ``workflow_dispatch`` for package-build smoke
tests. Manual dispatch stores Actions artifacts but does not create a GitHub
Release or upload release assets.

Release notes are extracted from the ``CHANGELOG.md`` section matching
``src/VERSION``. If the section is absent, the workflow publishes a minimal
``Release <version>`` note.

Expected release assets:

- ``astrology_<version>*_all.deb``
- ``astrology-<version>-*.rpm``
- ``Astrology-<version>-macos.app.tar.gz``
- ``Astrology-<version>-windows-ucrt64.zip``

For the operator checklist and troubleshooting steps, see ``PUBLISHING.md`` in
the repository root.

Windows and macOS
-----------------

Native desktop bundles use **PyInstaller** and must be built **on the target OS**
(GTK 4 + PyGObject cannot be cross-compiled from Linux).

macOS (.app)
~~~~~~~~~~~~

Requirements: Homebrew, Xcode command-line tools (for code signing, optional).

.. code-block:: bash

   make package-macos
   # or: bash scripts/build-macos.sh

Output:

- ``build/pyinstaller/dist/Astrology.app``
- ``dist/packages/Astrology-<version>-macos.app.tar.gz``

Windows (UCRT64)
~~~~~~~~~~~~~~~~

Requirements: `MSYS2 <https://www.msys2.org/>`_ UCRT64 shell with GTK 4 packages.

.. code-block:: bash

   pacman -S mingw-w64-ucrt-x86_64-{python,python-pip,gcc,gtk4,python-gobject,
     python-cairo,pango,librsvg,gettext,zip,tools}
   bash scripts/build-windows.sh

From PowerShell (launches MSYS2):

.. code-block:: powershell

   .\scripts\build-windows.ps1

Output:

- ``build/pyinstaller/dist/Astrology/`` (folder with ``Astrology.exe``)
- ``dist/packages/Astrology-<version>-windows-ucrt64.zip``

See ``packaging/pyinstaller/`` for the spec file and bundled data rules.

Environment variables
---------------------

``ASTROLOGY_UPDATE_EPHE``
  Set to ``0`` to skip ephemeris download during package builds.

``ASTROLOGY_SKIP_EPHE_UPDATE``
  Set to ``1`` during ``./install.sh`` to skip ephemeris refresh.
