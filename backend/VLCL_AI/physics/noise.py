# noise.py
import numpy as np
from typing import Dict, Any
from VLCL_AI.physics.constants import ELECTRON_CHARGE, BOLTZMANN_CONSTANT

def compute_shot_noise(
    current: float,
    bandwidth: float,
    enabled: bool = True
) -> float:
    """
    Computes Shot Noise variance (A^2).
    sigma_shot^2 = 2 * q * I * B
    """
    if not enabled or current <= 0:
        return 0.0
    return float(2.0 * ELECTRON_CHARGE * current * bandwidth)

def compute_thermal_noise(
    temperature: float,
    bandwidth: float,
    tia_gain: float,
    enabled: bool = True
) -> float:
    """
    Computes Thermal Noise variance (A^2).
    sigma_thermal^2 = 4 * k_B * T * B / R_tia
    """
    if not enabled or tia_gain <= 0:
        return 0.0
    return float(4.0 * BOLTZMANN_CONSTANT * temperature * bandwidth / tia_gain)

def compute_background_noise(
    background_current: float,
    bandwidth: float,
    enabled: bool = True
) -> float:
    """
    Computes Ambient Background Light Shot Noise variance (A^2).
    sigma_bg^2 = 2 * q * I_bg * B
    """
    if not enabled or background_current <= 0:
        return 0.0
    return float(2.0 * ELECTRON_CHARGE * background_current * bandwidth)

def compute_electronic_noise(
    bandwidth: float,
    enabled: bool = True
) -> float:
    """
    Computes additional electronic pre-amplifier noise variance (A^2).
    Using a nominal noise spectral density.
    """
    if not enabled:
        return 0.0
    spectral_density = 1e-22  # A^2 / Hz
    return float(spectral_density * bandwidth)

def total_noise_variance(
    signal_current: float,
    tia_gain: float,
    bandwidth: float,
    temperature: float = 298.15,
    background_current: float = 100e-6,
    config: Dict[str, bool] = None
) -> Dict[str, float]:
    """
    Computes individual noise variances and returns total variance and standard deviation.
    """
    if config is None:
        config = {
            "shot": True,
            "thermal": True,
            "background": True,
            "electronic": True
        }
        
    shot_var = compute_shot_noise(signal_current, bandwidth, config.get("shot", True))
    thermal_var = compute_thermal_noise(temperature, bandwidth, tia_gain, config.get("thermal", True))
    bg_var = compute_background_noise(background_current, bandwidth, config.get("background", True))
    elec_var = compute_electronic_noise(bandwidth, config.get("electronic", True))
    
    total_var = shot_var + thermal_var + bg_var + elec_var
    total_std = np.sqrt(total_var) if total_var > 0 else 0.0
    
    return {
        "shot_variance": shot_var,
        "thermal_variance": thermal_var,
        "background_variance": bg_var,
        "electronic_variance": elec_var,
        "total_variance": total_var,
        "total_std": total_std
    }
