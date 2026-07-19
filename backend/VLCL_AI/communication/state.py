# state.py
from dataclasses import dataclass, field
import numpy as np
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class CommunicationState:
    """
    Immutable representation of the physical-layer communication state.
    Calculated per simulation frame. Keeps high-resolution wave data separate
    from summary metrics to optimize network payloads.
    """
    simulation_time: float
    
    transmitted_bits: np.ndarray
    received_bits: np.ndarray
    
    qam_tx_symbols: np.ndarray
    qam_rx_symbols: np.ndarray
    
    ofdm_tx_waveform: np.ndarray
    ofdm_rx_waveform: np.ndarray
    
    frequency_grid: np.ndarray
    
    active_subcarriers: List[int]
    subcarrier_bandwidths: np.ndarray
    subcarrier_powers: np.ndarray
    subcarrier_assignments: Dict[int, Optional[int]]
    modulation_orders: np.ndarray
    
    channel_response: np.ndarray
    
    snr_per_subcarrier: np.ndarray
    ber_per_subcarrier: np.ndarray
    
    ber_per_user: Dict[int, float]
    evm_per_user: Dict[int, float]
    
    rate_per_user: Dict[int, float]
    sum_rate: float
    spectral_efficiency: float
    effective_throughput: float
    
    papr: float
    clipping_ratio: float
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Formats a lightweight dictionary containing only key KPIs for the UI."""
        return {
            "simulation_time": self.simulation_time,
            "sum_rate_mbps": float(self.sum_rate / 1e6),
            "effective_throughput_mbps": float(self.effective_throughput / 1e6),
            "spectral_efficiency": float(self.spectral_efficiency),
            "papr_db": float(self.papr),
            "clipping_ratio_pct": float(self.clipping_ratio),
            "ber_per_user": {str(uid): float(ber) for uid, ber in self.ber_per_user.items()},
            "evm_per_user_pct": {str(uid): float(evm * 100.0) for uid, evm in self.evm_per_user.items()},
            "rate_per_user_mbps": {str(uid): float(rate / 1e6) for uid, rate in self.rate_per_user.items()},
            "metadata": self.metadata
        }

    def to_detailed_dict(self) -> Dict[str, Any]:
        """Formats detailed state parameters suitable for analysis or JSON APIs."""
        summary = self.to_summary_dict()
        details = {
            "active_subcarriers": self.active_subcarriers,
            "snr_per_subcarrier": self.snr_per_subcarrier.tolist(),
            "ber_per_subcarrier": self.ber_per_subcarrier.tolist(),
            "channel_response_magnitude": np.abs(self.channel_response).tolist(),
            "subcarrier_powers": self.subcarrier_powers.tolist(),
            "subcarrier_assignments": {str(k): v for k, v in self.subcarrier_assignments.items()},
            "modulation_orders": self.modulation_orders.tolist()
        }
        summary.update(details)
        return summary
