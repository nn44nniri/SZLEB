# main_example.py
# 300-minute+ run, heater + vents example
# Adds 4 graphs on ONE page: ΔTin, ΔRH, Airflow (m³/s), Wind speed (m/s)

from greenhouse_estimator import (
    Geometry, Outside, Initial, BuildingParams, CouplingParams,
    estimate_environment, ActuatorMapping
)
import matplotlib.pyplot as plt

def main() -> None:
    # Scenario
    geom = Geometry(L=20.0, W=10.0, H=4.0)
    outside = Outside(T_out_c=-10.0, RH_out_pct=70.0, G_sun_w_m2=150.0)
    init = Initial(T_air_c=15.0, RH_air_pct=60.0, T_canopy_c=15.0)

    building = BuildingParams(
        UA_w_k=250.0,
        tau_alpha_air=0.25,
        tau_alpha_can=0.20,
    )
    coupling = CouplingParams(LAI=2.0)

    # minutes elapsed
    elapsed_s = 2001 * 60  # 24 hours, as in your code

    mapping = ActuatorMapping(
        base_ach_vents=3.0,
        base_ach_fans=6.0,
        heater_max_w=20_000.0,          # thermal output to air (physics side)

        # Energy tuning (new)
        heater_max_gas_m3_h=2.8,        # gas consumption at 100% heater
        heater_aux_elec_max_w=250.0,    # heater auxiliary electricity
        cooling_fans_max_elec_w=1800.0, # cooling fans electricity
        vents_motor_max_elec_w=80.0,    # optional vent actuator motor
    )
    result = estimate_environment(
        geom=geom,
        outside=outside,
        init=init,
        building=building,
        coupling=coupling,
        mapping=mapping,
        # vents ON
        vents_on=False,
        vents_activity_pct=10.0,
        vents_active_time_s=elapsed_s,

        # fans OFF
        fans_on=True,
        fans_activity_pct=5.0,
        fans_active_time_s=elapsed_s,

        # heater ON
        heater_on=True,
        heater_activity_pct=100.0,
        heater_active_time_s=elapsed_s,

        elapsed_s=elapsed_s,
        dt_s=60.0,
    )

    print(f"=== Summary ({elapsed_s} seconds) ===")
    print(f"Tout (°C): {result['Tout_C']:.2f}")
    print(f"Tin final (°C): {result['Tin_final_C']:.2f}")
    print(f"RH final (%): {result['RHin_final_pct']:.2f}")
    print(f"Airflow final (m³/s): {result['airflow_final_m3_s']:.4f}")
    print(f"Airflow avg   (m³/s): {result['airflow_avg_m3_s']:.4f}")
    print(f"ACH final (1/h): {result['ach_final_1_h']:.3f}")
    print(f"ACH avg   (1/h): {result['ach_avg_1_h']:.3f}")
    print("Actuator mapping debug:", result["actuator_mapping_debug"])
    print(f"Heater gas total (m³): {result['heater_gas_total_m3']:.4f}")
    print(f"Heater electricity total (kWh): {result['heater_elec_total_kwh']:.4f}")
    print(f"Cooling electricity total (kWh): {result['cooling_elec_total_kwh']:.4f}")
    print(f"Vents electricity total (kWh): {result['vents_elec_total_kwh']:.4f}")
    print(f"Total electricity (kWh): {result['total_elec_kwh']:.4f}")
    # --- Build vectors from the returned time-series ---
    rows = result["rows"]
    
    t = [r["t_min"] for r in rows]
    Tin = [r["Tair_C"] for r in rows]
    RH = [r["RH_air_pct"] for r in rows]
    airflow = [r.get("airflow_m3_s", 0.0) for r in rows]  # already in each row

    # --- Wind speed proxy (simple, derived from airflow) ---
    # NOTE: This is a proxy since the current simulator is single-zone and does not
    # explicitly simulate wind velocity fields. We estimate mean velocity at a
    # representative opening area A_open.
    A_open = 2.0  # m^2 (choose a representative effective opening area)
    wind_speed = [(q / A_open) if A_open > 0 else 0.0 for q in airflow]  # m/s

    # --- "Amount of change" relative to the initial (t=0) values ---
    Tin0 = Tin[0]
    RH0 = RH[0]
    dTin = [x - Tin0 for x in Tin]
    dRH = [x - RH0 for x in RH]
    # Example: print first 3 rows of actuator energy bookkeeping
    r = result["rows"][-1]
    print({
        "t_min": r["t_min"],

        # cumulative values (preferred)
        "heater_gas_m3_cum": r.get("heater_gas_m3_cum", None),
        "heater_elec_kwh_cum": r.get("heater_elec_kwh_cum", None),
        "cooling_elec_kwh_cum": r.get("cooling_elec_kwh_cum", None),
        "vents_elec_kwh_cum": r.get("vents_elec_kwh_cum", None),
        "total_elec_kwh_cum": r.get("total_elec_kwh_cum", None),

        # optional diagnostics (if present)
        "heater_gas_m3_h_rate": r.get("heater_gas_m3_h_rate", r.get("heater_gas_m3_h", None)),
        "heater_gas_m3_step": r.get("heater_gas_m3_step", None),
        "heater_elec_kwh_step": r.get("heater_elec_kwh_step", None),
        "cooling_elec_kwh_step": r.get("cooling_elec_kwh_step", None),
    })
    # --- 4 graphs on one page (no color specified) ---
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    # 1) ΔTin
    axs[0, 0].plot(t, dTin)
    axs[0, 0].set_title("ΔTin (°C) from t=0")
    axs[0, 0].set_xlabel("Time (min)")
    axs[0, 0].set_ylabel("ΔTin (°C)")
    axs[0, 0].grid(True)

    # 2) ΔRH
    axs[0, 1].plot(t, dRH)
    axs[0, 1].set_title("ΔRH (%) from t=0")
    axs[0, 1].set_xlabel("Time (min)")
    axs[0, 1].set_ylabel("ΔRH (%)")
    axs[0, 1].grid(True)

    # 3) Airflow
    axs[1, 0].plot(t, airflow)
    axs[1, 0].set_title("Airflow (m³/s)")
    axs[1, 0].set_xlabel("Time (min)")
    axs[1, 0].set_ylabel("m³/s")
    axs[1, 0].grid(True)

    # 4) Wind speed (proxy)
    axs[1, 1].plot(t, wind_speed)
    axs[1, 1].set_title("Wind speed (m/s) [proxy from airflow/A_open]")
    axs[1, 1].set_xlabel("Time (min)")
    axs[1, 1].set_ylabel("m/s")
    axs[1, 1].grid(True)

    fig.suptitle(f"Greenhouse signals (0–{elapsed_s/60:.0f} minutes)", fontsize=14)
    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
