from __future__ import annotations

import math
from typing import List, Dict, Optional

from .psychrometrics import (
    abs_humidity_from_rh,
    rh_from_abs_humidity,
    vapor_pressure_from_abs_humidity,
    es_magnus_tetens_pa,
)
from .models import (
    Geometry, Outside, Initial, AirProps, CouplingParams,
    BaselinePlantParams, BuildingParams, ActuationResolved
)

# -----------------------------
# Trigger labelling (descriptive)
# -----------------------------
def build_trigger_string(
    ACH: float,
    Q_heater_w: float,
    G_sun_w_m2: float,
    LAI: float,
    A_crop: float,
    Q_trans_W: float,
) -> str:
    """
    Purely descriptive flags; no control logic changes.
    - heater_active: Q_heater_w > 0
    - solar_active: G_sun_w_m2 > 0
    - ventilation_active: ACH > 0
    - transpiration_active: Q_trans_W > 0
    - canopy_convection_active: LAI > 0 (implies h=10LAI) and A_crop > 0
    """
    flags = []
    if Q_heater_w > 0:
        flags.append("heater")
    if G_sun_w_m2 > 0:
        flags.append("solar")
    if ACH > 0:
        flags.append("ventilation")
    if Q_trans_W > 0:
        flags.append("transpiration")
    if LAI > 0 and A_crop > 0:
        flags.append("canopy_convection(h=10LAI)")
    return "|".join(flags) if flags else "none"


