# lai_coupled_single_zone.py (patched)
# CHANGE: without changing any physics/formula logic, we only add a "triggers" field
# in the output table so each row shows:
#   - outside temperature (Tout)
#   - inside temperature (T_air)
#   - which triggers were active (heater/solar/ventilation/transpiration/canopy_convection)

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict, Optional


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


# -----------------------------
# Model parameters
# -----------------------------
@dataclass(frozen=True)
class Geometry:
    L: float  # m
    W: float  # m
    H: float  # m

    @property
    def V(self) -> float:  # air volume (m^3)
        return self.L * self.W * self.H

    @property
    def A_floor(self) -> float:  # m^2
        return self.L * self.W

@dataclass(frozen=True)
class Outside:
    T_out_c: float
    RH_out_pct: float
    G_sun_w_m2: float  # shortwave irradiance proxy (W/m^2)

@dataclass(frozen=True)
class Initial:
    T_air_c: float
    RH_air_pct: float
    T_canopy_c: float  # canopy initial temp (°C)

@dataclass(frozen=True)
class AirProps:
    rho: float = 1.20   # kg/m^3
    cp: float = 1006.0  # J/(kg*K)

@dataclass(frozen=True)
class CouplingParams:
    LAI: float

    # h = 10*LAI (Table 2)
    h_per_LAI: float = 10.0  # W/(m^2*K) per LAI unit

    # Transpiration equations (14–16)
    k_lat: float = 2.45e6     # J/kg latent heat of vaporization (approx, near 20°C)
    gamma: float = 66.0       # Pa/K (psychrometric constant in Pa/K, simple constant)
    r_b: float = 200.0        # s/m (boundary-layer resistance, used in the paper block)
    k_tp: float = 0.7         # transpiration parameter in Eq(16) (chosen)
    rn_gain: float = 0.70     # R_n ≈ rn_gain * G (chosen proxy)

@dataclass(frozen=True)
class Actuation:
    ACH: float            # 1/h (airflow proxy)
    UA_w_k: float         # W/K (envelope/insulation lumped)
    Q_heater_w: float     # W
    tau_alpha_air: float  # fraction of solar into air node
    tau_alpha_can: float  # fraction of solar into canopy node


# -----------------------------
# Trigger labelling (NEW)
# -----------------------------
def build_trigger_string(
    act: Actuation,
    outside: Outside,
    coup: CouplingParams,
    A_crop: float,
    Q_trans_W: float,
) -> str:
    """
    Purely descriptive flags; no control logic changes.
    - heater_active: Q_heater_w > 0
    - solar_active: outside.G_sun_w_m2 > 0
    - ventilation_active: ACH > 0
    - transpiration_active: Q_trans_W > 0
    - canopy_convection_active: LAI > 0 (implies h=10*LAI) and A_crop > 0
    """
    flags = []

    if act.Q_heater_w > 0:
        flags.append("heater")
    if outside.G_sun_w_m2 > 0:
        flags.append("solar")
    if act.ACH > 0:
        flags.append("ventilation")
    if Q_trans_W > 0:
        flags.append("transpiration")
    if coup.LAI > 0 and A_crop > 0:
        flags.append("canopy_convection(h=10LAI)")

    return "|".join(flags) if flags else "none"


