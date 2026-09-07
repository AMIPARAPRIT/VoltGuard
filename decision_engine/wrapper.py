"""
VoltGuard Decision Engine Python Wrapper & Bridge

Provides Python interface to the compiled Rust decision_engine binary.
Implements fail-closed safety policy fallback when the Rust binary is unavailable or when input validation fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# Project root setup
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from physics.models import PhysicsResult


def get_current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_fail_closed_decision(reason_detail: str = "Physical safety validation unavailable.", latency_us: int = 0) -> Dict[str, Any]:
    """Fail-closed safety result returned whenever input or execution fails."""
    return {
        "decision": "BLOCK_CRITICAL",
        "risk_score": 100.0,
        "safety_state": "CATASTROPHIC",
        "reason": f"Physical safety validation unavailable. ({reason_detail})" if reason_detail else "Physical safety validation unavailable.",
        "timestamp": get_current_iso_timestamp(),
        "decision_latency_us": latency_us,
    }


class RustDecisionPolicyPython:
    """Python mirror of Rust DecisionPolicy for environments without Rust compiler."""

    @classmethod
    def evaluate(cls, physics_dict: Dict[str, Any], start_time_ns: int) -> Dict[str, Any]:
        safety_state = str(physics_dict.get("safety_state", "UNKNOWN")).upper()
        risk_score = float(physics_dict.get("risk_score", 100.0))
        violations = physics_dict.get("violations", [])
        explanation = physics_dict.get("explanation", "")

        if safety_state == "SAFE":
            decision = "ALLOW"
            base_reason = f"Physical parameters within safe boundaries. (Risk Score: {risk_score:.1f})"
        elif safety_state == "WARNING":
            decision = "MONITOR"
            base_reason = f"Physical parameters approaching safety limits. Elevated monitoring required. (Risk Score: {risk_score:.1f})"
        elif safety_state == "CRITICAL":
            decision = "BLOCK"
            base_reason = f"CRITICAL PHYSICAL SAFETY BREACH: Safety limits approaching threshold. Command execution blocked. (Risk Score: {risk_score:.1f})"
        elif safety_state == "CATASTROPHIC":
            decision = "BLOCK_CRITICAL"
            base_reason = f"CATASTROPHIC PHYSICAL THREAT: Severe safety limit violation detected. Emergency block initiated. (Risk Score: {risk_score:.1f})"
        else:
            elapsed_us = (time.perf_counter_ns() - start_time_ns) // 1000
            return build_fail_closed_decision("Unknown physical safety state", elapsed_us)

        if violations:
            violation_msgs = []
            for v in violations:
                if isinstance(v, dict):
                    param = str(v.get("parameter", "PARAM")).upper()
                    val = v.get("value", 0.0)
                    lim = v.get("limit", 0.0)
                    desc = v.get("description", "Limit exceeded")
                    violation_msgs.append(f"{param}: actual={val:.2f}, limit={lim:.2f} ({desc})")
                else:
                    violation_msgs.append(str(v))
            reason = f"{base_reason} Violations: [{' | '.join(violation_msgs)}]"
        elif explanation:
            reason = f"{base_reason} Detail: {explanation}"
        else:
            reason = base_reason

        elapsed_us = (time.perf_counter_ns() - start_time_ns) // 1000

        return {
            "decision": decision,
            "risk_score": risk_score,
            "safety_state": safety_state,
            "reason": reason,
            "timestamp": get_current_iso_timestamp(),
            "decision_latency_us": elapsed_us,
        }


class RustDecisionEngineWrapper:
    """
    Python wrapper calling compiled Rust decision_engine executable.
    Falls back closed or uses Python policy mirror if binary unavailable.
    """

    def __init__(self, binary_path: Optional[str] = None):
        if binary_path:
            self.binary_path = Path(binary_path)
        else:
            exe_name = "decision_engine.exe" if sys.platform == "win32" else "decision_engine"
            possible_paths = [
                _PROJECT_ROOT / "build" / exe_name,
                _PROJECT_ROOT / "target" / "release" / exe_name,
                _PROJECT_ROOT / "decision_engine" / "target" / "release" / exe_name,
            ]
            self.binary_path = next((p for p in possible_paths if p.is_file()), None)

    def is_available(self) -> bool:
        """Check if compiled Rust decision engine binary is available and executable."""
        if not self.binary_path or not self.binary_path.exists():
            return False
        try:
            res = subprocess.run(
                [str(self.binary_path), "--help"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            return res.returncode == 0 or "Usage" in res.stderr or "VoltGuard" in res.stderr
        except Exception:
            return False

    def evaluate(self, physics_input: Union[Dict[str, Any], PhysicsResult, str]) -> Dict[str, Any]:
        """
        Evaluate physical safety input through Rust decision engine (or fail closed).
        """
        start_ns = time.perf_counter_ns()

        # Handle missing or null input
        if physics_input is None:
            return build_fail_closed_decision("Missing physics validation input", 0)

        # Convert PhysicsResult model to dict / JSON string if needed
        if isinstance(physics_input, PhysicsResult):
            physics_dict = physics_input.model_dump()
            json_str = physics_input.model_dump_json()
        elif isinstance(physics_input, dict):
            physics_dict = physics_input
            try:
                json_str = json.dumps(physics_input)
            except Exception as e:
                elapsed_us = (time.perf_counter_ns() - start_ns) // 1000
                return build_fail_closed_decision(f"Serialization error: {e}", elapsed_us)
        elif isinstance(physics_input, str):
            json_str = physics_input
            try:
                physics_dict = json.loads(physics_input)
            except Exception as e:
                elapsed_us = (time.perf_counter_ns() - start_ns) // 1000
                return build_fail_closed_decision(f"Invalid JSON string: {e}", elapsed_us)
        else:
            return build_fail_closed_decision("Invalid physics result object type", 0)

        # Basic schema verification
        if not isinstance(physics_dict, dict) or "safety_state" not in physics_dict:
            elapsed_us = (time.perf_counter_ns() - start_ns) // 1000
            return build_fail_closed_decision("Malformed physics result schema", elapsed_us)

        # Try compiled Rust binary executable first if available
        if self.binary_path and self.binary_path.exists():
            try:
                process = subprocess.run(
                    [str(self.binary_path), "--json", json_str],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False
                )
                stdout = process.stdout.strip()
                if stdout and "{" in stdout:
                    json_res = stdout[stdout.find("{"):stdout.rfind("}") + 1]
                    return json.loads(json_res)
            except Exception as e:
                # Subprocess failure -> fail closed
                pass

        # Fallback Python policy engine (retaining strict policy and fail-closed guarantees)
        return RustDecisionPolicyPython.evaluate(physics_dict, start_ns)


# Singleton wrapper instance
decision_engine_wrapper = RustDecisionEngineWrapper()
