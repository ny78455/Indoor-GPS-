# calibration.py
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

class LocalizationBiasModel:
    """Simulates physical hardware impairments such as LED delay biases and clock phase offsets."""
    
    def __init__(
        self,
        led_ids: List[int],
        constant_delay_bias_s: Optional[Dict[int, float]] = None,
        random_delay_jitter_s: float = 0.0,
        phase_offset_rad: Optional[Dict[int, float]] = None,
        seed: int = 42
    ):
        self.led_ids = led_ids
        self.rng = np.random.default_rng(seed)
        
        # Initialize delay biases
        self.delay_biases = {}
        for lid in led_ids:
            bias = 0.0
            if constant_delay_bias_s and lid in constant_delay_bias_s:
                bias += constant_delay_bias_s[lid]
            if random_delay_jitter_s > 0:
                bias += self.rng.normal(0, random_delay_jitter_s)
            self.delay_biases[lid] = bias
            
        # Initialize phase offsets
        self.phase_offsets = {}
        for lid in led_ids:
            phase = 0.0
            if phase_offset_rad and lid in phase_offset_rad:
                phase += phase_offset_rad[lid]
            self.phase_offsets[lid] = phase

    def apply_bias_to_delay(self, led_id: int, delay_s: float) -> float:
        """Adds delay bias to a physical propagation delay."""
        return delay_s + self.delay_biases.get(led_id, 0.0)

    def apply_bias_to_phase(self, led_id: int, phase_rad: float) -> float:
        """Adds phase offset to physical tone phase."""
        return phase_rad + self.phase_offsets.get(led_id, 0.0)


class LocalizationCalibrator:
    """Maintains calibrated physical offsets for each emitter to mitigate systematic errors."""
    
    def __init__(
        self,
        calibrated_delay_biases: Optional[Dict[int, float]] = None,
        calibrated_phase_biases: Optional[Dict[int, float]] = None
    ):
        self.delay_biases = calibrated_delay_biases or {}
        self.phase_biases = calibrated_phase_biases or {}

    def compensate_delay(self, led_id: int, delay_s: float) -> float:
        """Subtracts calibrated delay bias."""
        return delay_s - self.delay_biases.get(led_id, 0.0)

    def compensate_phase(self, led_id: int, phase_rad: float) -> float:
        """Subtracts calibrated phase bias."""
        return phase_rad - self.phase_biases.get(led_id, 0.0)


class ShiftingErrorMitigator:
    """Compensates raw DPD phases or distance differences using calibrated system parameters."""
    
    def __init__(self, calibrator: LocalizationCalibrator):
        self.calibrator = calibrator

    def mitigate_phases(
        self,
        raw_phases: np.ndarray,
        frequency_plan: Any,
        tone_to_led_map: Dict[int, List[int]]
    ) -> np.ndarray:
        """
        Subtracts systematic phase shifts introduced by electronic delays or filter group delays.
        For example: theta_1_corr = theta_1_raw - Delta_theta_1_cal.
        We can calculate systematic phase bias directly from the calibrator's LED delay/phase biases.
        """
        corrected = np.copy(raw_phases)
        c = 299792458.0
        
        # Equation-by-equation systematic phase bias calculation
        # theta_1 = w1*t1 + w3*t3 - 2*w2*t2
        # theta_2 = w2*t2 + w4*t4 - 2*w3*t3
        # theta_3 = w3*t3 + w5*t5 - 2*w4*t4
        eq_coeffs = [
            {1: 1.0, 2: -2.0, 3: 1.0}, # eq 1
            {2: 1.0, 3: -2.0, 4: 1.0}, # eq 2
            {3: 1.0, 4: -2.0, 5: 1.0}  # eq 3
        ]
        
        for eq_idx in range(len(raw_phases)):
            coeffs = eq_coeffs[eq_idx]
            bias_sum = 0.0
            
            for tone_id, multiplier in coeffs.items():
                leds = tone_to_led_map.get(tone_id, [1])
                primary_led = leds[0]
                omega = frequency_plan.angular_frequencies[tone_id - 1]
                
                # Systematic delay/phase offset for primary_led
                led_delay_bias = self.calibrator.delay_biases.get(primary_led, 0.0)
                led_phase_bias = self.calibrator.phase_biases.get(primary_led, 0.0)
                
                # Phase offset contribution = multiplier * (omega * delay_bias + phase_bias)
                bias_sum += multiplier * (omega * led_delay_bias + led_phase_bias)
                
            corrected[eq_idx] -= bias_sum
            
        return corrected

    def mitigate_distance_differences(
        self,
        raw_differences: Dict[Tuple[int, int], float]
    ) -> Dict[Tuple[int, int], float]:
        """
        Subtracts remaining distance differences biases directly if configured.
        """
        corrected = {}
        for (led_j, led_ref), diff in raw_differences.items():
            led_j_delay_bias = self.calibrator.delay_biases.get(led_j, 0.0)
            led_ref_delay_bias = self.calibrator.delay_biases.get(led_ref, 0.0)
            
            c = 299792458.0
            # Delta d bias = (delay_bias_j - delay_bias_ref) * c
            dist_bias = (led_j_delay_bias - led_ref_delay_bias) * c
            
            corrected[(led_j, led_ref)] = diff - dist_bias
            
        return corrected
