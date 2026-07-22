# pre_equalizer.py
import numpy as np
from typing import Union, Dict, Any, Tuple, Optional
from VLCL_AI.communication.exceptions import OFDMError

class PreEqualizer:
    """
    Applies transmitter-side pre-equalization to compensate for LED low-pass frequency response.
    Implements Eq. (18) from Yang et al. (IEEE Trans. Commun. Dec 2023):
        S'_k = sqrt(P_k) * H_k^-1 * S_k
    
    Supports NONE, ZERO_FORCING (FULL_INVERSE), REGULARIZED, and PAPER_WEIGHTED modes
    with safety thresholds, gain caps, and power budget preservation.
    """
    
    def __init__(
        self,
        mode: str = "regularized",
        regularization: float = 1e-4,
        max_gain_db: float = 10.0,  # Max gain cap in dB
        max_gain: Optional[float] = None, # Linear gain cap for backward compatibility
        enabled: bool = True
    ):
        self.mode = mode.lower()
        self.regularization = regularization
        if max_gain is not None:
            self.max_gain_linear = float(max_gain)
            self.max_gain_db = float(20.0 * np.log10(self.max_gain_linear)) if self.max_gain_linear > 0 else 0.0
        else:
            self.max_gain_db = max_gain_db
            self.max_gain_linear = 10.0 ** (max_gain_db / 20.0)
        self.enabled = enabled

    def compute_coefficients(self, h_response: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes the pre-equalization filter coefficients W_n for each subcarrier
        and identifies gain-saturated subcarrier indices.
        
        Args:
            h_response (np.ndarray): Complex channel response H_n of the LED/channel.
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (coefficients_W, saturated_boolean_mask)
        """
        if not self.enabled or self.mode == "none":
            return np.ones_like(h_response, dtype=complex), np.zeros_like(h_response, dtype=bool)
            
        h_abs = np.abs(h_response)
        
        if self.mode in ["zero_forcing", "full_inverse"]:
            # W = 1 / H
            h_safe = np.where(h_abs < 1e-9, 1e-9, h_response)
            w = 1.0 / h_safe
            
        elif self.mode in ["regularized", "paper_weighted", "simulator_regularized_baseline", "weighted"]:
            # W = H* / (|H|^2 + lambda)
            denom = (h_abs ** 2) + self.regularization
            w = np.conj(h_response) / denom
            
        else:
            return np.ones_like(h_response, dtype=complex), np.zeros_like(h_response, dtype=bool)
            
        # Apply gain ceiling (clipping the gain magnitude)
        w_abs = np.abs(w)
        saturated_mask = w_abs > self.max_gain_linear
        
        scaled_w = np.where(
            saturated_mask,
            w * (self.max_gain_linear / np.where(w_abs == 0, 1.0, w_abs)),
            w
        )
        
        return scaled_w, saturated_mask

    def apply_eq18(
        self,
        symbols: np.ndarray,
        h_response: np.ndarray,
        allocated_power: Union[float, np.ndarray]
    ) -> np.ndarray:
        """
        Evaluates paper Equation (18): S'_k = sqrt(P_k) * H_k^-1 * S_k
        
        Args:
            symbols (np.ndarray): Input frequency domain QAM symbols S_k.
            h_response (np.ndarray): LED transfer function H_k.
            allocated_power (float or np.ndarray): Allocated electrical power P_k or P_n per carrier.
            
        Returns:
            np.ndarray: Pre-equalized transmit symbols S'_k.
        """
        coeffs, _ = self.compute_coefficients(h_response)
        sqrt_power = np.sqrt(np.maximum(allocated_power, 0.0))
        return sqrt_power * coeffs * symbols