# -----------------------------
# Core coupled simulation (same structural logic)
# -----------------------------
def simulate(
    geom: Geometry,
    outside: Outside,
    init: Initial,
    building: BuildingParams,
    act: ActuationResolved,
    coup: CouplingParams,
    plant: BaselinePlantParams = BaselinePlantParams(),
    air: AirProps = AirProps(),
    crop_area_m2: Optional[float] = None,
    dt_s: float = 60.0,
    elapsed_s: float = 600.0,
) -> Dict[str, object]:
    """
    Returns:
      - rows: time series table
      - airflow_final_m3_s, airflow_avg_m3_s
      - ach_final_1_h, ach_avg_1_h
      - Tin_final_C, RHin_final_pct, Tout_C
    """
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

    steps = int(elapsed_s / dt_s)
    # Energy accumulators (new)
    heater_gas_total_m3 = 0.0
    heater_elec_total_kwh = 0.0
    cooling_elec_total_kwh = 0.0
    vents_elec_total_kwh = 0.0
    rows: List[Dict[str, float | str]] = []

    # For "final and average air flow"
    airflow_series_m3_s: List[float] = []
    ach_series: List[float] = []

    for k in range(steps + 1):
        t_min = (k * dt_s) / 60.0

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
        Q_env_W = building.UA_w_k * (outside.T_out_c - T_air)
        Q_vent_sens_W = mdot * air.cp * (outside.T_out_c - T_air)
        Q_solar_air_W = building.tau_alpha_air * outside.G_sun_w_m2 * geom.A_floor

        dTair_dt = (Q_env_W + Q_vent_sens_W + act.Q_heater_w + Q_solar_air_W + Q_conv_can_to_air_W) / (air.rho * air.cp * V)
        T_air = T_air + dTair_dt * dt_s

        # Energy balance (canopy)
        Q_solar_can_W = building.tau_alpha_can * outside.G_sun_w_m2 * geom.A_floor
        dTcan_dt = (Q_solar_can_W - Q_conv_can_to_air_W - Q_trans_W) / (plant.C_can_areal * A_crop)
        T_can = T_can + dTcan_dt * dt_s

        RH_air = rh_from_abs_humidity(T_air, v_air)

        triggers = build_trigger_string(
            ACH=act.ACH,
            Q_heater_w=act.Q_heater_w,
            G_sun_w_m2=outside.G_sun_w_m2,
            LAI=coup.LAI,
            A_crop=A_crop,
            Q_trans_W=Q_trans_W,
        )

        # airflow series
        airflow_series_m3_s.append(Vdot)
        ach_series.append(act.ACH)
        # --- Per-step actuator energy bookkeeping (new) ---
        dt_h = dt_s / 3600.0

        heater_gas_m3_step = act.heater_gas_m3_h * dt_h
        heater_elec_kwh_step = (act.heater_elec_w / 1000.0) * dt_h
        cooling_elec_kwh_step = (act.cooling_elec_w / 1000.0) * dt_h
        vents_elec_kwh_step = (act.vents_elec_w / 1000.0) * dt_h
        dt_h = dt_s / 3600.0

        # Step consumptions (already activity-scaled because act.* values are activity-scaled)
        heater_gas_m3_step = act.heater_gas_m3_h * dt_h
        heater_elec_kwh_step = (act.heater_elec_w / 1000.0) * dt_h
        cooling_elec_kwh_step = (act.cooling_elec_w / 1000.0) * dt_h
        vents_elec_kwh_step = (act.vents_elec_w / 1000.0) * dt_h

        # Running totals (cumulative up to current timestep)

        heater_gas_total_m3 += heater_gas_m3_step
        heater_elec_total_kwh += heater_elec_kwh_step
        cooling_elec_total_kwh += cooling_elec_kwh_step
        vents_elec_total_kwh += vents_elec_kwh_step
        rows.append({
            "t_min": t_min,
            "Tout_C": outside.T_out_c,
            "Tair_C": T_air,
            "RH_air_pct": RH_air,
            "Triggers": triggers,
            "airflow_m3_s": Vdot,
            "ACH_1_h": act.ACH,

            # Optional: instantaneous rates (can keep for diagnostics)
            "heater_thermal_w": act.Q_heater_w,
            "heater_gas_m3_h_rate": act.heater_gas_m3_h,
            "heater_elec_w_rate": act.heater_elec_w,
            "cooling_elec_w_rate": act.cooling_elec_w,
            "vents_elec_w_rate": act.vents_elec_w,

            # Per-step consumption (optional)
            "heater_gas_m3_step": heater_gas_m3_step,
            "heater_elec_kwh_step": heater_elec_kwh_step,
            "cooling_elec_kwh_step": cooling_elec_kwh_step,
            "vents_elec_kwh_step": vents_elec_kwh_step,

            # REQUIRED: cumulative consumption up to current step
            "heater_gas_m3_cum": heater_gas_total_m3,
            "heater_elec_kwh_cum": heater_elec_total_kwh,
            "cooling_elec_kwh_cum": cooling_elec_total_kwh,
            "vents_elec_kwh_cum": vents_elec_total_kwh,

            # Optional combined cumulative values
            "cooling_total_elec_kwh_cum": cooling_elec_total_kwh + vents_elec_total_kwh,
            "total_elec_kwh_cum": heater_elec_total_kwh + cooling_elec_total_kwh + vents_elec_total_kwh,
        })

    airflow_final_m3_s = airflow_series_m3_s[-1] if airflow_series_m3_s else 0.0
    airflow_avg_m3_s = sum(airflow_series_m3_s) / len(airflow_series_m3_s) if airflow_series_m3_s else 0.0

    ach_final = ach_series[-1] if ach_series else 0.0
    ach_avg = sum(ach_series) / len(ach_series) if ach_series else 0.0

    return {
        "rows": rows,
        "Tout_C": outside.T_out_c,
        "Tin_final_C": T_air,
        "RHin_final_pct": RH_air,
        "airflow_final_m3_s": airflow_final_m3_s,
        "airflow_avg_m3_s": airflow_avg_m3_s,
        "ach_final_1_h": ach_final,
        "ach_avg_1_h": ach_avg,
        "heater_gas_total_m3": heater_gas_total_m3,
        "heater_elec_total_kwh": heater_elec_total_kwh,
        "cooling_elec_total_kwh": cooling_elec_total_kwh,
        "vents_elec_total_kwh": vents_elec_total_kwh,
        "total_elec_kwh": heater_elec_total_kwh + cooling_elec_total_kwh + vents_elec_total_kwh,
    }
