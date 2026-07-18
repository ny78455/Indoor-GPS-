# lambertian.py
import numpy as np
from typing import Union

def lambertian_order(theta_half_deg: float) -> float:
    """
    Computes the Lambertian order m from the semi-angle at half power.
    m = -ln(2) / ln(cos(theta_half))
    """
    theta_half_rad = np.radians(theta_half_deg)
    cos_theta = np.cos(theta_half_rad)
    if cos_theta <= 0 or cos_theta >= 1.0:
        return 1.0
    return float(-np.log(2.0) / np.log(cos_theta))

def radiation_pattern(m: float, phi_rad: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the normalized Lambertian radiation pattern intensity at a given angle.
    I(phi) = [(m + 1) / (2 * pi)] * cos^m(phi)
    """
    cos_phi = np.cos(phi_rad)
    # Cosine must be positive (only emission in the forward hemisphere)
    if isinstance(phi_rad, np.ndarray):
        cos_phi = np.clip(cos_phi, 0.0, 1.0)
        return ((m + 1) / (2 * np.pi)) * (cos_phi ** m)
    else:
        if cos_phi < 0:
            return 0.0
        return float(((m + 1) / (2 * np.pi)) * (cos_phi ** m))

def irradiance(m: float, power: float, distance: Union[float, np.ndarray], phi_rad: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the optical irradiance (W/m^2) at a given distance and angle.
    E(d, phi) = P_tx * [(m + 1) / (2 * pi * d^2)] * cos^m(phi)
    """
    cos_phi = np.cos(phi_rad)
    if isinstance(phi_rad, np.ndarray):
        cos_phi = np.clip(cos_phi, 0.0, 1.0)
        # Avoid division by zero
        dist_sq = np.where(distance > 0, distance ** 2, 1e-12)
        return power * ((m + 1) / (2 * np.pi * dist_sq)) * (cos_phi ** m)
    else:
        if cos_phi < 0 or distance <= 0:
            return 0.0
        return float(power * ((m + 1) / (2 * np.pi * (distance ** 2))) * (cos_phi ** m))
