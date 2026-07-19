# pre_equalizer.py
import numpy as np
from typing import Union, Dict, Any
from VLCL_AI.communication.exceptions import OFDMError

class PreEqualizer:
    """
    Applies transmitter-side pre-equalization to compensate for LED low-pass frequency response.
    Supports ZERO_FORCING and REGULARIZED modes with safety thresholds and power normalization.
    """
    
    def __init__(
        self,
        mode: str = "regularized",
        regularization: float = 1e-4,
        max_gain: float = 10.0,  # Max gain (linear factor) to prevent extreme boosting
        enabled: bool = False
    ):
        self.mode = mode.lower()
        self.regularization = regularization
        self.max_gain = max_gain
        self.enabled = enabled

    def compute_coefficients(self, h_response: np.ndarray) -> np.ndarray:
        """
        Computes the pre-equalization filter coefficients W_n for each subcarrier.
        
        Args:
            h_response (np.ndarray): Complex channel response H_n of the LED/channel.
        """
        if not self.enabled or self.mode == "none":
            return np.ones_like(h_response, dtype=complex)
            
        h_abs = np.abs(h_response)
        
        if self.mode == "zero_forcing":
            # W = 1 / H
            # Avoid divide-by-zero
            h_safe = np.where(h_abs < 1e-9, 1e-9, h_response)
            w = 1.0 / h_safe
            
        elif self.mode == "regularized" or self.mode == "weighted":
            # W = H* / (|H|^2 + lambda)
            denom = h_abs**2 + self.regularization
            w = np.conj(h_response) / denom
            
        else:
            return np.ones_like(h_response, dtype=complex)
            
        # Apply safety constraints (clipping the gain magnitude)
        w_abs = np.abs(w)
        scaled_w = np.where(w_abs > self.max_gain, w * (self.max_gain / np.where(w_abs == 0, 1.0, w_abs)), w)
        
        return scaled_w

    def pre_equalize(self, frequency_symbols: np.ndarray, h_response: np.ndarray) -> np.ndarray:
        """
        Applies pre-equalization coefficients to frequency domain symbols,
        optionally normalizing total transmit power.
        """
        if not self.enabled or self.mode == "none":
            return frequency_symbols
            
        coefficients = self.compute_coefficients(h_response)
        
        # Multiply coefficients across the frequency grid
        pre_eq_symbols = frequency_symbols * coefficients
        
        # Power normalization so total electrical power doesn't increase uncontrollably
        original_power = np.mean(np.abs(frequency_symbols) ** 2)
        eq_power = np.mean(np.abs(pre_eq_symbols) ** 2)
        
        if eq_power > 0 and original_power > 0:
            scale = np.sqrt(original_power / eq_power)
            normalized_symbols = pre_eq_symbols * scale
        else:
            normalized_symbols = pre_eq_symbols
            
        return normalized_symbols
