# constraint_evaluator.py
import numpy as np
from typing import Dict, List, Any, Optional
from VLCL_AI.adaptive.joint_state import ConstraintStatus

class ConstraintEvaluator:
    """
    Evaluates system constraint satisfaction across physical, localization, QoS, BER, and spectrum domains.
    Implements the strict priority hierarchy specified in Module 8.
    """

    def __init__(
        self,
        target_localization_error_m: float = 0.20,
        ber_max: float = 3.8e-3,
        per_led_max_power_w: float = 10.0,
        total_max_power_w: float = 40.0
    ):
        self.target_loc_error_m = target_localization_error_m
        self.ber_max = ber_max
        self.per_led_max_power_w = per_led_max_power_w
        self.total_max_power_w = total_max_power_w

    def evaluate(
        self,
        localization_error_m: float,
        achieved_rates_bps: Dict[int, float],
        min_rates_bps: Dict[int, float],
        per_device_ber: Dict[int, float],
        per_led_power_w: Dict[int, float],
        rho: np.ndarray,
        loc_indices: List[int]
    ) -> ConstraintStatus:
        """
        Evaluates all system constraints and returns structured status.
        """
        # 1. Physical Power Constraint
        power_excess = 0.0
        power_satisfied = True
        total_p = sum(per_led_power_w.values())
        if total_p > self.total_max_power_w + 1e-6:
            power_satisfied = False
            power_excess = max(power_excess, total_p - self.total_max_power_w)

        for led_id, p_val in per_led_power_w.items():
            if p_val > self.per_led_max_power_w + 1e-6:
                power_satisfied = False
                power_excess = max(power_excess, p_val - self.per_led_max_power_w)

        # 2. Localization Accuracy Constraint
        loc_satisfied = (localization_error_m <= self.target_loc_error_m + 1e-4)

        # 3. QoS Rate Constraint
        rate_deficits = {}
        qos_satisfied = True
        for dev_id, req_rate in min_rates_bps.items():
            ach_rate = achieved_rates_bps.get(dev_id, 0.0)
            if ach_rate < req_rate - 1.0: # Allow 1 bps rounding margin
                qos_satisfied = False
                rate_deficits[dev_id] = float(req_rate - ach_rate)

        # 4. BER Feasibility Constraint
        ber_excesses = {}
        ber_satisfied = True
        for dev_id, ber in per_device_ber.items():
            if ber > self.ber_max + 1e-6:
                ber_satisfied = False
                ber_excesses[dev_id] = float(ber - self.ber_max)

        # 5. Spectrum Uniqueness & Non-Overlap
        spectrum_satisfied = True
        K, N = rho.shape
        # Check subcarriers allocated to at most one user
        sc_allocation_counts = np.sum(rho, axis=0)
        if np.any(sc_allocation_counts > 1):
            spectrum_satisfied = False

        # Check localization subcarriers are reserved (rho = 0)
        loc_idx_list = list(loc_indices)
        if len(loc_idx_list) > 0 and np.any(rho[:, loc_idx_list] > 0):
            spectrum_satisfied = False

        overall_feasible = (
            power_satisfied and
            loc_satisfied and
            qos_satisfied and
            ber_satisfied and
            spectrum_satisfied
        )

        return ConstraintStatus(
            localization_satisfied=loc_satisfied,
            qos_satisfied=qos_satisfied,
            ber_satisfied=ber_satisfied,
            power_satisfied=power_satisfied,
            spectrum_satisfied=spectrum_satisfied,
            overall_feasible=overall_feasible,
            localization_error_m=float(localization_error_m),
            localization_target_m=float(self.target_loc_error_m),
            rate_deficits_bps=rate_deficits,
            ber_excesses=ber_excesses,
            power_excess_w=float(power_excess)
        )
