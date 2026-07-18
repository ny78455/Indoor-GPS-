# concentrator.py
import numpy as np
from typing import Union

def optical_concentrator_gain(
    incident_angle_rad: Union[float, np.ndarray],
    fov_rad: float,
    refractive_index: float = 1.5
) -> Union[float, np.ndarray]:
    """
    Computes optical concentrator gain.
    g(psi) = (n^2) / (sin^2(FOV)) for 0 <= psi <= FOV, else 0
    """
    if fov_rad <= 0:
        return 0.0
        
    gain_val = (refractive_index ** 2) / (np.sin(fov_rad) ** 2)
    
    if isinstance(incident_angle_rad, np.ndarray):
        # Array-wise selection
        gain = np.zeros_like(incident_angle_rad)
        mask = (incident_angle_rad >= 0.0) & (incident_angle_rad <= fov_rad)
        gain[mask] = gain_val
        return gain
    else:
        if 0.0 <= incident_angle_rad <= fov_rad:
            return float(gain_val)
        return 0.0
