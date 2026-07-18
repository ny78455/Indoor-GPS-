# signal.py
import numpy as np
from typing import Union, Dict, Any, List

def convert_optical_to_electrical(
    received_optical_powers: List[float],
    responsivity: float = 0.54,
    gain_m: float = 1.0,
    tia_gain: float = 1e4,
    adc_resolution_bits: int = 12,
    adc_voltage_range: float = 3.3
) -> Dict[str, Any]:
    """
    Transforms optical powers (W) from multiple LEDs into aggregate and individual photocurrents,
    voltages, and simulates ADC quantization.
    This output matches the specifications of future OFDM inputs.
    """
    optical_sum = sum(received_optical_powers)
    
    # Calculate individual currents
    currents = [p * responsivity * gain_m for p in received_optical_powers]
    total_current = sum(currents)
    
    # Calculate voltages via TIA amplifier
    voltages = [i * tia_gain for i in currents]
    total_voltage = total_current * tia_gain
    
    # ADC Quantization step
    # Max value = 2^bits - 1
    max_adc_val = (2 ** adc_resolution_bits) - 1
    quantized_voltage = np.clip(total_voltage, 0.0, adc_voltage_range)
    adc_value = int((quantized_voltage / adc_voltage_range) * max_adc_val)
    
    return {
        "total_optical_power_received": optical_sum,
        "individual_currents": currents,
        "total_current": total_current,
        "individual_voltages": voltages,
        "total_voltage": total_voltage,
        "adc_quantized_value": adc_value,
        "adc_voltage_range": adc_voltage_range,
        "adc_resolution_bits": adc_resolution_bits
    }
