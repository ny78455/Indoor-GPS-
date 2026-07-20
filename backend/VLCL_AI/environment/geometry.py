import numpy as np
from typing import Tuple, List, Optional
from loguru import logger
from .obstacle import Obstacle

class GeometryEngine:
    """
    Computes all essential 3D vector geometries for Integrated VLCL.

    ANGULAR UNIT CONTRACT (M1-ENV-ANGLE-001)
    =========================================
    All angles returned by this class are in RADIANS.
    Configuration and UI may accept degrees, but conversion occurs
    exactly once at the configuration/environment boundary.

    Internal computation:  radians
    Configuration / UI:    may use degrees (convert at boundary)
    Display:               may convert radians → degrees for output
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
        and incident angle (psi) at the photo receiver.

        Returns:
            Tuple[float, float]: (irradiance_angle_rad, incident_angle_rad)
              Both values are in RADIANS.
              Range: [0, pi]

        Paper reference: H(0) definition — phi and psi are used directly
        in cos^m(phi) and cos(psi) terms; must be in radians for numpy trig.

        Req: M1-ENV-ANGLE-001 — canonical internal unit = radians.
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
        phi_rad = np.arccos(cos_phi)  # radians — NO np.degrees() wrapper

        # Incident angle (psi): Angle between receiver normal (n_rx) and incoming vector
        cos_psi = np.clip(np.dot(-v_tr_unit, n_rx_unit), -1.0, 1.0)
        psi_rad = np.arccos(cos_psi)  # radians — NO np.degrees() wrapper

        return phi_rad, psi_rad

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

    # NOTE: calculate_lambertian_dc_gain() has been REMOVED (M1-ENV-002).
    # H(0) is computed exclusively by physics/optical_channel.py::compute_los_dc_gain().
    # Module 1 (environment) does NOT compute any channel-gain-shaped quantity.
    # See PhysicsState.los_gains for the canonical H(0) output.

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
