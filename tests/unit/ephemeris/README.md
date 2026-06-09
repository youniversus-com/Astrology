# Ephemeris regression tests

Compares Swiss Ephemeris output for fixed Julian dates against reference tropical longitudes (Sun and Moon at J2000.0 noon UT).

`test_de441_bundle.py` checks that DE441-era `.se1` files from `scripts/ephemeris-de441-astrology.txt` are installed (`make update-ephemeris`).

`test_houses.py` checks pysweph’s 13-element `houses()` cusp array is normalized to 12 (ASC index 0, DSC index 6).

No GTK required. Marker: `unit`.
