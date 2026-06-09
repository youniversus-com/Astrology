Getting started
===============

Screenshots
-----------

.. figure:: screenshots/natal-wheel-default.png
   :alt: Natal chart wheel with default theme
   :width: 480px

   Natal chart wheel (Amsterdam, 1990-06-15).

.. figure:: screenshots/main-window.png
   :alt: Main application window
   :width: 640px

   Main window with chart, data table, and toolbar.

.. figure:: screenshots/transit-view.png
   :alt: Transit chart overlay
   :width: 480px

   Transit chart (outer ring) over the natal wheel.

.. figure:: screenshots/event-editor.png
   :alt: Edit event details dialog
   :width: 480px

   Event editor for birth date, time, and location.

.. figure:: screenshots/settings-planets.png
   :alt: Planets and angles settings dialog
   :width: 360px

   Planets & angles settings.

Installation
------------

Clone the repository and run the install script:

.. code-block:: bash

   git clone https://github.com/YOUR_ORG/astrology.git
   cd astrology
   ./install.sh
   source .venv/bin/activate
   astrology

System packages (Debian/Ubuntu):

.. code-block:: bash

   sudo apt install python3-dev python3-gi python3-gi-cairo \
     gir1.2-gtk-4.0 gir1.2-rsvg-2.0 librsvg2-bin imagemagick

Ephemeris data
--------------

Swiss Ephemeris ``.se1`` files are fetched on install. To skip:

.. code-block:: bash

   ASTROLOGY_SKIP_EPHE_UPDATE=1 ./install.sh

User data
---------

Charts and settings are stored under ``~/.config/com.youniverse.astrology/`` by default
(see :mod:`astrologymod.branding`).

Running from source
-------------------

.. code-block:: bash

   source .venv/bin/activate
   python src/astrology

Troubleshooting
---------------

- **Window does not appear:** check ``echo $DISPLAY``; stop stuck instances with
  ``pkill -f '.venv/bin/astrology'``.
- **``gi`` import errors in venv:** re-run ``./install.sh`` (ensures
  ``system-site-packages`` is enabled for PyGObject).
