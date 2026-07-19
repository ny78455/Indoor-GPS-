# led_frequency_response.py
import numpy as np
from typing import Union

class LEDFrequencyResponse:
    """
    Models the non-flat frequency response of an LED.
    Typically modeled as a first-order low-pass filter.
    """
    
    def __init__(self, model_type: str = "first_order", cutoff_frequency_hz: float = 20e6):
        self.model_type = model_type.lower()
        self.cutoff_frequency_hz = cutoff_frequency_hz

    def complex_response(self, f: Union[float, np.ndarray]) -> Union[complex, np.ndarray]:
        """Returns the complex frequency response H(f)."""
        f_arr = np.asarray(f, dtype=float)
        
        if self.model_type == "flat":
            return np.ones_like(f_arr, dtype=complex)
            
        elif self.model_type == "first_order":
            # H(f) = 1 / (1 + j * f/fc)
            return 1.0 / (1.0 + 1j * (f_arr / self.cutoff_frequency_hz))
            
        else:
            # Fallback to flat
            return np.ones_like(f_arr, dtype=complex)

    def magnitude(self, f: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Returns the magnitude response |H(f)|."""
        return np.abs(self.complex_response(f))

    def phase(self, f: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Returns the phase response in radians."""
        return np.angle(self.complex_response(f))
