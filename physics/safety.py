"""
VoltGuard Physics Engine — Safety Analysis

Converts raw predicted physical values into a safety classification,
a normalized risk score, violation details, and a human-readable explanation.

No equations live here — only classification logic.
"""

from __future__ import annotations

from typing import List, Tuple

from physics.models import SafetyState, ViolationDetail


# ---------------------------------------------------------------------------
# Safety thresholds (as a fraction of the configured limit)
# ---------------------------------------------------------------------------

# Below this ratio → SAFE
SAFE_THRESHOLD: float = 0.70

# At or above this ratio → WARNING (but below CRITICAL)
WARNING_THRESHOLD: float = 0.70

# At or above this ratio → CRITICAL (but below limit)
CRITICAL_THRESHOLD: float = 0.90

# At or above 1.0 → CATASTROPHIC (limit exceeded)


def _ratio(value: float, limit: float) -> float:
    """Return value / limit. Handles limit == 0 by returning 0."""
    if limit <= 0.0:
        return 0.0
    return value / limit


def _classify_single(ratio: float) -> SafetyState:
    """Classify one parameter's ratio against its limit."""
    if ratio >= 1.0:
        return SafetyState.CATASTROPHIC
    if ratio >= CRITICAL_THRESHOLD:
        return SafetyState.CRITICAL
    if ratio >= WARNING_THRESHOLD:
        return SafetyState.WARNING
    return SafetyState.SAFE


def _state_severity(state: SafetyState) -> int:
    """Return an integer severity so the worst state can be found easily."""
    order = {
        SafetyState.SAFE: 0,
        SafetyState.WARNING: 1,
        SafetyState.CRITICAL: 2,
        SafetyState.CATASTROPHIC: 3,
    }
    return order[state]


def compute_violations(
    pump_rpm: float,
    predicted_flow: float,
    predicted_pressure: float,
    predicted_temperature: float,
    system_stress: float,
    rpm_limit: float,
    flow_limit: float,
    pressure_limit: float,
    temperature_limit: float,
    stress_limit: float,
) -> Tuple[List[ViolationDetail], SafetyState]:
    """
    Evaluate every physical parameter against its configured limit.

    Returns:
        violations: List of ViolationDetail for parameters that are
                    in WARNING, CRITICAL, or CATASTROPHIC state.
        worst_state: The most severe SafetyState across all parameters.
    """
    checks: List[Tuple[str, float, float, str]] = [
        ("pump_rpm",             pump_rpm,             rpm_limit,         "Pump RPM"),
        ("predicted_flow",       predicted_flow,        flow_limit,        "Flow rate"),
        ("predicted_pressure",   predicted_pressure,    pressure_limit,    "Pipeline pressure"),
        ("predicted_temperature",predicted_temperature, temperature_limit, "Fluid temperature"),
        ("system_stress",        system_stress,         stress_limit,      "Pipeline hoop stress"),
    ]

    violations: List[ViolationDetail] = []
    worst_state = SafetyState.SAFE

    for param, value, limit, label in checks:
        ratio = _ratio(value, limit)
        state = _classify_single(ratio)

        if _state_severity(state) > _state_severity(worst_state):
            worst_state = state

        if state != SafetyState.SAFE:
            if ratio >= 1.0:
                pct_over = (ratio - 1.0) * 100.0
                desc = (
                    f"{label} exceeds the safety limit by {pct_over:.1f}% "
                    f"({value:.2f} vs limit {limit:.2f})."
                )
            else:
                pct_of = ratio * 100.0
                desc = (
                    f"{label} is at {pct_of:.1f}% of its safety limit "
                    f"({value:.2f} vs limit {limit:.2f})."
                )
            violations.append(
                ViolationDetail(
                    parameter=param,
                    value=round(value, 4),
                    limit=round(limit, 4),
                    ratio=round(ratio, 6),
                    description=desc,
                )
            )

    return violations, worst_state


def compute_risk_score(
    pump_rpm: float,
    predicted_flow: float,
    predicted_pressure: float,
    predicted_temperature: float,
    system_stress: float,
    rpm_limit: float,
    flow_limit: float,
    pressure_limit: float,
    temperature_limit: float,
    stress_limit: float,
) -> float:
    """
    Compute a normalized risk score in [0, 100].

    Method:
        For each parameter, compute ratio = value / limit.
        Map ratio to a score component using a clamped quadratic scale:
            score_i = min(ratio, 1.5)² / 1.5² × 100
        This causes:
            ratio = 0.0  → score  0
            ratio = 0.70 → score ~22  (WARNING boundary)
            ratio = 0.90 → score ~36  (CRITICAL boundary)
            ratio = 1.0  → score ~44
            ratio = 1.5  → score 100  (hard cap)
        The final risk score is the maximum score across all parameters,
        so the worst violation drives the result.

    Returns:
        risk_score: float in [0.0, 100.0]
    """
    MAX_RATIO_CAP = 1.5  # beyond this, score saturates at 100

    ratios = [
        _ratio(pump_rpm,              rpm_limit),
        _ratio(predicted_flow,        flow_limit),
        _ratio(predicted_pressure,    pressure_limit),
        _ratio(predicted_temperature, temperature_limit),
        _ratio(system_stress,         stress_limit),
    ]

    def ratio_to_score(r: float) -> float:
        capped = min(r, MAX_RATIO_CAP)
        return (capped / MAX_RATIO_CAP) ** 2 * 100.0

    scores = [ratio_to_score(r) for r in ratios]
    return round(min(max(scores), 100.0), 2)


def build_explanation(violations: List[ViolationDetail], safety_state: SafetyState) -> str:
    """
    Build a human-readable explanation string for the simulation result.

    This string is designed to be shown directly in the dashboard and
    used in security event logs.

    Args:
        violations:    List of ViolationDetail objects from compute_violations().
        safety_state:  Overall SafetyState classification.

    Returns:
        A clear English sentence describing the system state.
    """
    if safety_state == SafetyState.SAFE:
        return "All physical parameters are within safe operating limits."

    if not violations:
        # Should not happen — but defensive fallback
        return f"System state is {safety_state.value}. No specific parameter data available."

    if len(violations) == 1:
        v = violations[0]
        if v.ratio >= 1.0:
            pct = (v.ratio - 1.0) * 100.0
            return (
                f"ALERT: {v.description} "
                f"Safety limit exceeded by {pct:.1f}%. Immediate action required."
            )
        return f"CAUTION: {v.description}"

    # Multiple violations
    param_names = ", ".join(v.parameter.replace("_", " ") for v in violations)
    exceeded = [v for v in violations if v.ratio >= 1.0]

    if exceeded:
        exceeded_names = ", ".join(v.parameter.replace("_", " ") for v in exceeded)
        return (
            f"CRITICAL ALERT: Multiple physical safety constraints violated. "
            f"Parameters exceeding limits: {exceeded_names}. "
            f"All affected parameters: {param_names}. Immediate shutdown recommended."
        )

    return (
        f"WARNING: Multiple physical parameters approaching safety limits: {param_names}. "
        f"Monitor closely and prepare for controlled shutdown."
    )