# -----------------------------
# Core coupled simulation
# -----------------------------
def simulate(
    geom: Geometry,
    outside: Outside,
    init: Initial,
    act: Actuation,
    coup: CouplingParams,
    air: AirProps = AirProps(),
    crop_area_m2: Optional[float] = None,
    dt_s: float = 60.0,
    minutes: int = 10,
) -> List[Dict[str, float]]:

    A_crop = crop_area_m2 if crop_area_m2 is not None else geom.A_floor
    V = geom.V
    dx_airlayers = geom.H  # mapping of "air-layer thickness" to room height

    # Outside humidity in absolute form
    v_out = abs_humidity_from_rh(outside.T_out_c, outside.RH_out_pct)

    # Initial states
    T_air = init.T_air_c
    v_air = abs_humidity_from_rh(init.T_air_c, init.RH_air_pct)
    T_can = init.T_canopy_c

    # Airflow from ACH
    Vdot = act.ACH * V / 3600.0         # m^3/s
    mdot = air.rho * Vdot               # kg/s

    rows: List[Dict[str, float]] = []
    steps = int(minutes * 60.0 / dt_s)

    for k in range(steps + 1):
        t_min = k * dt_s / 60.0

        # --- Derived psychrometrics for Eq(14) ---
        e_s_air = es_magnus_tetens_pa(T_air)                     # Pa
        e_air = vapor_pressure_from_abs_humidity(T_air, v_air)   # Pa

        # --- Net radiation proxy for Eq(16) ---
        Rn = coup.rn_gain * outside.G_sun_w_m2  # W/m^2 proxy

        # Eq (16): stomatal resistance rs (s/m)
        LAI = max(1e-6, coup.LAI)
        r_s = 82.0 + 570.0 * math.exp(-(coup.k_tp * Rn) / LAI) * (1.0 + 0.023 * (T_air - 20.0) ** 2)

        # Eq (15): VEC
        VEC = (2.0 * air.cp * air.rho * LAI) / (coup.k_lat * coup.gamma * (coup.r_b + r_s))

        # Eq (14): transpiration (W) over crop area
        Q_trans_W = coup.k_lat * VEC * max(0.0, (e_s_air - e_air)) * A_crop

        # h = 10*LAI (Table 2): canopy-air convection
        h_can_air = coup.h_per_LAI * LAI
        Q_conv_can_to_air_W = h_can_air * A_crop * (T_can - T_air)

        # Ventilation latent term for Eq(17)
        Q_latent_vent_Wm2 = (act.ACH / 3600.0) * dx_airlayers * coup.k_lat * (v_air - v_out)

        # Eq (17): dAH (kg/m^3) over dt
        dAH = (dt_s * ((Q_trans_W / A_crop) - Q_latent_vent_Wm2)) / (coup.k_lat * dx_airlayers)
        v_air = max(0.0, v_air + dAH)

        # Energy balance (air)
        Q_env_W = act.UA_w_k * (outside.T_out_c - T_air)
        Q_vent_sens_W = mdot * air.cp * (outside.T_out_c - T_air)
        Q_solar_air_W = act.tau_alpha_air * outside.G_sun_w_m2 * geom.A_floor

        dTair_dt = (Q_env_W + Q_vent_sens_W + act.Q_heater_w + Q_solar_air_W + Q_conv_can_to_air_W) / (air.rho * air.cp * V)
        T_air = T_air + dTair_dt * dt_s

        # Energy balance (canopy)
        C_can_areal = 30_000.0  # J/(m^2*K) chosen effective canopy thermal mass
        Q_solar_can_W = act.tau_alpha_can * outside.G_sun_w_m2 * geom.A_floor
        dTcan_dt = (Q_solar_can_W - Q_conv_can_to_air_W - Q_trans_W) / (C_can_areal * A_crop)
        T_can = T_can + dTcan_dt * dt_s

        RH_air = rh_from_abs_humidity(T_air, v_air)

        # NEW: trigger string (descriptive)
        triggers = build_trigger_string(
            act=act,
            outside=outside,
            coup=coup,
            A_crop=A_crop,
            Q_trans_W=Q_trans_W,
        )

        rows.append({
            "t_min": t_min,

            # Requested in final table
            "Tout_C": outside.T_out_c,
            "Tair_C": T_air,
            "Triggers": triggers,

            # Keep existing outputs (useful diagnostics)
            "RH_air_pct": RH_air,
            "v_air_g_m3": v_air * 1000.0,
            "T_can_C": T_can,
            "ACH_1_h": act.ACH,
            "LAI": coup.LAI,
            "h_can_air_W_m2K": h_can_air,
            "r_s_s_m": r_s,
            "VEC": VEC,
            "Q_trans_W": Q_trans_W,
            "Q_conv_can_to_air_W": Q_conv_can_to_air_W,
            "v_out_g_m3": v_out * 1000.0,
        })

    return rows


def main() -> None:
    geom = Geometry(L=20.0, W=10.0, H=4.0)

    outside = Outside(
        T_out_c=-10.0,
        RH_out_pct=70.0,
        G_sun_w_m2=150.0,
    )

    init = Initial(
        T_air_c=15.0,
        RH_air_pct=60.0,
        T_canopy_c=15.0,
    )

    act = Actuation(
        ACH=2.0,
        UA_w_k=250.0,
        Q_heater_w=10_000.0,
        tau_alpha_air=0.25,
        tau_alpha_can=0.20,
    )

    coup = CouplingParams(LAI=2.0)

    rows = simulate(
        geom=geom,
        outside=outside,
        init=init,
        act=act,
        coup=coup,
        dt_s=60.0,
        minutes=10,
    )

    # Final table (requested columns first)
    print("t(min)\tTout(°C)\tTin(°C)\tTriggers\t\t\tRH(%)\tv(g/m3)")
    for r in rows:
        print(
            f"{r['t_min']:>5.0f}\t"
            f"{r['Tout_C']:>7.2f}\t"
            f"{r['Tair_C']:>7.2f}\t"
            f"{r['Triggers']:<28}\t"
            f"{r['RH_air_pct']:>6.1f}\t"
            f"{r['v_air_g_m3']:>7.3f}"
        )


if __name__ == "__main__":
    main()