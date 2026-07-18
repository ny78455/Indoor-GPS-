# optical_power.py
import numpy as np
from typing import Union, Dict, Any

def compute_received_power(power: float, dc_gain: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes received optical power.
    P_rx = P_tx * H(0)
    """
    return power * dc_gain
