from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ActuatorCommand:
    """
    Generic actuator command:
    - on: True/False
    - activity_pct: 0..100
    - active_time_s: active duration during the elapsed window (seconds)
    """
    on: bool
    activity_pct: float
    active_time_s: float

    def duty(self, elapsed_s: float) -> float:
        if elapsed_s <= 0:
            return 0.0
        return max(0.0, min(1.0, self.active_time_s / elapsed_s))

    def activity01(self) -> float:
        return max(0.0, min(1.0, self.activity_pct / 100.0))

@dataclass(frozen=True)
class ActuatorSet:
    vents: ActuatorCommand
    fans: ActuatorCommand
    heater: ActuatorCommand

@dataclass(frozen=True)
class ActuatorMapping:
    """
    Maps actuator setpoints -> model parameters.
    Practical knobs (not paper-identical) to preserve simulator structure.

    Physics-facing:
      - ACH from vents/fans
      - heater thermal power Q_heater_w

    Energy-facing (new):
      - heater gas consumption (m^3/h)
      - heater electricity (auxiliary, W)
      - cooling electricity (fans, W)
      - optional vents actuator electricity (W)
    """
    # Existing airflow / thermal mapping
    base_ach_vents: float = 3.0      # ACH at 100% vents, 100% duty
    base_ach_fans: float = 6.0       # ACH at 100% fans, 100% duty
    heater_max_w: float = 20_000.0   # W thermal to air at 100% heater, 100% duty

    # New energy consumption mappings (adjustable)
    heater_max_gas_m3_h: float = 2.5     # m^3/h natural gas at 100% heater
    heater_aux_elec_max_w: float = 300.0 # W electrical auxiliaries for heater (controls/pump/ignition fan)
    cooling_fans_max_elec_w: float = 1500.0  # W fan electricity at 100% fans
    vents_motor_max_elec_w: float = 0.0      # W vent motor electricity (optional; set >0 if used)

def resolve_actuation(
    actuators: ActuatorSet,
    elapsed_s: float,
    mapping: ActuatorMapping = ActuatorMapping(),
):
    """
    Returns (ACH, Q_heater_w, debug_dict, energy_dict).

    ACH combines vents + fans; heater maps to Q_heater_w.
    energy_dict contains per-actuator instantaneous rates used for bookkeeping.
    """
    v_on = 1.0 if actuators.vents.on else 0.0
    f_on = 1.0 if actuators.fans.on else 0.0
    h_on = 1.0 if actuators.heater.on else 0.0

    v_eff = v_on * actuators.vents.activity01() * actuators.vents.duty(elapsed_s)
    f_eff = f_on * actuators.fans.activity01() * actuators.fans.duty(elapsed_s)
    h_eff = h_on * actuators.heater.activity01() * actuators.heater.duty(elapsed_s)

    # Existing physics-facing outputs
    ACH = mapping.base_ach_vents * v_eff + mapping.base_ach_fans * f_eff
    Q_heater_w = mapping.heater_max_w * h_eff

    # New energy-facing outputs (instantaneous rates)
    heater_gas_m3_h = mapping.heater_max_gas_m3_h * h_eff
    heater_elec_w = mapping.heater_aux_elec_max_w * h_eff
    cooling_elec_w = mapping.cooling_fans_max_elec_w * f_eff
    vents_elec_w = mapping.vents_motor_max_elec_w * v_eff

    dbg = {
        "vents_effective_0to1": v_eff,
        "fans_effective_0to1": f_eff,
        "heater_effective_0to1": h_eff,
        "ACH": ACH,
        "Q_heater_w": Q_heater_w,
    }

    energy = {
        "heater_gas_m3_h": heater_gas_m3_h,
        "heater_elec_w": heater_elec_w,
        "cooling_elec_w": cooling_elec_w,  # cooling actuator = fans in this SZLEB abstraction
        "vents_elec_w": vents_elec_w,
        "total_elec_w": heater_elec_w + cooling_elec_w + vents_elec_w,
    }

    return ACH, Q_heater_w, dbg, energy