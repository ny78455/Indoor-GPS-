# modulation_controller.py
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from VLCL_AI.communication.ber import BERCalculator
from VLCL_AI.adaptive.snr_thresholds import SNRThresholdTable

class AdaptiveModulationController:
    """
    Adaptive Modulation Controller enforcing Eq. (17) and BER_max constraint.
    
    Determines highest feasible modulation order M for given linear SNR gamma_{k,n}
    such that BER_analytical(M, gamma_{k,n}) <= BER_max.
    """

    def __init__(
        self,
        ber_max: float = 3.8e-3,
        supported_modulations: List[int] = None,
        threshold_table: Optional[SNRThresholdTable] = None
    ):
        self.ber_max = ber_max
        self.supported_modulations = sorted(supported_modulations or [2, 4, 16, 64, 256])
        self.threshold_table = threshold_table or SNRThresholdTable(ber_max, self.supported_modulations)

    def select_modulation_order(self, snr_linear: float) -> Tuple[int, float, bool]:
        """
        Selects highest modulation order M satisfying BER(M, snr_linear) <= BER_max.
        
        Args:
            snr_linear: Linear dimensionless SNR gamma_{k,n}.
            
        Returns:
            Tuple of (M, predicted_ber, is_feasible).
            If no supported M satisfies the BER target, returns (0, 1.0, False).
        """
        snr_linear = float(max(snr_linear, 0.0))
        if snr_linear <= 0.0:
            return 0, 1.0, False

        best_M = 0
        best_ber = 1.0
        is_feasible = False

        # Evaluate candidate modulation orders from largest to smallest
        for M in reversed(self.supported_modulations):
            predicted_ber = float(BERCalculator.compute_analytical_qam(snr_linear, M))
            if predicted_ber <= self.ber_max + 1e-12: # Include tolerance for float comparison
                best_M = M
                best_ber = predicted_ber
                is_feasible = True
                break

        return best_M, best_ber, is_feasible

    def process_snr_matrix(self, snr_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Processes a 2D matrix of SNRs (shape K devices x N subcarriers).
        
        Returns:
            M_matrix: shape (K, N), integer modulation orders M.
            ber_matrix: shape (K, N), predicted analytical BERs.
            feasibility_matrix: shape (K, N), boolean feasibility flags.
        """
        snr_matrix = np.asarray(snr_matrix, dtype=float)
        K, N = snr_matrix.shape

        M_matrix = np.zeros((K, N), dtype=int)
        ber_matrix = np.ones((K, N), dtype=float)
        feasibility_matrix = np.zeros((K, N), dtype=bool)

        for k in range(K):
            for n in range(N):
                M, ber, feat = self.select_modulation_order(snr_matrix[k, n])
                M_matrix[k, n] = M
                ber_matrix[k, n] = ber
                feasibility_matrix[k, n] = feat

        return M_matrix, ber_matrix, feasibility_matrix
