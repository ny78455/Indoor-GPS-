# state.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

@dataclass(frozen=True)
class LocalizationState:
    """Immutable representation of the localization engine state per frame."""
    simulation_time: float
    frame_id: int
    
    # Coordinates
    estimated_position: List[float] # [x_est, y_est, z_est]
    true_position_for_evaluation_only: List[float] # [x_true, y_true, z_true]
    
    # Error metrics
    instantaneous_error_m: float
    horizontal_error_m: float
    vertical_error_m: float
    rmse_m: float
    
    # Frequencies and Transmitters
    frequencies_hz: List[float]
    tone_powers: List[float]
    received_powers: Dict[int, float]
    localization_snr: Dict[int, float]
    
    # Intermediate signal measurements
    I_components: List[float]
    Q_components: List[float]
    wrapped_phases: List[float]
    unwrapped_phases: List[float]
    
    # Recovered geometry
    distance_differences: Dict[str, float] # string-serialized keys: "led_j-led_ref"
    used_led_ids: List[int]
    rejected_measurements: List[str]
    
    # Solver statistics
    solver_method: str
    solver_iterations: int
    solver_cost: float
    solver_residual: List[float]
    
    # Quality & Calibration status
    confidence: float # 0.0 to 1.0
    status: str       # "VALID", "LOW_CONFIDENCE", "SOLVER_FAILED", "LOW_SNR", "INSUFFICIENT_GEOMETRY"
    calibration_applied: bool
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts state to serializable dictionary."""
        return {
            "simulation_time": self.simulation_time,
            "frame_id": self.frame_id,
            "estimated_position": self.estimated_position,
            "true_position": self.true_position_for_evaluation_only,
            "errors": {
                "instantaneous_m": self.instantaneous_error_m,
                "horizontal_m": self.horizontal_error_m,
                "vertical_m": self.vertical_error_m,
                "rmse_m": self.rmse_m
            },
            "signals": {
                "frequencies_hz": self.frequencies_hz,
                "tone_powers": self.tone_powers,
                "received_powers": self.received_powers,
                "localization_snr": self.localization_snr
            },
            "measurements": {
                "I": self.I_components,
                "Q": self.Q_components,
                "wrapped_phases": self.wrapped_phases,
                "unwrapped_phases": self.unwrapped_phases
            },
            "geometry": {
                "distance_differences": self.distance_differences,
                "used_led_ids": self.used_led_ids,
                "rejected_measurements": self.rejected_measurements
            },
            "solver": {
                "method": self.solver_method,
                "iterations": self.solver_iterations,
                "cost": self.solver_cost,
                "residual": self.solver_residual
            },
            "quality": {
                "confidence": self.confidence,
                "status": self.status,
                "calibration_applied": self.calibration_applied
            },
            "metadata": self.metadata
        }
