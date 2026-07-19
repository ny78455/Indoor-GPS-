# rate.py
import numpy as np
from typing import Dict, Any, List

class RateCalculator:
    """
    Computes communication rates, spectral efficiency, and effective throughput.
    Supports generalized variable subcarrier-bandwidth structures.
    """

    @staticmethod
    def compute_user_rates(
        allocated_subcarriers_indices: List[int],
        subcarrier_bandwidths: np.ndarray,      # Array of B_n for all N subcarriers
        modulation_orders: np.ndarray,           # Array of M_n for all N subcarriers
        cp_ratio: float = 0.125,
        pilot_indices: List[int] = None,
        ber: float = 0.0,
        total_system_bandwidth: float = 20e6
    ) -> Dict[str, float]:
        """
        Computes rate metrics for a user k.
        
        Args:
            allocated_subcarriers_indices (list): Indices of active communication subcarriers assigned to this user.
            subcarrier_bandwidths (np.ndarray): Bandwidth (Hz) of each subcarrier in the grid.
            modulation_orders (np.ndarray): Modulation order (M_n) of each subcarrier.
            cp_ratio: Cyclic prefix ratio (e.g. 0.125).
            pilot_indices: List of pilot subcarrier indices.
            ber: Bit Error Rate (used to penalize throughput).
            total_system_bandwidth: Total system bandwidth (used for spectral efficiency).
        """
        if not allocated_subcarriers_indices:
            return {
                "raw_rate_bps": 0.0,
                "effective_throughput_bps": 0.0,
                "spectral_efficiency": 0.0
            }
            
        raw_rate = 0.0
        active_sc_count = len(allocated_subcarriers_indices)
        
        # Calculate raw PHY rate: sum_n (B_n * log2(M_n))
        for idx in allocated_subcarriers_indices:
            b_n = subcarrier_bandwidths[idx]
            m_n = modulation_orders[idx]
            if m_n > 1:
                k_n = np.log2(m_n)
                raw_rate += b_n * k_n
                
        # Overhead factors
        # 1. Cyclic prefix overhead: cp_overhead = cp_ratio / (1 + cp_ratio)
        # e.g., if cp_ratio = 0.125, factor = 0.125 / 1.125 = 11.1% overhead
        # Symbol efficiency = 1 / (1 + cp_ratio)
        symbol_efficiency = 1.0 / (1.0 + cp_ratio)
        
        # 2. Pilot overhead
        pilot_efficiency = 1.0
        if pilot_indices and active_sc_count > 0:
            # Fraction of communication + pilot carriers used for pilots
            total_pilots_used = sum(1 for idx in pilot_indices if idx in allocated_subcarriers_indices)
            if total_pilots_used < active_sc_count:
                pilot_efficiency = (active_sc_count - total_pilots_used) / active_sc_count
                
        # 3. BER/Packet-error penalty (Goodput)
        # Under a simple model, throughput degrades with bit errors.
        # Often modeled as (1 - BER) or (1 - BER)^k. We can use a linear penalty (1 - 2 * BER) capped at 0.
        ber_efficiency = np.maximum(0.0, 1.0 - ber)
        
        # Effective throughput (Goodput)
        effective_throughput = raw_rate * symbol_efficiency * pilot_efficiency * ber_efficiency
        
        # Spectral Efficiency (bits/s/Hz)
        spectral_efficiency = raw_rate / total_system_bandwidth if total_system_bandwidth > 0 else 0.0
        
        return {
            "raw_rate_bps": float(raw_rate),
            "effective_throughput_bps": float(effective_throughput),
            "spectral_efficiency": float(spectral_efficiency)
        }
