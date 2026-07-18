# receiver_model.py
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ReceiverModel:
    position: List[float] = field(default_factory=lambda: [2.5, 2.5, 0.85])
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    fov: float = 70.0  # FOV semi-angle in degrees
    area: float = 1e-4  # APD active area (m^2)
    roll: float = 0.0  # degrees
    pitch: float = 0.0  # degrees
    yaw: float = 0.0  # degrees
    
    def get_rotation_matrix(self) -> np.ndarray:
        """
        Computes the rotation matrix R = Rz(yaw) * Ry(pitch) * Rx(roll).
        """
        r_x = np.radians(self.roll)
        r_y = np.radians(self.pitch)
        r_z = np.radians(self.yaw)
        
        # Rx (roll)
        R_x = np.array([
            [1, 0, 0],
            [0, np.cos(r_x), -np.sin(r_x)],
            [0, np.sin(r_x), np.cos(r_x)]
        ])
        
        # Ry (pitch)
        R_y = np.array([
            [np.cos(r_y), 0, np.sin(r_y)],
            [0, 1, 0],
            [-np.sin(r_y), 0, np.cos(r_y)]
        ])
        
        # Rz (yaw)
        R_z = np.array([
            [np.cos(r_z), -np.sin(r_z), 0],
            [np.sin(r_z), np.cos(r_z), 0],
            [0, 0, 1]
        ])
        
        return R_z @ R_y @ R_x

    def get_normal_vector(self) -> np.ndarray:
        """
        Transforms the default receiver normal vector [0, 0, 1] using the rotation matrix R.
        """
        R = self.get_rotation_matrix()
        default_normal = np.array([0.0, 0.0, 1.0])
        return R @ default_normal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "orientation": self.orientation,
            "fov": self.fov,
            "area": self.area,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "normal": self.get_normal_vector().tolist()
        }
