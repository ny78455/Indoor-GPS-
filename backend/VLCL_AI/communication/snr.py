# snr.py
import numpy as np
from typing import Dict, Any

def compute_communication_snr(
    responsivity: float,
    subcarrier_powers: np.ndarray,      # Array of electrical powers P_n,i (shape: N_subcarriers, N_leds)
    channel_gains: np.ndarray,          # Array of optical gains H_i,n,k (shape: N_leds, N_subcarriers)
    noise_variance: float,              # Thermal + shot noise power (float)
    delta: float = 1.0                  # System scaling/efficiency factor
) -> np.ndarray:
    """
    Computes communication SNR per subcarrier for a user k:
    gamma_{k,n}^co = (delta^2 * mu^2 * (sum_{i=1}^L P_{n,i} * H_{i,n,k})^2) / sigma^2
    
    Args:
        responsivity (mu): Photodiode conversion efficiency (A/W).
        subcarrier_powers: Electrical power allocated to subcarrier n at LED i. Shape (N_subcarriers, N_leds)
        channel_gains: Optical channel gain of subcarrier n from LED i to user k. Shape (N_leds, N_subcarriers)
        noise_variance (sigma^2): Noise power.
        delta: Standard scaling factor.
    """
    # Number of subcarriers and LEDs
    n_subcarriers, n_leds = subcarrier_powers.shape
    
    # Calculate sum_{i=1}^L (P_{n,i} * H_{i,n,k})
    # We do element-wise multiplication of P_n,i and H_i,n, then sum across LEDs
    # Powers is (N_subcarriers, N_leds), Gains transposed is (N_subcarriers, N_leds)
    gains_transposed = channel_gains.T  # Shape: (N_subcarriers, N_leds)
    
    combined_optical = np.sum(subcarrier_powers * gains_transposed, axis=1) # Shape: (N_subcarriers,)
    
    # Numerator: delta^2 * mu^2 * (combined_optical)^2
    numerator = (delta ** 2) * (responsivity ** 2) * (combined_optical ** 2)
    
    # Avoid division by zero
    safe_noise = noise_variance if noise_variance > 1e-18 else 1e-18
    
    # Linear SNR
    snr_linear = numerator / safe_noise
    
    return snr_linear
