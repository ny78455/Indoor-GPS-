# transfer_function.py
import numpy as np
from typing import List, Optional

class TransferFunctionMatrix:
    """
    Represents the diagonal LED transfer-function matrix H_k for a signal group or user subcarriers.
    In OFDM, subcarriers are orthogonal, so H_k is represented as a diagonal matrix or a 1D complex vector.
    """

    def __init__(
        self,
        group_id: int,
        subcarrier_indices: List[int],
        frequencies_hz: np.ndarray,
        complex_response: np.ndarray
    ):
        self.group_id = group_id
        self.subcarrier_indices = list(subcarrier_indices)
        self.frequencies_hz = np.asarray(frequencies_hz, dtype=float)
        self.complex_response = np.asarray(complex_response, dtype=complex)
        
        if len(self.subcarrier_indices) != len(self.complex_response):
            raise ValueError("Length of subcarrier_indices must match complex_response length.")

    @property
    def magnitudes(self) -> np.ndarray:
        """Returns the magnitude response |H_k|."""
        return np.abs(self.complex_response)

    @property
    def phases(self) -> np.ndarray:
        """Returns the phase response in radians."""
        return np.angle(self.complex_response)

    @property
    def condition_number(self) -> float:
        """
        Computes condition number max(|H|)/min(|H|) for non-zero entries.
        """
        mags = self.magnitudes
        mags_nonzero = mags[mags > 1e-12]
        if len(mags_nonzero) == 0:
            return float('inf')
        return float(np.max(mags_nonzero) / np.min(mags_nonzero))

    def as_diagonal_matrix(self) -> np.ndarray:
        """Returns full M_k x M_k diagonal numpy matrix."""
        return np.diag(self.complex_response)

    def inverse_diagonal(self, mode: str = "zero_forcing", eps: float = 1e-9, reg_lambda: float = 1e-4) -> np.ndarray:
        """
        Computes element-wise inverse diagonal filter coefficients H_k^-1.
        """
        H = self.complex_response
        H_abs = np.abs(H)

        if mode == "none":
            return np.ones_like(H, dtype=complex)

        elif mode == "zero_forcing" or mode == "full_inverse":
            H_safe = np.where(H_abs < eps, eps, H)
            return 1.0 / H_safe

        elif mode in ["regularized", "paper_weighted", "simulator_regularized_baseline"]:
            denom = (H_abs ** 2) + reg_lambda
            return np.conj(H) / denom

        else:
            return np.ones_like(H, dtype=complex)
