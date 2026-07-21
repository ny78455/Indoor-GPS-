# channel_interface.py
# Phase F Audit Result: PASS (with one fix applied — see below)
# Verified:
#   - H_total(f) = H_optical * H_LED(f): correct frequency-selective composition
#   - FFT-domain channel application is correct
#   - Module 2 PhysicsState consumed correctly (total_gains, noise_variances)
#   - FIX_REQUIRED: rng seeded with fixed seed=42 per call → deterministic non-random noise
#     Fixed below: rng = np.random.default_rng(seed=None) → truly random each call
import numpy as np
from typing import Dict, Any, Union
from VLCL_AI.physics.physics_engine import PhysicsState
from VLCL_AI.communication.led_frequency_response import LEDFrequencyResponse

class CommunicationChannelInterface:
    """
    Consumes PhysicsState from Module 2 and applies physical optical channel gains,
    frequency-selective LED responses, multipath propagation, and physical noise injection.
    """

    def __init__(self, led_response: LEDFrequencyResponse, noise_seed: int = None):
        self.led_response = led_response
        # Phase F fix: seed=None produces truly random noise each call.
        # Pass a fixed integer only for reproducible unit tests.
        self.noise_seed = noise_seed

    def get_frequency_response(self, physics_state: PhysicsState, led_id: int, frequencies: np.ndarray) -> np.ndarray:
        """
        Computes the complete frequency-selective channel gain H_total(f).
        H_total(f) = H_optical * H_LED(f)
        """
        h_optical = physics_state.total_gains.get(led_id, 0.0)
        h_led = self.led_response.complex_response(frequencies)
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
        frequencies = np.fft.fftfreq(n_samples, d=1.0 / sample_rate)

        # Get frequency-selective channel response and apply
        H = self.get_frequency_response(physics_state, led_id, frequencies)
        Y = X * H

        # Transform back to time-domain
        rx_waveform = np.real(np.fft.ifft(Y))

        # 2. Add physical noise
        noise_var = physics_state.noise_variances.get(led_id, 1e-12)
        std_noise = np.sqrt(noise_var)

        # Phase F fix (M3-F-001): seed=None → truly random noise each simulation step.
        # Previously seeded with 42 → same noise pattern on every call → NOT random.
        rng = np.random.default_rng(seed=self.noise_seed)
        noise_samples = rng.normal(0, std_noise, size=n_samples)

        return rx_waveform + noise_samples
