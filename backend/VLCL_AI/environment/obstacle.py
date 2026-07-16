import numpy as np
from typing import Dict, Any, Tuple, Optional
from loguru import logger

class Obstacle:
    """Base class representing physical obstacles in the laboratory environment."""
    def __init__(self, obstacle_id: str, obstacle_type: str, position: np.ndarray, 
                 rotation: np.ndarray, scale: np.ndarray, reflectivity: float = 0.3, 
                 material: str = "generic"):
        self.id = obstacle_id
        self.type = obstacle_type
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)  # Roll, Pitch, Yaw in degrees
        self.scale = np.array(scale, dtype=float)  # Dimensions/scaling factors
        self.reflectivity = reflectivity
        self.material = material

    def intersects_ray(self, origin: np.ndarray, direction: np.ndarray) -> Tuple[bool, float]:
        """
        Determines if a ray intersects this obstacle.
        Returns:
            Tuple[bool, float]: (is_intersected, distance_to_intersection)
        """
        raise NotImplementedError("Subclasses must implement ray intersection tests.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position.tolist(),
            "rotation": self.rotation.tolist(),
            "scale": self.scale.tolist(),
            "reflectivity": self.reflectivity,
            "material": self.material
        }


class SphereObstacle(Obstacle):
    def __init__(self, obstacle_id: str, position: np.ndarray, radius: float, 
                 reflectivity: float = 0.3, material: str = "generic"):
        # Scale is [radius, radius, radius]
        super().__init__(obstacle_id, "sphere", position, np.array([0, 0, 0]), 
                         np.array([radius, radius, radius]), reflectivity, material)
        self.radius = radius

    def intersects_ray(self, origin: np.ndarray, direction: np.ndarray) -> Tuple[bool, float]:
        # Ray-Sphere intersection
        # Ray: P(t) = O + t*D, where D is normalized
        D = direction / np.linalg.norm(direction)
        L = self.position - origin
        tca = np.dot(L, D)
        if tca < 0:
            return False, float('inf')
            
        d2 = np.dot(L, L) - tca * tca
        r2 = self.radius * self.radius
        if d2 > r2:
            return False, float('inf')
            
        thc = np.sqrt(r2 - d2)
        t0 = tca - thc
        t1 = tca + thc
        
        t = t0 if t0 >= 0 else t1
        if t < 0:
            return False, float('inf')
            
        return True, t


class CylinderObstacle(Obstacle):
    def __init__(self, obstacle_id: str, position: np.ndarray, radius: float, height: float,
                 reflectivity: float = 0.3, material: str = "generic"):
        # scale is [radius, radius, height]
        super().__init__(obstacle_id, "cylinder", position, np.array([0, 0, 0]), 
                         np.array([radius, radius, height]), reflectivity, material)
        self.radius = radius
        self.height = height

    def intersects_ray(self, origin: np.ndarray, direction: np.ndarray) -> Tuple[bool, float]:
        # Simple vertical cylinder intersection (aligned with Z-axis)
        # Infinite cylinder in X-Y: (x - cx)^2 + (y - cy)^2 = r^2
        # Ray: P(t) = O + t*D
        D = direction / np.linalg.norm(direction)
        
        # Project vectors onto X-Y plane
        ox, oy = origin[0], origin[1]
        dx, dy = D[0], D[1]
        cx, cy = self.position[0], self.position[1]
        
        # Standard quadratic equation: A*t^2 + B*t + C = 0
        A = dx**2 + dy**2
        if abs(A) < 1e-8:
            # Parallel to cylinder axis
            # Check if origin is inside cylinder radius
            dist_xy_sq = (ox - cx)**2 + (oy - cy)**2
            if dist_xy_sq <= self.radius**2:
                # Intersects caps
                z_min = self.position[2] - self.height / 2.0
                z_max = self.position[2] + self.height / 2.0
                if D[2] > 0:
                    t = (z_min - origin[2]) / D[2]
                else:
                    t = (z_max - origin[2]) / D[2]
                if t >= 0:
                    return True, t
            return False, float('inf')

        B = 2 * (dx * (ox - cx) + dy * (oy - cy))
        C = (ox - cx)**2 + (oy - cy)**2 - self.radius**2
        
        discriminant = B**2 - 4 * A * C
        if discriminant < 0:
            return False, float('inf')
            
        t0 = (-B - np.sqrt(discriminant)) / (2 * A)
        t1 = (-B + np.sqrt(discriminant)) / (2 * A)
        
        for t in [t0, t1]:
            if t < 0:
                continue
            # Check Z height limits
            z_intersect = origin[2] + t * D[2]
            z_min = self.position[2] - self.height / 2.0
            z_max = self.position[2] + self.height / 2.0
            if z_min <= z_intersect <= z_max:
                return True, t
                
        return False, float('inf')


class BoxObstacle(Obstacle):
    def __init__(self, obstacle_id: str, position: np.ndarray, size: np.ndarray,
                 reflectivity: float = 0.3, material: str = "generic"):
        # Scale is [dx, dy, dz]
        super().__init__(obstacle_id, "box", position, np.array([0, 0, 0]), 
                         size, reflectivity, material)
        self.size = np.array(size, dtype=float)

    def intersects_ray(self, origin: np.ndarray, direction: np.ndarray) -> Tuple[bool, float]:
        # Ray-AABB intersection (Slab method)
        # Box bounds: [pos - size/2, pos + size/2]
        half_size = self.size / 2.0
        bounds_min = self.position - half_size
        bounds_max = self.position + half_size
        
        D = direction / np.linalg.norm(direction)
        
        tmin = -float('inf')
        tmax = float('inf')
        
        for i in range(3):
            if abs(D[i]) < 1e-8:
                # Parallel to axis slab
                if origin[i] < bounds_min[i] or origin[i] > bounds_max[i]:
                    return False, float('inf')
            else:
                t1 = (bounds_min[i] - origin[i]) / D[i]
                t2 = (bounds_max[i] - origin[i]) / D[i]
                
                tmin = max(tmin, min(t1, t2))
                tmax = min(tmax, max(t1, t2))
                
        if tmax >= tmin and tmax >= 0:
            t = tmin if tmin >= 0 else tmax
            return True, t
            
        return False, float('inf')


def create_obstacle(config: Dict[str, Any]) -> Obstacle:
    obs_id = config.get("id", "obstacle")
    obs_type = config.get("type", "box")
    pos = np.array(config.get("position", [0.0, 0.0, 0.0]))
    scale = np.array(config.get("scale", [1.0, 1.0, 1.0]))
    reflectivity = config.get("reflectivity", 0.3)
    material = config.get("material", "generic")
    
    if obs_type == "sphere":
        return SphereObstacle(obs_id, pos, scale[0], reflectivity, material)
    elif obs_type == "cylinder":
        return CylinderObstacle(obs_id, pos, scale[0], scale[2], reflectivity, material)
    else:
        return BoxObstacle(obs_id, pos, scale, reflectivity, material)
