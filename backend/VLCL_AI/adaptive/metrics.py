# metrics.py
import numpy as np
from typing import Dict, List, Any

class AdaptiveMetrics:
    """
    Computes diagnostic and telemetry metrics for Module 6.
    """

    @staticmethod
    def compute_jains_fairness_index(rates: Dict[int, float]) -> float:
        """
        Computes Jain's Fairness Index:
            J = (sum_k R_k)^2 / (K * sum_k R_k^2)
        Returns 1.0 if all rates are equal or if K <= 1.
        """
        r_vals = np.array(list(rates.values()), dtype=float)
        K = len(r_vals)
        if K <= 1:
            return 1.0

        sum_r = float(np.sum(r_vals))
        sum_sq_r = float(np.sum(r_vals ** 2))

        if sum_sq_r == 0.0:
            return 1.0

        return float((sum_r ** 2) / (K * sum_sq_r))

    @staticmethod
    def compute_telemetry(
        sum_rate_bps: float,
        achievable_rates_bps: Dict[int, float],
        min_rates_bps: Dict[int, float],
        total_bandwidth_hz: float,
        num_allocated_comm_subcarriers: int,
        total_comm_subcarriers: int,
        modulation_map: Dict[Any, int]
    ) -> Dict[str, Any]:
        """
        Compiles comprehensive telemetry dictionary.
        """
        jains_fairness = AdaptiveMetrics.compute_jains_fairness_index(achievable_rates_bps)
        spectral_efficiency = sum_rate_bps / total_bandwidth_hz if total_bandwidth_hz > 0 else 0.0
        
        utilization_ratio = (
            num_allocated_comm_subcarriers / total_comm_subcarriers
            if total_comm_subcarriers > 0 else 0.0
        )

        mod_orders = list(modulation_map.values())
        avg_bits_per_symbol = float(np.mean([np.log2(m) if m > 1 else 0.0 for m in mod_orders])) if mod_orders else 0.0

        return {
            "sum_rate_bps": float(sum_rate_bps),
            "spectral_efficiency_bps_hz": float(spectral_efficiency),
            "jains_fairness_index": float(jains_fairness),
            "subcarrier_utilization_ratio": float(utilization_ratio),
            "allocated_subcarrier_count": int(num_allocated_comm_subcarriers),
            "total_comm_subcarrier_count": int(total_comm_subcarriers),
            "average_bits_per_symbol": float(avg_bits_per_symbol)
        }
