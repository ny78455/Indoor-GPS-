import numpy as np
from typing import Dict, Any
from loguru import logger

class Room:
    """
    Represents the indoor optical lab, establishing geometry boundaries
    and surface reflection coefficients.
    """
    def __init__(self, width: float, length: float, height: float, 
                 wall_reflectivity: float = 0.8, 
                 floor_reflectivity: float = 0.2, 
                 ceiling_reflectivity: float = 0.5):
        self.width = width
        self.length = length
        self.height = height
        self.wall_reflectivity = wall_reflectivity
        self.floor_reflectivity = floor_reflectivity
        self.ceiling_reflectivity = ceiling_reflectivity
        
        logger.info(f"Initialized Room: {width}x{length}x{height}m. Reflectivities - W:{wall_reflectivity}, F:{floor_reflectivity}, C:{ceiling_reflectivity}")

    def is_inside(self, position: np.ndarray) -> bool:
        """Checks if a 3D position is inside the room boundaries."""
        x, y, z = position[0], position[1], position[2]
        return (0 <= x <= self.width) and (0 <= y <= self.length) and (0 <= z <= self.height)

    def reset(self, width: float = 5.0, length: float = 5.0, height: float = 3.0,
              wall_reflectivity: float = 0.8, floor_reflectivity: float = 0.2, ceiling_reflectivity: float = 0.5):
        """Resets the room parameters to new values."""
        self.width = width
        self.length = length
        self.height = height
        self.wall_reflectivity = wall_reflectivity
        self.floor_reflectivity = floor_reflectivity
        self.ceiling_reflectivity = ceiling_reflectivity
        logger.info("Room parameters reset.")

    def to_dict(self) -> Dict[str, Any]:
        """Exports room configuration to a dictionary."""
        return {
            "width": self.width,
            "length": self.length,
            "height": self.height,
            "wall_reflectivity": self.wall_reflectivity,
            "floor_reflectivity": self.floor_reflectivity,
            "ceiling_reflectivity": self.ceiling_reflectivity
        }

    def render_3d_specs(self) -> Dict[str, Any]:
        """Returns 3D rendering data (walls, coordinates, axes)."""
        return {
            "bounds": [self.width, self.length, self.height],
            "vertices": [
                [0, 0, 0], [self.width, 0, 0], [self.width, self.length, 0], [0, self.length, 0],
                [0, 0, self.height], [self.width, 0, self.height], [self.width, self.length, self.height], [0, self.length, self.height]
            ]
        }
