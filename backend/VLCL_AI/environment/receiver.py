import numpy as np
from typing import Dict, Any, Tuple
from loguru import logger
from .coordinate_system import CoordinateSystem

class Receiver:
    """
    Represents the optoelectronic mobile receiver (photodiode or APD sensor)
    in the laboratory environment.
    """
    def __init__(self, position: np.ndarray, orientation: np.ndarray,
                 velocity: np.ndarray = None, acceleration: np.ndarray = None,
                 fov: float = 70.0, apd_size: float = 1e-4, noise: float = 1e-14,
                 gain: float = 1.0, roll: float = 0.0, pitch: float = 0.0, yaw: float = 0.0):
        self.position = np.array(position, dtype=float)
        self.initial_orientation = CoordinateSystem.normalize_vector(orientation)
        self.velocity = np.array(velocity if velocity is not None else [0.0, 0.0, 0.0], dtype=float)
        self.acceleration = np.array(acceleration if acceleration is not None else [0.0, 0.0, 0.0], dtype=float)
        
        self.fov = fov  # Field of view semi-angle (degrees)
        self.apd_size = apd_size  # Active physical area of the APD (m^2)
        self.noise = noise  # APD noise level (W/Hz)
        self.gain = gain  # Optical filter + concentrator gain
        
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        
        # Calculate active orientation based on initial direction and roll/pitch/yaw angles
        self.update_angles(roll, pitch, yaw)
        
        logger.info(f"Initialized Receiver at {self.position.tolist()} facing {self.orientation.tolist()} (Roll: {roll}, Pitch: {pitch}, Yaw: {yaw})")

    def update_angles(self, roll: float, pitch: float, yaw: float):
        """Updates roll, pitch, yaw angles and recalculates orientation."""
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        
        # Get rotation matrix R
        R = CoordinateSystem.get_rotation_matrix(roll, pitch, yaw)
        self.orientation = CoordinateSystem.normalize_vector(R @ self.initial_orientation)
        self.rotation_matrix = R

    def move(self, delta_time: float, max_bounds: np.ndarray = None):
        """Advances receiver position using Euler integration with velocity/acceleration."""
        # s = s0 + v * dt + 0.5 * a * dt^2
        self.position += self.velocity * delta_time + 0.5 * self.acceleration * (delta_time ** 2)
        self.velocity += self.acceleration * delta_time
        
        # Clamping boundaries to keep receiver inside room
        if max_bounds is not None:
            self.position[0] = np.clip(self.position[0], 0.0, max_bounds[0])
            self.position[1] = np.clip(self.position[1], 0.0, max_bounds[1])
            self.position[2] = np.clip(self.position[2], 0.0, max_bounds[2])

    def rotate(self, delta_roll: float, delta_pitch: float, delta_yaw: float):
        """Increments roll, pitch, and yaw rotation angles."""
        self.update_angles(
            self.roll + delta_roll,
            self.pitch + delta_pitch,
            self.yaw + delta_yaw
        )


    # M1-ENV-004: receive_signal() and measure_snr() have been REMOVED.
    # These were dead code implementing received-power and SNR calculations —
    # physics quantities exclusively owned by Module 2 (PhysicsEngine).
    # Use physics/photodiode.py and physics/snr.py for canonical implementations.


    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position.tolist(),
            "orientation": self.orientation.tolist(),
            "velocity": self.velocity.tolist(),
            "acceleration": self.acceleration.tolist(),
            "fov": self.fov,
            "apd_size": self.apd_size,
            "noise": self.noise,
            "gain": self.gain,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw
        }
