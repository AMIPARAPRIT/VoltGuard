"""
VoltGuard Physics Engine — Pure Equation Functions

All functions here are pure mathematics with no side effects,
no imports from config, and no logging. They take explicit
numeric parameters and return floats.

PROTOTYPE DISCLAIMER:
    This is a simplified model for demonstration purposes only.
    It does NOT represent a calibrated real-world hydraulic system.

Assumptions:
    1. Centrifugal pump: flow scales linearly with normalized RPM.
    2. Valve: flow scales linearly with fractional opening (0–1).
    3. Pressure rise is quadratic in flow (Darcy-Weisbach head-loss concept).
    4. Fluid temperature rises linearly with flow above the inlet temperature.
    5. Pipeline hoop stress is proportional to internal predicted pressure.

Units (consistent throughout):
    pressure    → bar
    flow        → L/min
    rpm         → RPM
    temperature → °C
    stress      → MPa
"""

from __future__ import annotations


def compute_flow(
    pump_rpm: float,
    valve_position: float,
    reference_rpm: float,
    base_flow: float,
    pump_efficiency: float,
) -> float:
    """
    Predict volumetric flow rate (L/min).

    Model:
        valve_factor    = valve_position / 100
        normalized_rpm  = pump_rpm / reference_rpm
        flow            = base_flow × normalized_rpm × valve_factor × pump_efficiency

    Args:
        pump_rpm:        Current pump speed (RPM).
        valve_position:  Valve opening (0–100 %).
        reference_rpm:   RPM at which base_flow is calibrated.
        base_flow:       Nominal flow at reference_rpm, fully open valve, 100% eff.
        pump_efficiency: Mechanical efficiency fraction (0–1].

    Returns:
        Predicted flow rate in L/min (≥ 0).
    """
    valve_factor = valve_position / 100.0
    normalized_rpm = pump_rpm / reference_rpm
    flow = base_flow * normalized_rpm * valve_factor * pump_efficiency
    return max(flow, 0.0)  # flow cannot be negative


def compute_pressure(
    current_pressure: float,
    flow: float,
    pipeline_resistance: float,
    pressure_gain_coefficient: float,
    pressure_loss_coefficient: float,
) -> float:
    """
    Predict outlet pressure (bar).

    Model (simplified quasi-steady-state):
        pressure_rise = pressure_gain_coefficient × flow² × pipeline_resistance
        pressure_loss = pressure_loss_coefficient × flow × pipeline_resistance
        predicted     = current_pressure + pressure_rise - pressure_loss

    The quadratic rise term dominates at high flow, ensuring the system
    approaches and exceeds the safety limit under attack conditions.

    Args:
        current_pressure:            Inlet/baseline pressure (bar, ≥ 0).
        flow:                        Predicted flow rate (L/min).
        pipeline_resistance:         Dimensionless resistance coefficient.
        pressure_gain_coefficient:   bar / (L/min)².
        pressure_loss_coefficient:   bar / (L/min) / resistance unit.

    Returns:
        Predicted pressure in bar (≥ 0).
    """
    pressure_rise = pressure_gain_coefficient * (flow ** 2) * pipeline_resistance
    pressure_loss = pressure_loss_coefficient * flow * pipeline_resistance
    predicted = current_pressure + pressure_rise - pressure_loss
    return max(predicted, 0.0)


def compute_temperature(
    current_temperature: float,
    flow: float,
    thermal_gain_coefficient: float,
) -> float:
    """
    Predict fluid temperature (°C).

    Model:
        delta_T = thermal_gain_coefficient × flow
        predicted_temperature = current_temperature + delta_T

    Higher flow carries more energy and raises fluid temperature.

    Args:
        current_temperature:     Inlet fluid temperature (°C).
        flow:                    Predicted flow rate (L/min).
        thermal_gain_coefficient: °C per L/min.

    Returns:
        Predicted temperature in °C.
    """
    delta_t = thermal_gain_coefficient * flow
    return current_temperature + delta_t


def compute_stress(
    predicted_pressure: float,
    stress_per_bar: float,
) -> float:
    """
    Predict pipeline hoop stress (MPa).

    Model:
        stress = predicted_pressure × stress_per_bar

    Hoop stress in a thin-walled cylinder is proportional to internal pressure.
    The coefficient stress_per_bar encapsulates pipe geometry (radius/wall thickness).

    Args:
        predicted_pressure: Internal pressure (bar).
        stress_per_bar:     MPa of hoop stress per bar of pressure.

    Returns:
        Predicted hoop stress in MPa (≥ 0).
    """
    return max(predicted_pressure * stress_per_bar, 0.0)
