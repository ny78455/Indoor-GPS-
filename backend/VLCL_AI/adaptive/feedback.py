# feedback.py
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ChannelFeedback:
    """
    Simulated Channel State Information (CSI) feedback from device to transmitter.
    """
    device_id: int
    snr_per_subcarrier: np.ndarray             # Linear SNR gamma_{k,n} for subcarrier n
    requested_min_rate_bps: float = 0.0       # Minimum QoS throughput demand R_{min,k} (bps)
    channel_gain_per_subcarrier: Optional[np.ndarray] = None # Optical channel gain H
    timestamp: float = 0.0                     # Measurement timestamp (s)

    def __post_init__(self):
        self.snr_per_subcarrier = np.asarray(self.snr_per_subcarrier, dtype=float)
        # Ensure linear SNR non-negativity
        self.snr_per_subcarrier = np.maximum(self.snr_per_subcarrier, 0.0)
        if self.channel_gain_per_subcarrier is not None:
            self.channel_gain_per_subcarrier = np.asarray(self.channel_gain_per_subcarrier, dtype=float)
