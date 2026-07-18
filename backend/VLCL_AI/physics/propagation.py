# propagation.py
import numpy as np
from typing import Union, Dict, Any, Tuple
from VLCL_AI.physics.constants import SPEED_OF_LIGHT

def compute_propagation(
    tx_pos: Union[list, np.ndarray],
    rx_pos: Union[list, np.ndarray],
) -> Dict[str, float]:
    """
    Computes direct line-of-sight propagation metrics between a transmitter and a receiver.
    Returns:
        Dict containing distance, travel_time (optical delay), and free_space_attenuation.
    """
    tx = np.array(tx_pos, dtype=float)
    rx = np.array(rx_pos, dtype=float)
    
    vec = rx - tx
    distance = float(np.linalg.norm(vec))
    
    if distance <= 0:
        travel_time = 0.0
        free_space_atten = 1.0
    else:
        travel_time = float(distance / SPEED_OF_LIGHT)
        # Free space attenuation can be modeled by 1 / (4 * pi * d^2) or standard geometric 1/d^2 factor
        free_space_atten = float(1.0 / (distance ** 2))
        
    return {
        "distance": distance,
        "travel_time": travel_time,
        "free_space_attenuation": free_space_atten
    }
