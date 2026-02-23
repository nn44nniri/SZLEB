from .models import (
    Geometry, Outside, Initial, AirProps,
    CouplingParams, BuildingParams, BaselinePlantParams
)
from .actuators import (
    ActuatorCommand, ActuatorSet, ActuatorMapping, resolve_actuation
)
from .simulator import simulate

def estimate_environment(
    *,
    geom: Geometry,
    outside: Outside,
    init: Initial,
    building: BuildingParams,
    coupling: CouplingParams,
    # actuator inputs:
    vents_on: bool,
    vents_activity_pct: float,
    vents_active_time_s: float,
    fans_on: bool,
    fans_activity_pct: float,
    fans_active_time_s: float,
    heater_on: bool,
    heater_activity_pct: float,
    heater_active_time_s: float,
    elapsed_s: float,
    dt_s: float = 60.0,
    crop_area_m2: float | None = None,
    mapping: ActuatorMapping = ActuatorMapping(),
) -> dict:
    """
    One-call API:
      - Set ON/OFF, activity (0..100), active time (s) for vents/fans/heater
      - Returns FINAL-only outputs (no time-series)

    Note: actuator->(ACH,Q_heater) mapping is a practical wrapper. The physics
    equations used inside simulate() keep the same structural logic.
    """
    from .actuators import ActuatorCommand, ActuatorSet, resolve_actuation
    from .models import ActuationResolved

    actuators = ActuatorSet(
        vents=ActuatorCommand(vents_on, vents_activity_pct, vents_active_time_s),
        fans=ActuatorCommand(fans_on, fans_activity_pct, fans_active_time_s),
        heater=ActuatorCommand(heater_on, heater_activity_pct, heater_active_time_s),
    )

    ACH, Q_heater_w, dbg, energy = resolve_actuation(
        actuators, elapsed_s=elapsed_s, mapping=mapping
    )

    act = ActuationResolved(
        ACH=ACH,
        Q_heater_w=Q_heater_w,
        heater_gas_m3_h=energy["heater_gas_m3_h"],
        heater_elec_w=energy["heater_elec_w"],
        cooling_elec_w=energy["cooling_elec_w"],
        vents_elec_w=energy["vents_elec_w"],
    )

    out = simulate(
        geom=geom,
        outside=outside,
        init=init,
        building=building,
        act=act,
        coup=coupling,
        crop_area_m2=crop_area_m2,
        dt_s=dt_s,
        elapsed_s=elapsed_s,
    )
    out["actuator_mapping_debug"] = dbg
    return out
