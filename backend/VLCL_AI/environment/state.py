import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EnvironmentState:
    """
    Immutable representation of the physical environment state at a specific simulation frame.

    OWNERSHIP BOUNDARY (Modules 1–4 Audit & Repair):
    =================================================
    This state carries GEOMETRY ONLY. No channel-gain-shaped quantity lives here.
    - incident_angles_rad, irradiance_angles_rad: angles in RADIANS (M1-ENV-ANGLE-001)
    - dc_gains: REMOVED (M1-ENV-002) — use PhysicsState.los_gains from Module 2
    - led_lambertian_orders: NOT PRESENT — derived by Module 2 from led_beam_angles
    - room_dims, led_orientations, led_beam_angles: primitives for Module 2 (INT-001)

    Module 2 (PhysicsEngine) is the sole owner of H(0), received power, noise, SNR.
    """
    current_time: float
    frame_index: int
    fps: float

    # Receiver kinematics
    receiver_position: List[float]
    receiver_orientation: List[float]
    receiver_velocity: List[float]
    receiver_acceleration: List[float]
    receiver_angles: Dict[str, float]  # roll, pitch, yaw (degrees — display convention)

    # LED descriptors
    led_positions: Dict[int, List[float]]
    led_powers: Dict[int, float]
    led_active: Dict[int, bool]

    # INT-001: LED geometry primitives for Module 2 (not computed here)
    led_orientations: Dict[int, List[float]]   # LED normal vectors
    led_beam_angles: Dict[int, float]           # semi-angle at half-power (degrees, config primitive)
    # NOTE: led_lambertian_orders is NOT in EnvironmentState.
    #   m = -ln(2)/ln(cos(beam_angle)) is a derived optical quantity owned by Module 2.
    #   Module 2 derives m from led_beam_angles using physics/lambertian.py::lambertian_order().

    # Physical metric matrices (geometry only)
    distances: Dict[int, float]           # LED id → distance to receiver (metres)
    incident_angles_rad: Dict[int, float]   # LED id → receiver incidence angle ψ (RADIANS)
    irradiance_angles_rad: Dict[int, float] # LED id → LED irradiance angle φ (RADIANS)
    # dc_gains REMOVED (M1-ENV-002): Module 1 must NOT compute channel gain.
    # Use PhysicsState.los_gains for the canonical H(0) values.

    # Visibility and blockages
    visibility_matrix: Dict[int, bool]   # LED id → within FOV & within cone
    los_matrix: Dict[int, bool]          # LED id → unobstructed path
    blocking_obstacles: Dict[int, str]   # LED id → obstacle ID causing block (if any)

    # Room geometry (INT-001): sourced from Room object, propagated to Module 2/4
    room_dims: List[float]  # [width, length, height] in metres

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
            "led_orientations": self.led_orientations,
            "led_beam_angles": self.led_beam_angles,
            "metrics": {
                "distances": self.distances,
                # Angles in radians; display code should convert to degrees if needed
                "incident_angles_rad": self.incident_angles_rad,
                "irradiance_angles_rad": self.irradiance_angles_rad,
                # dc_gains removed — use physics.los_gains
            },
            "visibility": {
                "visibility_matrix": self.visibility_matrix,
                "los_matrix": self.los_matrix,
                "blocking_obstacles": self.blocking_obstacles
            },
            "room_dims": self.room_dims,
            "obstacles": self.obstacles
        }

