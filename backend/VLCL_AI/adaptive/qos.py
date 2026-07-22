# qos.py
from enum import Enum
from typing import Dict, List, Tuple, Any

class QoSStatus(Enum):
    FEASIBLE = "FEASIBLE"
    PARTIALLY_FEASIBLE = "PARTIALLY_FEASIBLE"
    INFEASIBLE_QOS = "INFEASIBLE_QOS"

class QoSEvaluator:
    """
    Evaluates QoS compliance (R_k >= R_min_k) and calculates deficit metrics.
    """

    @staticmethod
    def evaluate_qos(
        achievable_rates_bps: Dict[int, float],
        min_rates_bps: Dict[int, float]
    ) -> Tuple[Dict[int, bool], Dict[int, float], QoSStatus, float]:
        """
        Evaluates QoS satisfaction per device.
        
        Args:
            achievable_rates_bps: Dict device_id -> achieved rate R_k (bps).
            min_rates_bps: Dict device_id -> required rate R_min_k (bps).
            
        Returns:
            Tuple of (qos_satisfied_dict, qos_deficits_dict, qos_status, feasibility_ratio).
        """
        qos_satisfied = {}
        qos_deficits = {}
        satisfied_count = 0
        total_count = len(min_rates_bps)

        if total_count == 0:
            return {}, {}, QoSStatus.FEASIBLE, 1.0

        for dev_id, r_min in min_rates_bps.items():
            r_achieved = achievable_rates_bps.get(dev_id, 0.0)
            if r_achieved >= r_min - 1e-6: # Tolerance for float equality
                qos_satisfied[dev_id] = True
                qos_deficits[dev_id] = 0.0
                satisfied_count += 1
            else:
                qos_satisfied[dev_id] = False
                qos_deficits[dev_id] = float(r_min - r_achieved)

        feasibility_ratio = satisfied_count / total_count if total_count > 0 else 1.0

        if satisfied_count == total_count:
            status = QoSStatus.FEASIBLE
        elif satisfied_count > 0:
            status = QoSStatus.PARTIALLY_FEASIBLE
        else:
            status = QoSStatus.INFEASIBLE_QOS

        return qos_satisfied, qos_deficits, status, float(feasibility_ratio)
