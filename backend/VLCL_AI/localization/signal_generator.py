# signal_generator.py
import numpy as np
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass, field
from VLCL_AI.localization.frequency_plan import LocalizationFrequencyPlan

@dataclass
class LocalizationFrame:
    """Represents a transmitted frame of localization tones."""
    frame_id: int
    timestamp: float
    frequency_plan: LocalizationFrequencyPlan
    powers: np.ndarray
    initial_phase: float
    sample_rate: float
    duration: float
    tone_to_led_map: Dict[int, List[int]]
    signal_mode: str  # "full_waveform" or "phase_equivalent"
    
    # Mode-dependent transmitted signals
    # For full_waveform: 2D array of shape (count, num_samples) representing tone time-series
    # For phase_equivalent: 1D complex array of shape (count,) representing complex phasors
    transmitted_signals: np.ndarray
    time_vector: Optional[np.ndarray] = None


class LocalizationSignalGenerator:
    """Generates the emitted signals from LEDs for localization."""
    
    def __init__(self, sample_rate_hz: float = 10.0e6, duration_s: float = 0.01, signal_mode: str = "phase_equivalent"):
        self.sample_rate = float(sample_rate_hz)
        self.duration = float(duration_s)
        self.signal_mode = signal_mode
        self.frame_counter = 0

    def generate_frame(
        self, 
        frequency_plan: LocalizationFrequencyPlan, 
        powers: Union[List[float], np.ndarray], 
        initial_phase: float = 0.0,
        tone_to_led_map: Optional[Dict[int, List[int]]] = None
    ) -> LocalizationFrame:
        """
        Generates a transmitted localization frame under configured mode.
        """
        self.frame_counter += 1
        powers = np.array(powers, dtype=np.float64)
        
        default_mapping = {1: [1], 2: [2], 3: [3], 4: [4], 5: [1]}
        mapping = tone_to_led_map or default_mapping
        
        num_tones = len(frequency_plan.frequencies)
        
        if self.signal_mode == "full_waveform":
            # Generate actual time vector
            num_samples = int(self.sample_rate * self.duration)
            t = np.arange(num_samples) / self.sample_rate
            
            # shape (num_tones, num_samples)
            signals = np.zeros((num_tones, num_samples), dtype=np.float64)
            for i in range(num_tones):
                freq = frequency_plan.frequencies[i]
                pwr = powers[i]
                # s_i(t) = sqrt(pwr) * sin(2*pi*f_i*t + phase)
                signals[i, :] = np.sqrt(pwr) * np.sin(2 * np.pi * freq * t + initial_phase)
                
            return LocalizationFrame(
                frame_id=self.frame_counter,
                timestamp=0.0,  # can be updated by caller
                frequency_plan=frequency_plan,
                powers=powers,
                initial_phase=initial_phase,
                sample_rate=self.sample_rate,
                duration=self.duration,
                tone_to_led_map=mapping,
                signal_mode=self.signal_mode,
                transmitted_signals=signals,
                time_vector=t
            )
        else:
            # Phase-equivalent mode
            # shape (num_tones,) complex phasors: sqrt(P) * e^{j * phi}
            # We model s_i(t) = sqrt(P) * sin(wt + phi). In complex form: sqrt(P) * e^{j * phi}
            phasors = np.sqrt(powers) * np.exp(1j * initial_phase)
            
            return LocalizationFrame(
                frame_id=self.frame_counter,
                timestamp=0.0,
                frequency_plan=frequency_plan,
                powers=powers,
                initial_phase=initial_phase,
                sample_rate=self.sample_rate,
                duration=self.duration,
                tone_to_led_map=mapping,
                signal_mode=self.signal_mode,
                transmitted_signals=phasors,
                time_vector=None
            )
