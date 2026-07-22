# water_filling.py
import numpy as np
from typing import Dict, List, Tuple, Optional

class WaterFillingAllocator:
    """
    Implements classical water-filling power allocation for a fixed set of subcarriers and fixed modulation order.
    P_n = max(0, nu - 1 / gamma_unit_n)
    s.t. sum(P_n) <= P_budget.
    """

    @staticmethod
    def allocate_power(
        unit_snrs: np.ndarray,
        p_budget: float,
        allocatable_mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calculates optimal electrical power per subcarrier given unit-power SNR values.

        Args:
            unit_snrs (np.ndarray): SNR per subcarrier when allocated 1.0 Watt (gamma_n / P_n).
            p_budget (float): Total electrical power budget to distribute across active carriers.
            allocatable_mask (np.ndarray, optional): Boolean mask of active subcarriers.

        Returns:
            np.ndarray: Allocated electrical power P_n for each subcarrier (same length as unit_snrs).
        """
        p_alloc = np.zeros_like(unit_snrs, dtype=float)

        if p_budget <= 1e-12:
            return p_alloc

        if allocatable_mask is None:
            mask = unit_snrs > 1e-12
        else:
            mask = allocatable_mask & (unit_snrs > 1e-12)

        indices = np.where(mask)[0]
        num_active = len(indices)

        if num_active == 0:
            return p_alloc

        # Unit SNR values for active carriers
        active_snrs = unit_snrs[indices]
        
        # Inverse channel qualities alpha_i = 1 / gamma_unit_i
        alpha = 1.0 / active_snrs
        
        # Sort alpha ascending
        sort_idx = np.argsort(alpha)
        alpha_sorted = alpha[sort_idx]

        # Iteratively search for water level nu_K
        nu = 0.0
        k_opt = 0
        for k in range(1, num_active + 1):
            temp_nu = (p_budget + np.sum(alpha_sorted[:k])) / k
            if temp_nu > alpha_sorted[k - 1]:
                nu = temp_nu
                k_opt = k
            else:
                break

        if k_opt == 0:
            # Fallback: distribute power equally if channel is extremely weak
            p_alloc[indices] = p_budget / num_active
            return p_alloc

        # Calculate allocated power for active set
        power_active = np.maximum(0.0, nu - alpha)
        p_alloc[indices] = power_active

        # Fine numerical normalization to ensure exact sum(P_n) == p_budget
        sum_allocated = np.sum(p_alloc)
        if sum_allocated > 1e-12:
            p_alloc[indices] = p_alloc[indices] * (p_budget / sum_allocated)

        return p_alloc
