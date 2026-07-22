# allocation.py
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from VLCL_AI.adaptive.resource_mask import ResourceMask
from VLCL_AI.adaptive.qos import QoSEvaluator, QoSStatus

class TwoStageSubcarrierAllocator:
    """
    Deterministic Two-Stage QoS-Aware Subcarrier Allocator for Module 6.
    
    Constructs binary allocation matrix rho[k, n] in {0, 1} satisfying:
        sum_k rho[k, n] <= 1  for all n in N_comm
        rho[k, n] = 0         for locked/non-comm subcarriers
        
    Stage A (QoS Satisfaction):
        Iteratively allocates subcarriers to unsatisfied users (R_k < R_min_k)
        maximizing incremental rate progress.
        
    Stage B (Surplus Allocation):
        Allocates remaining available subcarriers to users providing the maximum
        incremental rate gain delta R_{k,n}.
        
    Deterministic Tie-Breaking Rules:
        1. Higher candidate rate gain delta R_{k,n}
        2. Higher subcarrier SNR gamma_{k,n}
        3. Lower device ID k
        4. Lower subcarrier index n
    """

    def __init__(self, subcarrier_bandwidth_hz: float = 20.0e6 / 256):
        self.subcarrier_bandwidth_hz = subcarrier_bandwidth_hz

    def allocate(
        self,
        device_ids: List[int],
        available_subcarriers: List[int],
        candidate_rate_matrix: np.ndarray, # shape (K, N_subcarriers)
        snr_matrix: np.ndarray,             # shape (K, N_subcarriers)
        min_rates_bps: Dict[int, float],     # device_id -> R_min_k
        mode: str = "ADAPTIVE"
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Executes two-stage subcarrier allocation.
        
        Args:
            device_ids: Ordered list of device IDs [1..K].
            available_subcarriers: List of unassigned communication subcarrier indices.
            candidate_rate_matrix: Precomputed candidate achievable rate for device k, carrier n.
            snr_matrix: Precomputed linear SNR for device k, carrier n.
            min_rates_bps: Required minimum QoS rate per device.
            mode: "ADAPTIVE" or "STATIC".
            
        Returns:
            Tuple of (rho_matrix, unused_subcarriers_list).
            rho_matrix shape is (K, total_subcarriers).
        """
        K = len(device_ids)
        total_subcarriers = candidate_rate_matrix.shape[1]
        rho = np.zeros((K, total_subcarriers), dtype=int)
        
        dev_to_idx = {dev_id: idx for idx, dev_id in enumerate(device_ids)}
        remaining_carriers = set(available_subcarriers)
        
        current_rates = {dev_id: 0.0 for dev_id in device_ids}

        if mode == "STATIC":
            # Equal / round-robin allocation across available subcarriers
            sorted_carriers = sorted(list(remaining_carriers))
            for i, sc_idx in enumerate(sorted_carriers):
                dev_id = device_ids[i % K]
                idx = dev_to_idx[dev_id]
                rho[idx, sc_idx] = 1
            return rho, []

        # ===================================================================
        # STAGE A: QoS SATISFACTION
        # ===================================================================
        while remaining_carriers:
            # Check which users are still unsatisfied: R_k < R_min_k
            unsatisfied_dev_ids = [
                d for d in device_ids if current_rates[d] < min_rates_bps.get(d, 0.0) - 1e-6
            ]
            if not unsatisfied_dev_ids:
                break # All QoS requirements satisfied! Move to Stage B.

            # Find best candidate (dev_id, sc_idx) among unsatisfied users
            best_candidate = None
            best_key = None # (rate_gain, snr, -dev_id, -sc_idx)

            for dev_id in unsatisfied_dev_ids:
                k_idx = dev_to_idx[dev_id]
                for sc_idx in remaining_carriers:
                    gain = candidate_rate_matrix[k_idx, sc_idx]
                    if gain <= 0.0:
                        continue # Unusable carrier for this user
                    snr_val = snr_matrix[k_idx, sc_idx]

                    # Deterministic tie-breaking key
                    key = (gain, snr_val, -dev_id, -sc_idx)
                    if best_key is None or key > best_key:
                        best_key = key
                        best_candidate = (dev_id, sc_idx, gain)

            if best_candidate is None:
                # No unsatisfied user can make progress with remaining carriers
                break

            # Assign carrier to best candidate
            sel_dev_id, sel_sc_idx, sel_gain = best_candidate
            sel_k_idx = dev_to_idx[sel_dev_id]

            rho[sel_k_idx, sel_sc_idx] = 1
            current_rates[sel_dev_id] += sel_gain
            remaining_carriers.remove(sel_sc_idx)

        # ===================================================================
        # STAGE B: SURPLUS RESOURCE ALLOCATION
        # ===================================================================
        while remaining_carriers:
            best_candidate = None
            best_key = None

            for dev_id in device_ids:
                k_idx = dev_to_idx[dev_id]
                for sc_idx in remaining_carriers:
                    gain = candidate_rate_matrix[k_idx, sc_idx]
                    if gain <= 0.0:
                        continue
                    snr_val = snr_matrix[k_idx, sc_idx]

                    key = (gain, snr_val, -dev_id, -sc_idx)
                    if best_key is None or key > best_key:
                        best_key = key
                        best_candidate = (dev_id, sc_idx, gain)

            if best_candidate is None:
                # Remaining carriers cannot be used by any user at valid modulation
                break

            sel_dev_id, sel_sc_idx, sel_gain = best_candidate
            sel_k_idx = dev_to_idx[sel_dev_id]

            rho[sel_k_idx, sel_sc_idx] = 1
            current_rates[sel_dev_id] += sel_gain
            remaining_carriers.remove(sel_sc_idx)

        unused_subcarriers = sorted(list(remaining_carriers))
        return rho, unused_subcarriers
