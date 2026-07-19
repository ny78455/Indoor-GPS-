# frame.py
from dataclasses import dataclass, field
import numpy as np
from typing import Optional, List

@dataclass
class CommunicationFrame:
    frame_id: int
    user_id: int
    payload_bits: np.ndarray
    modulation_order: int
    subcarrier_indices: np.ndarray
    pilot_indices: np.ndarray
    qam_symbols: np.ndarray
    frequency_symbols: np.ndarray
    time_waveform: np.ndarray
    sample_rate: float
    cyclic_prefix_length: int
    metadata: dict = field(default_factory=dict)
