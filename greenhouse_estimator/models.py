from __future__ import annotations
from dataclasses import dataclass

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
class BaselinePlantParams:
    """Tuning/lumped parameters used in the canopy energy balance (kept same logic as before)."""
    C_can_areal: float = 30_000.0  # J/(m^2*K) effective canopy thermal mass

@dataclass(frozen=True)
class BuildingParams:
    """Envelope/solar parameters (same role as before)."""
    UA_w_k: float              # W/K (envelope/insulation lumped)
    tau_alpha_air: float       # fraction of solar into air node
    tau_alpha_can: float       # fraction of solar into canopy node

@dataclass(frozen=True)
class ActuationResolved:
    """Resolved physical actuation parameters used by the simulator."""
    ACH: float           # 1/h (airflow proxy)
    Q_heater_w: float    # W thermal to air

    # New: instantaneous energy consumption rates for bookkeeping/output
    heater_gas_m3_h: float = 0.0
    heater_elec_w: float = 0.0
    cooling_elec_w: float = 0.0
    vents_elec_w: float = 0.0
