# single_zone_greenhouse_sim.py
# 10-minute single-zone (lumped) temperature + humidity simulation
# Uses the paper's psychrometrics:
#   Eq. (12)  v = es*(RH/100) / (T*K * Cvap)
#   Eq. (13)  es = 610.94 * exp(17.625*T / (243.04+T))
# where T is °C in Eq.(13) and Kelvin in Eq.(12).

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple


# ---- Paper psychrometrics (Eq. 12–13) ----
CVAP = 461.5  # J/(kg*K) as used in the paper for Eq.(12)


def es_magnus_tetens_pa(T_c: float) -> float:
    """Saturation vapor pressure es (Pa) using Magnus–Tetens (Eq. 13)."""
    return 610.94 * math.exp((17.625 * T_c) / (243.04 + T_c))


def abs_humidity_from_rh(T_c: float, RH_pct: float) -> float:
    """
    Absolute humidity v (kg/m^3) from temperature and RH using Eq.(12)+(13).
    Eq.(12): v = es*(RH/100) / (T_K * Cvap)
    """
    es = es_magnus_tetens_pa(T_c)
    T_k = T_c + 273.15
    return es * (RH_pct / 100.0) / (T_k * CVAP)


def rh_from_abs_humidity(T_c: float, v: float) -> float:
    """
    RH (%) from absolute humidity v (kg/m^3) by rearranging Eq.(12):
      RH = 100 * v * T_K * Cvap / es
    """
    es = es_magnus_tetens_pa(T_c)
    T_k = T_c + 273.15
    RH = 100.0 * v * T_k * CVAP / es
    return max(0.0, min(100.0, RH))


# ---- Simulation inputs ----
@dataclass(frozen=True)
class Geometry:
    L: float  # m
    W: float  # m
    H: float  # m

    @property
    def volume(self) -> float:
        return self.L * self.W * self.H  # m^3

    @property
    def floor_area(self) -> float:
        return self.L * self.W  # m^2


@dataclass(frozen=True)
class Outside:
    T_out_c: float      # °C
    RH_out_pct: float   # %
    G_sun_w_m2: float   # W/m^2


@dataclass(frozen=True)
class InsideInitial:
    T_in_c: float     # °C
    RH_in_pct: float  # %


@dataclass(frozen=True)
class Actuation:
    ACH: float            # 1/h
    UA_w_k: float         # W/K
    Q_heater_w: float     # W
    tau_alpha: float      # -
    transp_g_m2_h: float  # g/m^2/h over crop area


@dataclass(frozen=True)
class AirProps:
    rho: float = 1.20     # kg/m^3
    cp: float = 1006.0    # J/(kg*K)


def simulate_10min(
    geom: Geometry,
    outside: Outside,
    inside0: InsideInitial,
    act: Actuation,
    air: AirProps = AirProps(),
    dt_s: float = 60.0,
    minutes: int = 10,
    crop_area_m2: float | None = None,
) -> List[Dict[str, float]]:
    """
    Single-zone lumped model for temperature + absolute humidity.

    Temperature:
      dT/dt = ( UA*(Tout-Tin) + mdot*cp*(Tout-Tin) + Qsolar + Qheater ) / (rho*cp*V)

    Moisture (absolute humidity v in kg/m^3):
      dv/dt = (m_trans/V) - (Vdot/V)*(v_in - v_out)

    RH is computed from v and T using the paper's Eq.(12).
    """
    V = geom.volume
    A_floor = geom.floor_area
    A_crop = crop_area_m2 if crop_area_m2 is not None else A_floor

    # Outside absolute humidity (paper Eq. 12–13)
    v_out = abs_humidity_from_rh(outside.T_out_c, outside.RH_out_pct)

    # Initial inside absolute humidity
    T_in = inside0.T_in_c
    v_in = abs_humidity_from_rh(inside0.T_in_c, inside0.RH_in_pct)

    # Ventilation flow
    Vdot = act.ACH * V / 3600.0                 # m^3/s
    mdot = air.rho * Vdot                       # kg/s

    # Gains
    Q_solar = act.tau_alpha * outside.G_sun_w_m2 * A_floor  # W
    Q_heater = act.Q_heater_w

    # Transpiration moisture source (kg/s)
    m_trans = (act.transp_g_m2_h / 1000.0) / 3600.0 * A_crop

    steps = int(minutes * 60.0 / dt_s)
    rows: List[Dict[str, float]] = []

    for k in range(steps + 1):
        t_min = (k * dt_s) / 60.0
        RH_in = rh_from_abs_humidity(T_in, v_in)

        rows.append({
            "t_min": t_min,
            "Tin_C": T_in,
            "RHin_pct": RH_in,
            "vin_g_m3": v_in * 1000.0,
            "Tout_C": outside.T_out_c,
            "RHout_pct": outside.RH_out_pct,
            "vout_g_m3": v_out * 1000.0,
        })

        if k == steps:
            break

        # --- Energy balance ---
        Q_env = act.UA_w_k * (outside.T_out_c - T_in)         # W
        Q_vent = mdot * air.cp * (outside.T_out_c - T_in)     # W
        dTdt = (Q_env + Q_vent + Q_solar + Q_heater) / (air.rho * air.cp * V)
        T_in = T_in + dTdt * dt_s

        # --- Moisture balance ---
        dvdt = (m_trans / V) - (Vdot / V) * (v_in - v_out)
        v_in = v_in + dvdt * dt_s

    return rows


def main() -> None:
    # --- Numerical example (same as earlier) ---
    geom = Geometry(L=20.0, W=10.0, H=4.0)

    outside = Outside(
        T_out_c=-10.0,      # given
        RH_out_pct=70.0,    # chosen
        G_sun_w_m2=150.0,   # chosen
    )

    inside0 = InsideInitial(
        T_in_c=15.0,        # given
        RH_in_pct=60.0,     # chosen
    )

    act = Actuation(
        ACH=2.0,             # chosen
        UA_w_k=250.0,         # chosen (lumped insulation)
        Q_heater_w=10_000.0,  # chosen
        tau_alpha=0.45,       # chosen
        transp_g_m2_h=50.0,   # chosen
    )

    rows = simulate_10min(
        geom=geom,
        outside=outside,
        inside0=inside0,
        act=act,
        dt_s=60.0,
        minutes=10,
    )

    # Print a compact table
    print("t(min)\tTin(°C)\tRH(%)\tvin(g/m³)\tvout(g/m³)")
    for r in rows:
        print(
            f"{r['t_min']:>5.0f}\t"
            f"{r['Tin_C']:>7.3f}\t"
            f"{r['RHin_pct']:>6.2f}\t"
            f"{r['vin_g_m3']:>8.3f}\t"
            f"{r['vout_g_m3']:>8.3f}"
        )


if __name__ == "__main__":
    main()