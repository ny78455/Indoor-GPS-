# channel_interface.py
import numpy as np
from typing import Dict, Any, Union
from VLCL_AI.physics.physics_engine import PhysicsState
from VLCL_AI.communication.led_frequency_response import LEDFrequencyResponse

class CommunicationChannelInterface:
    """
    Consumes PhysicsState from Module 2 and applies physical optical channel gains,
    frequency-selective LED responses, multipath propagation, and physical noise injection.
    """
    
    def __init__(self, led_response: LEDFrequencyResponse):
        self.led_response = led_response

    def get_frequency_response(self, physics_state: PhysicsState, led_id: int, frequencies: np.ndarray) -> np.ndarray:
        """
        Computes the complete frequency-selective channel gain H_total(f).
        H_total(f) = H_optical * H_LED(f)
        """
        # Retrieve direct + reflected optical gain from Module 2 physics state
        h_optical = physics_state.total_gains.get(led_id, 0.0)
        
        # Retrieve frequency response of the LED
        h_led = self.led_response.complex_response(frequencies)
        
        # Combine optical gain and LED bandwidth response
        return h_optical * h_led

    def propagate(
        self,
        tx_waveform: np.ndarray,
        physics_state: PhysicsState,
        led_id: int,
        sample_rate: float
    ) -> np.ndarray:
        """
        Propagates the real-valued time-domain drive signal through the channel.
        Applies frequency response via FFT-domain multiplication, scales by optical-electrical gain,
        and adds physical noise samples based on Module 2 calculations.
        """
        n_samples = len(tx_waveform)
        if n_samples == 0:
            return tx_waveform
            
        # 1. Transform signal to frequency domain
        X = np.fft.fft(tx_waveform)
        
        # Calculate frequency bins for each FFT point
        frequencies = np.fft.fftfreq(n_samples, d=1.0 / sample_rate)
        
        # Get frequency-selective channel response
        H = self.get_frequency_response(physics_state, led_id, frequencies)
        
        # Apply channel response
        Y = X * H
        
        # Transform back to time-domain (should be real-valued since H is symmetric for positive/negative frequencies)
        rx_waveform = np.real(np.fft.ifft(Y))
        
        # 2. Add Physical noise
        # Retrieve total physical noise variance (thermal + shot) from Module 2 physics state
        noise_var = physics_state.noise_variances.get(led_id, 1e-12)
        
        # Generate Gaussian noise samples
        # std_noise = sqrt(noise_variance)
        # Note: if noise_variance is physical, generate corresponding time-domain noise
        std_noise = np.sqrt(noise_var)
        rng = np.random.default_rng(42)
        noise_samples = rng.normal(0, std_noise, size=n_samples)
        
        return rx_waveform + noise_samples
