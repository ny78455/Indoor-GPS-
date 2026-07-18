# multipath.py
import numpy as np
from typing import List, Dict, Any

def aggregate_channel_gains(
    los_gain: float,
    nlos_gain: float
) -> float:
    """
    Combines direct Line-of-Sight and diffuse multi-path components to calculate the total path loss.
    """
    return float(los_gain + nlos_gain)
