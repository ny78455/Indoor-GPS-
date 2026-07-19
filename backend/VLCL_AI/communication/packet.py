# packet.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Packet:
    packet_id: int
    payload_bits: np.ndarray
    timestamp: float
