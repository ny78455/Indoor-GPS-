# optical_channel.py
import numpy as np
from typing import Union, Dict, Any
from VLCL_AI.physics.lambertian import lambertian_order, radiation_pattern
from VLCL_AI.physics.concentrator import optical_concentrator_gain

def compute_los_dc_gain(
    distance: float,
    irradiance_angle_rad: float,
    incident_angle_rad: float,
    beam_angle_deg: float,
    receiver_area: float,
    fov_rad: float,
    refractive_index: float = 1.5,
    is_los: bool = True
) -> float:
    """
    Computes direct line-of-sight path loss H(0) according to VLC literature.
    H(0) = [(m+1)*A / (2*pi*d^2)] * cos^m(phi) * T(psi) * g(psi) * cos(psi)
    """
    if not is_los or distance <= 0:
        return 0.0
        
    # Check if light is within the receiver FOV
    if incident_angle_rad > fov_rad or incident_angle_rad < 0.0:
        return 0.0
        
    m = lambertian_order(beam_angle_deg)
    
    # Cosine factors
    cos_phi = np.cos(irradiance_angle_rad)
    cos_psi = np.cos(incident_angle_rad)
    
    if cos_phi < 0 or cos_psi < 0:
        return 0.0
        
    # Concentrator gain
    g_concentrator = optical_concentrator_gain(incident_angle_rad, fov_rad, refractive_index)
    
    # Optical filter gain (assumed default = 1.0)
    t_filter = 1.0
    
    # H(0) calculation
    gain = ((m + 1) * receiver_area / (2 * np.pi * (distance ** 2))) * \
           (cos_phi ** m) * t_filter * g_concentrator * cos_psi
           
    return float(gain)
