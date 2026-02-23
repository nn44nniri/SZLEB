from __future__ import annotations
import math

# -----------------------------
# Psychrometrics (Eq 12–13)
# -----------------------------
CVAP = 461.5  # J/(kg*K) used in Eq(12)

def es_magnus_tetens_pa(T_c: float) -> float:
    """Eq (13): saturated vapor pressure es (Pa), T in °C."""
    return 610.94 * math.exp((17.625 * T_c) / (243.04 + T_c))

def abs_humidity_from_rh(T_c: float, RH_pct: float) -> float:
    """Eq (12) + Eq (13): absolute humidity v (kg/m^3)."""
    es = es_magnus_tetens_pa(T_c)
    T_k = T_c + 273.15
    return es * (RH_pct / 100.0) / (T_k * CVAP)

def rh_from_abs_humidity(T_c: float, v: float) -> float:
    """Rearranged Eq (12): RH (%)."""
    es = es_magnus_tetens_pa(T_c)
    T_k = T_c + 273.15
    RH = 100.0 * v * T_k * CVAP / es
    return max(0.0, min(100.0, RH))

def vapor_pressure_from_abs_humidity(T_c: float, v: float) -> float:
    """From Eq (12): v = e / (T_k * Cvap)  =>  e = v * T_k * Cvap (Pa)."""
    T_k = T_c + 273.15
    return v * T_k * CVAP
