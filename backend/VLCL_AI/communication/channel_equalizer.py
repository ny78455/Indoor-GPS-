# channel_equalizer.py
import numpy as np
from typing import Dict, Any

class ChannelEqualizer:
    """
    Equalizes received complex symbols on active subcarriers.
    Supports ZERO_FORCING (ZF) and Minimum Mean Square Error (MMSE) modes.
    """
    
    def __init__(self, mode: str = "MMSE"):
        self.mode = mode.upper()

    def equalize(
        self,
        rx_symbols: np.ndarray,
        h_channel: np.ndarray,
        noise_variance: float = 1e-12,
        subcarrier_powers: np.ndarray = None
    ) -> np.ndarray:
        """
        Applies equalization to received symbols.
        
        Args:
            rx_symbols (np.ndarray): Complex received subcarrier symbols.
            h_channel (np.ndarray): Channel response coefficients H_n.
            noise_variance (float): Noise variance for MMSE calculations.
            subcarrier_powers (np.ndarray): Power allocated per subcarrier.
        """
        h_abs = np.abs(h_channel)
        
        if self.mode == "ZERO_FORCING" or self.mode == "ZF":
            # X_hat = Y / H
            # Guard against tiny coefficients
            h_safe = np.where(h_abs < 1e-9, 1e-9, h_channel)
            return rx_symbols / h_safe
            
        elif self.mode == "MMSE":
            # X_hat = (H* / (|H|^2 + noise/power)) * Y
            if subcarrier_powers is None:
                subcarrier_powers = np.ones_like(h_abs)
                
            # Avoid division by zero in power
            p_safe = np.where(subcarrier_powers < 1e-9, 1e-9, subcarrier_powers)
            snr_inv = noise_variance / p_safe
            
            denom = h_abs**2 + snr_inv
            # Guard denom from being too small
            denom_safe = np.where(denom < 1e-9, 1e-9, denom)
            
            w = np.conj(h_channel) / denom_safe
            return rx_symbols * w
            
        else:
            # No equalization
            return rx_symbols
