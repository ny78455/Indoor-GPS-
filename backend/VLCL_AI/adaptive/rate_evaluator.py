# rate_evaluator.py
import numpy as np
from typing import Dict, List, Tuple
from VLCL_AI.communication.rate import RateCalculator

class RateEvaluator:
    """
    Evaluates candidate and allocated PHY data rates per device and subcarrier.
    """

    def __init__(self, subcarrier_bandwidth_hz: float = 20.0e6 / 256, cp_ratio: float = 0.25):
        self.subcarrier_bandwidth_hz = subcarrier_bandwidth_hz
        self.cp_ratio = cp_ratio

    def compute_candidate_rate_matrix(self, M_matrix: np.ndarray) -> np.ndarray:
        """
        Computes rate_candidate[k,n] = B_sub * log2(M_candidate[k,n])
        for a candidate modulation matrix M (shape K x N).
        """
        M_matrix = np.asarray(M_matrix, dtype=int)
        K, N = M_matrix.shape
        rate_matrix = np.zeros((K, N), dtype=float)

        for k in range(K):
            for n in range(N):
                M = M_matrix[k, n]
                if M > 1:
                    rate_matrix[k, n] = self.subcarrier_bandwidth_hz * np.log2(M)

        return rate_matrix

    def compute_device_rates(
        self,
        rho: np.ndarray,
        M_matrix: np.ndarray,
        device_ids: List[int]
    ) -> Dict[int, float]:
        """
        Computes total achievable raw PHY data rate per device k:
            R_k = B_sub * sum_n (rho[k,n] * log2(M[k,n]))
            
        Args:
            rho: Binary allocation matrix (shape K x N).
            M_matrix: Selected modulation order matrix (shape K x N).
            device_ids: List of device IDs corresponding to rows of rho.
            
        Returns:
            Dictionary device_id -> rate_bps.
        """
        rho = np.asarray(rho, dtype=float)
        M_matrix = np.asarray(M_matrix, dtype=int)
        K, N = rho.shape

        rates = {}
        for idx, dev_id in enumerate(device_ids):
            dev_rate = 0.0
            for n in range(N):
                if rho[idx, n] > 0.5:
                    M = M_matrix[idx, n]
                    if M > 1:
                        dev_rate += self.subcarrier_bandwidth_hz * np.log2(M)
            rates[dev_id] = float(dev_rate)

        return rates

    def compute_sum_rate(self, device_rates: Dict[int, float]) -> float:
        """Computes sum rate R_sum = sum_k R_k across all devices."""
        return float(sum(device_rates.values()))
