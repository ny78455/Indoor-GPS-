import numpy as np
from typing import Tuple, List, Optional
from loguru import logger
from .obstacle import Obstacle

class GeometryEngine:
    """
    Computes all essential 3D vector geometries and optical channel parameters 
    for Integrated Visible Light Communication and Localization (VLCL).
    """

    @staticmethod
    def distance(p1: np.ndarray, p2: np.ndarray) -> float:
        """Computes Euclidean distance between two points."""
        return float(np.linalg.norm(p1 - p2))

    @staticmethod
    def calculate_angles(p_tx: np.ndarray, n_tx: np.ndarray,
                         p_rx: np.ndarray, n_rx: np.ndarray) -> Tuple[float, float]:
        """
        Calculates irradiance angle (phi) at the LED transmitter 
        and incident angle (psi) at the photo receiver in degrees.
        
        Args:
            p_tx: Transmitter position [x, y, z]
            n_tx: Transmitter normal vector [dx, dy, dz]
            p_rx: Receiver position [x, y, z]
            n_rx: Receiver normal vector [dx, dy, dz]
            
        Returns:
            Tuple[float, float]: (irradiance_angle_deg, incident_angle_deg)
        """
        # Vector from Tx to Rx
        v_tr = p_rx - p_tx
        d = np.linalg.norm(v_tr)
        if d == 0:
            return 0.0, 0.0
            
        v_tr_unit = v_tr / d
        n_tx_unit = n_tx / np.linalg.norm(n_tx)
        n_rx_unit = n_rx / np.linalg.norm(n_rx)
        
        # Irradiance angle (phi): Angle between emission normal (n_tx) and vector to receiver
        cos_phi = np.clip(np.dot(v_tr_unit, n_tx_unit), -1.0, 1.0)
        phi = np.degrees(np.arccos(cos_phi))
        
        # Incident angle (psi): Angle between receiver normal (n_rx) and incoming vector (-v_tr_unit)
        cos_psi = np.clip(np.dot(-v_tr_unit, n_rx_unit), -1.0, 1.0)
        psi = np.degrees(np.arccos(cos_psi))
        
        return phi, psi

    @staticmethod
    def is_visible_los(p_tx: np.ndarray, p_rx: np.ndarray, 
                       obstacles: List[Obstacle]) -> Tuple[bool, Optional[str]]:
        """
        Evaluates line-of-sight (LOS) blockages between LED and receiver.
        
        Returns:
            Tuple[bool, str]: (is_visible, blocking_obstacle_id)
        """
        ray_vec = p_rx - p_tx
        ray_dist = np.linalg.norm(ray_vec)
        if ray_dist == 0:
            return True, None
            
        ray_dir = ray_vec / ray_dist
        
        # Check intersection with all obstacles
        for obs in obstacles:
            intersects, t = obs.intersects_ray(p_tx, ray_dir)
            if intersects and (0.01 < t < (ray_dist - 0.01)):
                # Blocked by this obstacle before reaching receiver
                return False, obs.id
                
        return True, None

    @staticmethod
    def calculate_lambertian_dc_gain(p_tx: np.ndarray, n_tx: np.ndarray, m: float,
                                     p_rx: np.ndarray, n_rx: np.ndarray, rx_fov: float,
                                     rx_area: float, rx_gain: float) -> float:
        """
        Computes the standard Lambertian optical path loss gain (H(0)).
        """
        d = GeometryEngine.distance(p_tx, p_rx)
        if d == 0:
            return 0.0
            
        phi, psi = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)
        
        # Check FOV limit
        if abs(psi) > rx_fov:
            return 0.0
            
        cos_phi = np.cos(np.radians(phi))
        cos_psi = np.cos(np.radians(psi))
        
        if cos_phi < 0 or cos_psi < 0:
            return 0.0
            
        # H(0) = [(m+1) * A / (2 * pi * d^2)] * cos^m(phi) * T(psi) * g(psi) * cos(psi)
        # Assuming optical filter gain T(psi) = 1.0, and concentrator gain g(psi) = rx_gain
        coeff = ((m + 1) * rx_area) / (2.0 * np.pi * (d ** 2))
        gain = coeff * (cos_phi ** m) * rx_gain * cos_psi
        
        return float(gain)

    @staticmethod
    def check_room_boundaries_collision(position: np.ndarray, room_bounds: List[float], 
                                         margin: float = 0.05) -> Tuple[bool, np.ndarray]:
        """
        Checks if a position is colliding with walls and returns the resolved/clamped position.
        """
        collided = False
        resolved = np.array(position, dtype=float)
        
        for i in range(3):
            if resolved[i] < margin:
                resolved[i] = margin
                collided = True
            elif resolved[i] > (room_bounds[i] - margin):
                resolved[i] = room_bounds[i] - margin
                collided = True
                
        return collided, resolved
