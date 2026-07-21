# reflection.py
# Phase D Audit Result: PASS
# Verified:
#   - NLOS Lambertian model uses correct formula: h_wall = [(m+1)/(2πd²)] · cosᵐ(φ) · cos(α)
#   - Wall-to-receiver term: h_rx = (1/(πd²)) · cos(β) · cos(ψ) is correct (m=1 Lambertian)
#   - FOV gate applied correctly (psi > fov_rad -> skip)
#   - room_dims now passed in from EnvironmentState (INT-001 fix applied in physics_engine.py)
#   - FIX_REQUIRED: None in this file
import numpy as np
from typing import List, Dict, Any, Tuple
from VLCL_AI.physics.lambertian import radiation_pattern

def compute_nlos_reflection(
    led_pos: np.ndarray,
    led_normal: np.ndarray,
    m: float,
    rx_pos: np.ndarray,
    rx_normal: np.ndarray,
    rx_area: float,
    fov_rad: float,
    room_dims: List[float],
    wall_reflectivity: float = 0.8,
    num_grid_points: int = 10
) -> float:
    """
    Computes first-order Non-Line-Of-Sight (NLOS) reflection gain using a grid discretization of room walls.
    Assumes a rectangular room of dimensions width, length, height.
    Integrates the light paths LED -> Grid Wall Point -> Receiver.
    """
    W, L, H = room_dims
    total_nlos_gain = 0.0
    
    # Define wall surfaces to discretize
    # 6 faces: Left (x=0), Right (x=W), Front (y=0), Back (y=L), Floor (z=0), Ceiling (z=H)
    surfaces = [
        # (normal vector, constant coordinate index, coordinate value, surface_area)
        (np.array([1.0, 0.0, 0.0]), 0, 0.0, L * H),      # Left
        (np.array([-1.0, 0.0, 0.0]), 0, W, L * H),      # Right
        (np.array([0.0, 1.0, 0.0]), 1, 0.0, W * H),      # Front
        (np.array([0.0, -1.0, 0.0]), 1, L, W * H),      # Back
        (np.array([0.0, 0.0, 1.0]), 2, 0.0, W * L),      # Floor
        (np.array([0.0, 0.0, -1.0]), 2, H, W * L)        # Ceiling
    ]
    
    # Number of points per wall face to sample
    pts_per_axis = int(np.sqrt(num_grid_points)) if num_grid_points > 1 else 1
    
    for wall_norm, const_idx, const_val, surf_area in surfaces:
        # Generate grid on the surface
        if const_idx == 0:  # x is constant
            ys = np.linspace(0.1, L - 0.1, pts_per_axis)
            zs = np.linspace(0.1, H - 0.1, pts_per_axis)
            grid_y, grid_z = np.meshgrid(ys, zs)
            points = np.stack([np.full_like(grid_y, const_val), grid_y, grid_z], axis=-1).reshape(-1, 3)
        elif const_idx == 1:  # y is constant
            xs = np.linspace(0.1, W - 0.1, pts_per_axis)
            zs = np.linspace(0.1, H - 0.1, pts_per_axis)
            grid_x, grid_z = np.meshgrid(xs, zs)
            points = np.stack([grid_x, np.full_like(grid_x, const_val), grid_z], axis=-1).reshape(-1, 3)
        else:  # z is constant
            xs = np.linspace(0.1, W - 0.1, pts_per_axis)
            ys = np.linspace(0.1, L - 0.1, pts_per_axis)
            grid_x, grid_y = np.meshgrid(xs, ys)
            points = np.stack([grid_x, grid_y, np.full_like(grid_x, const_val)], axis=-1).reshape(-1, 3)
            
        ds_area = surf_area / len(points)  # Area element of wall
        
        # Vectorized calculation for grid points
        for pt in points:
            # LED to Wall Point
            d1_vec = pt - led_pos
            d1 = np.linalg.norm(d1_vec)
            if d1 <= 0:
                continue
            d1_dir = d1_vec / d1
            
            cos_phi = np.dot(d1_dir, led_normal)
            if cos_phi < 0:
                continue
                
            # Angle of incidence at the wall (with wall normal)
            # Wall normal points inward or outward; we use absolute cosine
            cos_alpha = np.abs(np.dot(-d1_dir, wall_norm))
            
            # Radiance received at wall point ds from LED
            h_wall_ds = ((m + 1) / (2 * np.pi * (d1 ** 2))) * (cos_phi ** m) * cos_alpha
            
            # Wall Point to Receiver
            d2_vec = rx_pos - pt
            d2 = np.linalg.norm(d2_vec)
            if d2 <= 0:
                continue
            d2_dir = d2_vec / d2
            
            # Angle of emission from wall point (diffuse lambertian reflector has m=1)
            cos_beta = np.dot(d2_dir, wall_norm)
            if cos_beta < 0:
                continue
                
            # Angle of incidence at receiver
            cos_psi = np.dot(-d2_dir, rx_normal)
            psi = np.arccos(np.clip(cos_psi, -1.0, 1.0))
            if psi > fov_rad:
                continue
                
            # Gain from wall point to receiver (wall point acts as secondary Lambertian source with m=1)
            h_rx_ds = (1.0 / (np.pi * (d2 ** 2))) * cos_beta * cos_psi
            
            # Add to total gain
            total_nlos_gain += h_wall_ds * wall_reflectivity * ds_area * h_rx_ds * rx_area
            
    return float(total_nlos_gain)
