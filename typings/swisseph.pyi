"""Minimal stubs for pysweph / pyswisseph (Swiss Ephemeris Python binding).

The runtime module is a C extension without shipped type information.
"""

from collections.abc import Sequence
from typing import Any

# --- Functions ---

def julday(year: int, month: int, day: int, hour: float, cal: int = ...) -> float: ...
def calc_ut(
    tjd_ut: float,
    ipl: int,
    iflag: int,
) -> tuple[Any, ...]: ...
def houses(
    tjd_ut: float,
    geolat: float,
    geolon: float,
    hsys: bytes,
) -> tuple[Sequence[float], Sequence[float]]: ...
def houses_ex(
    tjd_ut: float,
    geolat: float,
    geolon: float,
    hsys: bytes,
    iflag: int,
) -> tuple[Sequence[float], Sequence[float]]: ...
def nod_aps_ut(
    tjd_ut: float,
    ipl: int,
    nodbit: int,
    iflag: int,
) -> tuple[Any, ...]: ...
def set_ephe_path(path: str) -> None: ...
def set_topo(geolon: float, geolat: float, altitude: float) -> Any: ...
def set_sid_mode(sid_mode: int, t0: float = ..., ayan_t0: float = ...) -> None: ...
def close() -> None: ...
def _years_diff(tjd_ut1: float, tjd_ut2: float) -> float: ...
def _revjul(
    tjd_ut: float,
    cal: int,
) -> tuple[int, int, int, int, int, int]: ...

# --- Module attributes ---

version: str

# Bodies (SE_* constants)
SUN: int
MOON: int
MERCURY: int
VENUS: int
MARS: int
JUPITER: int
SATURN: int
URANUS: int
NEPTUNE: int
PLUTO: int

# Calculation flags (SEFLG_*)
FLG_SWIEPH: int
FLG_SPEED: int
FLG_TRUEPOS: int
FLG_TOPOCTR: int
FLG_HELCTR: int
FLG_SIDEREAL: int

# Node / apsis flags
NODBIT_MEAN: int
NODBIT_OSCU: int

# Calendar
GREG_CAL: int

# Sidereal modes (SE_SIDM_*); used via getattr(swe, "SIDM_" + name)
SIDM_FAGAN_BRADLEY: int
SIDM_LAHIRI: int
SIDM_DELUCE: int
SIDM_RAMAN: int
SIDM_USHASHASHI: int
SIDM_KRISHNAMURTI: int
SIDM_DJWHAL_KHUL: int
SIDM_YUKTESHWAR: int
SIDM_JN_BHASIN: int
SIDM_BABYL_KUGLER1: int
SIDM_BABYL_KUGLER2: int
SIDM_BABYL_KUGLER3: int
SIDM_BABYL_HUBER: int
SIDM_BABYL_ETPSC: int
SIDM_ALDEBARAN_15TAU: int
SIDM_HIPPARCHOS: int
SIDM_SASSANIAN: int
SIDM_J2000: int
SIDM_J1900: int
SIDM_B1950: int
