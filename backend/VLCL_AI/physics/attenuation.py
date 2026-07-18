# attenuation.py
import numpy as np
from typing import Union

def atmospheric_attenuation(distance: Union[float, np.ndarray], loss_coefficient_db_per_m: float) -> Union[float, np.ndarray]:
    """
    Computes atmospheric attenuation over a given distance using dB loss.
    Loss (linear) = 10 ^ (- (coef * distance) / 10)
    """
    db_loss = loss_coefficient_db_per_m * distance
    return 10.0 ** (-db_loss / 10.0)

def material_reflection_loss(reflectivity: float) -> float:
    """
    Computes reflection loss based on material reflectivity.
    """
    return float(np.clip(reflectivity, 0.0, 1.0))
