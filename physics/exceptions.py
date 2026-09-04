"""
VoltGuard Physics Engine — Custom Exceptions

Raised by the physics engine to signal validation and simulation failures.
These are intentionally separate from FastAPI HTTPException so the engine
remains independent of the web layer.
"""


class PhysicsValidationError(ValueError):
    """
    Raised when a PhysicsCommand contains physically impossible values.

    Examples:
        - pump_rpm < 0
        - valve_position outside [0, 100]
        - NaN or infinite values in any field
        - current_temperature below absolute zero

    The caller should catch this and return a 422 or equivalent response.
    """

    def __init__(self, field: str, value: object, reason: str) -> None:
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"[PhysicsValidationError] field='{field}' value={value!r}: {reason}"
        )


class PhysicsSimulationError(RuntimeError):
    """
    Raised when the physics calculation itself fails unexpectedly.

    This should not normally occur with valid inputs.
    If caught, log as CRITICAL and return a 500.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"[PhysicsSimulationError] {detail}")
