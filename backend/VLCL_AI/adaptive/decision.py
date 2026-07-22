# decision.py
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

@dataclass
class AllocationDecision:
    """
    Data contract output from Module 6 AdaptiveTransmissionEngine.
    Passed to Module 5 (IntegratedVLCLEngine) for waveform synthesis.
    """
    rho: np.ndarray                            # Binary allocation matrix shape (K, N_subcarriers)
    modulation_map: Dict[Tuple[int, int], int] # (device_id, subcarrier_index) -> M
    predicted_ber_map: Dict[Tuple[int, int], float] # (device_id, subcarrier_index) -> BER
    achievable_rates_bps: Dict[int, float]     # device_id -> rate (bps)
    sum_rate_bps: float                        # System sum throughput R_sum (bps)
    qos_satisfied: Dict[int, bool]             # device_id -> bool
    qos_deficits_bps: Dict[int, float]         # device_id -> deficit (bps)
    qos_status: str                            # "FEASIBLE", "PARTIALLY_FEASIBLE", "INFEASIBLE_QOS"
    unused_subcarriers: List[int]              # Subcarriers left unassigned
    diagnostics: Dict[str, Any] = field(default_factory=dict) # Telemetry details

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return {
            "sum_rate_bps": float(self.sum_rate_bps),
            "achievable_rates_bps": {int(k): float(v) for k, v in self.achievable_rates_bps.items()},
            "qos_status": str(self.qos_status),
            "qos_satisfied": {int(k): bool(v) for k, v in self.qos_satisfied.items()},
            "qos_deficits_bps": {int(k): float(v) for k, v in self.qos_deficits_bps.items()},
            "unused_subcarriers_count": len(self.unused_subcarriers),
            "diagnostics": self.diagnostics
        }
