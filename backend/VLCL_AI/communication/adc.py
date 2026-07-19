# adc.py
import numpy as np
from typing import Dict, Any

class ADCModel:
    """
    Models an Analog-to-Digital Converter (ADC).
    Simulates resolution quantization and full-scale saturation effects.
    """
    
    def __init__(
        self,
        sample_rate_hz: float = 50e6,
        bit_depth: int = 12,
        full_scale_voltage: float = 2.0,
        mode: str = "ideal"
    ):
        self.sample_rate_hz = sample_rate_hz
        self.bit_depth = bit_depth
        self.full_scale_voltage = full_scale_voltage
        self.mode = mode.lower()

    def process(self, analog_waveform: np.ndarray) -> np.ndarray:
        """
        Processes the incoming continuous-time analog electrical signal.
        Applies quantization and clipping (saturation) if configured as 'quantized'.
        """
        if self.mode == "ideal":
            return analog_waveform
            
        # Clipping/Saturation at full-scale voltage
        # Assuming single-ended input from 0 to full_scale_voltage
        saturated_waveform = np.clip(analog_waveform, 0.0, self.full_scale_voltage)
        
        # Quantization
        levels = 2 ** self.bit_depth
        quantization_step = self.full_scale_voltage / (levels - 1)
        
        # Quantize by rounding to nearest level
        quantized_waveform = np.round(saturated_waveform / quantization_step) * quantization_step
        
        return quantized_waveform
