import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EnvironmentState:
    """
    Immutable representation of the physical environment state at a specific simulation frame.
    Enables future RL agents or communication protocols to read state snapshots safely.
    """
    current_time: float
    frame_index: int
    fps: float
    
    # Receiver kinematics
    receiver_position: List[float]
    receiver_orientation: List[float]
    receiver_velocity: List[float]
    receiver_acceleration: List[float]
    receiver_angles: Dict[str, float]  # roll, pitch, yaw
    
    # LED list
    led_positions: Dict[int, List[float]]
    led_powers: Dict[int, float]
    led_active: Dict[int, bool]
    
    # Physical metric matrices
    distances: Dict[int, float]  # LED id to receiver distance
    incident_angles: Dict[int, float]  # LED id to receiver incidence angle
    irradiance_angles: Dict[int, float]  # LED id to receiver irradiance angle
    dc_gains: Dict[int, float]  # Lambertian path loss values H(0)
    
    # Visibility and blockages
    visibility_matrix: Dict[int, bool]  # LED id to within FOV & within cone
    los_matrix: Dict[int, bool]  # LED id to unobstructed path
    blocking_obstacles: Dict[int, str]  # LED id to obstacle ID causing block (if any)
    
    # Obstacles
    obstacles: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Converts state to standard dictionary (serializable to JSON/YAML)."""
        return {
            "current_time": self.current_time,
            "frame_index": self.frame_index,
            "fps": self.fps,
            "receiver": {
                "position": self.receiver_position,
                "orientation": self.receiver_orientation,
                "velocity": self.receiver_velocity,
                "acceleration": self.receiver_acceleration,
                "angles": self.receiver_angles
            },
            "led_positions": self.led_positions,
            "led_powers": self.led_powers,
            "led_active": self.led_active,
            "metrics": {
                "distances": self.distances,
                "incident_angles": self.incident_angles,
                "irradiance_angles": self.irradiance_angles,
                "dc_gains": self.dc_gains
            },
            "visibility": {
                "visibility_matrix": self.visibility_matrix,
                "los_matrix": self.los_matrix,
                "blocking_obstacles": self.blocking_obstacles
            },
            "obstacles": self.obstacles
        }
