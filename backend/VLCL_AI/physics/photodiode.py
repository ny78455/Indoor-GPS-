# photodiode.py
from dataclasses import dataclass
from typing import Union, Dict, Any
import numpy as np
from VLCL_AI.physics.constants import DEFAULT_RESPONSIVITY, DEFAULT_DARK_CURRENT, DEFAULT_CAPACITANCE, DEFAULT_BANDWIDTH, DEFAULT_TRANSIMPEDANCE_GAIN, DEFAULT_AMBIENT_TEMPERATURE

@dataclass
class Photodiode:
    area: float = 1e-4  # m^2
    responsivity: float = DEFAULT_RESPONSIVITY  # A/W
    capacitance: float = DEFAULT_CAPACITANCE  # F
    dark_current: float = DEFAULT_DARK_CURRENT  # A
    gain: float = 1.0  # APD multiplication gain M
    bandwidth: float = DEFAULT_BANDWIDTH  # Hz
    temperature: float = DEFAULT_AMBIENT_TEMPERATURE  # K
    tia_gain: float = DEFAULT_TRANSIMPEDANCE_GAIN  # V/A (Transimpedance Amplifier Ohm gain)

    def convert_power_to_current(self, optical_power: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Converts optical power into photo-current.
        I_photo = P_opt * R * M
        """
        return optical_power * self.responsivity * self.gain

    def generate_voltage(self, current: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Converts photodiode current into voltage using TIA gain.
        V_out = I_photo * R_tia
        """
        # Include dark current contribution
        total_current = current + self.dark_current * self.gain
        return total_current * self.tia_gain

    def process_optical_power(self, optical_power: Union[float, np.ndarray]) -> Dict[str, Union[float, np.ndarray]]:
        """
        Simulates the entire optoelectronic transduction pipeline.
        Optical Power -> Photo-current -> Output Voltage
        """
        photo_current = self.convert_power_to_current(optical_power)
        voltage = self.generate_voltage(photo_current)
        
        return {
            "photo_current": photo_current,
            "voltage": voltage
        }
