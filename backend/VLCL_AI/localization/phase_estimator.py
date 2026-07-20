# phase_estimator.py
import numpy as np
import scipy.signal as signal
from typing import List, Dict, Any, Tuple, Optional
from VLCL_AI.localization.exceptions import SignalError
from VLCL_AI.localization.frequency_plan import LocalizationFrequencyPlan
from VLCL_AI.localization.filters import LocalizationBandpassFilter, LocalizationLowpassFilter, trim_transients

class PhaseEstimator:
    """Performs differential phase processing, I/Q extraction, phase estimation, and unwrapping."""
    
    def __init__(
        self,
        frequency_plan: LocalizationFrequencyPlan,
        sample_rate_hz: float,
        bp_bandwidth_hz: float = 20000.0,
        lp_cutoff_hz: float = 10000.0,
        filter_type: str = "butterworth",
        filter_order: int = 4,
        offline_zero_phase: bool = True
    ):
        self.plan = frequency_plan
        self.fs = sample_rate_hz
        self.bp_bandwidth = bp_bandwidth_hz
        self.lp_cutoff = lp_cutoff_hz
        self.filter_type = filter_type
        self.filter_order = filter_order
        self.offline_zero_phase = offline_zero_phase
        
        # We will dynamically instantiate filters for full waveform mode
        self.delta_f = self.plan.get_spacing()

    def process_full_waveform(self, r: np.ndarray, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Runs the full multi-stage DSP receiver chain:
        1. Band-pass filter r(t) at each frequency f_i to isolate tones s_i(t).
        2. Multiply adjacent tones to form difference-frequency products D_i(t).
        3. Band-pass filter D_i(t) at delta_f.
        4. Multiply adjacent differential signals D_i(t) * D_{i+1}(t) to form dual differentials.
        5. Extract I and Q components via LPF and Hilbert transform.
        6. Compute atan2 phase.
        """
        num_tones = len(self.plan.frequencies)
        num_samples = len(r)
        
        # 1. Band-pass filter to isolate each tone
        isolated_tones = []
        for freq in self.plan.frequencies:
            # We use a bandpass filter centered at freq, with width delta_f/2
            bp_tone = LocalizationBandpassFilter(
                center_freq_hz=freq,
                bandwidth_hz=self.delta_f * 0.8, # slightly wider than half spacing to avoid attenuation
                sample_rate_hz=self.fs,
                filter_type=self.filter_type,
                order=self.filter_order,
                offline_zero_phase=self.offline_zero_phase
            )
            isolated_tones.append(bp_tone.filter(r))
            
        # 2 & 3. Multiply adjacent tones and BPF at delta_f to get D1, D2, D3, D4
        D_signals = []
        for i in range(num_tones - 1):
            s_curr = isolated_tones[i]
            s_next = isolated_tones[i+1]
            
            # Multiplication
            mult_sig = s_curr * s_next
            
            # Bandpass filter at delta_f
            bp_diff = LocalizationBandpassFilter(
                center_freq_hz=self.delta_f,
                bandwidth_hz=self.bp_bandwidth,
                sample_rate_hz=self.fs,
                filter_type=self.filter_type,
                order=self.filter_order,
                offline_zero_phase=self.offline_zero_phase
            )
            D_signals.append(bp_diff.filter(mult_sig))
            
        # 4 & 5. Dual Differential and I/Q extraction
        # We want to extract 3 phase combinations: theta_1, theta_2, theta_3
        I_vals = np.zeros(num_tones - 2)
        Q_vals = np.zeros(num_tones - 2)
        
        # Lowpass filter
        lp_filt = LocalizationLowpassFilter(
            cutoff_hz=self.lp_cutoff,
            sample_rate_hz=self.fs,
            filter_type=self.filter_type,
            order=self.filter_order,
            offline_zero_phase=self.offline_zero_phase
        )
        
        for i in range(num_tones - 2):
            D_curr = D_signals[i]
            D_next = D_signals[i+1]
            
            # Analytical signal using Hilbert transform
            # Note: Hilbert transform shift
            # scipy.signal.hilbert returns real_signal + 1j * hilbert_transform
            analytic = signal.hilbert(D_next)
            D_next_hilb = np.imag(analytic)
            
            # Multiplications
            I_sig = D_curr * D_next
            Q_sig = D_curr * D_next_hilb
            
            # Lowpass filter
            I_filtered = lp_filt.filter(I_sig)
            Q_filtered = lp_filt.filter(Q_sig)
            
            # Trim transient regions (first and last 10% samples)
            I_trimmed = trim_transients(I_filtered, self.fs, len(r)/self.fs)
            Q_trimmed = trim_transients(Q_filtered, self.fs, len(r)/self.fs)
            
            # Extract DC averages
            I_vals[i] = np.mean(I_trimmed)
            Q_vals[i] = np.mean(Q_trimmed)
            
        # 6. Compute phase with atan2
        # theta_i = atan2(Q_i, I_i)
        # Note: Depending on multiplication order, we might get negative or positive sign.
        # We align with expected mathematical convention: theta_1 = w1*t1 + w3*t3 - 2*w2*t2
        phases = np.zeros(len(I_vals))
        for i in range(len(I_vals)):
            # Force phase relationship to align perfectly with:
            # theta_1 = w1*t1 + w3*t3 - 2*w2*t2
            # Let's compute atan2
            phases[i] = np.atan2(Q_vals[i], I_vals[i])
            
        return phases, I_vals, Q_vals

    def process_phase_equivalent(self, Y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Processes complex received phasors directly:
        1. D_i = Y_{i+1} * Y_i^*
        2. DD_i = D_{i+1} * D_i^*
        3. theta_i = angle(DD_i)
        """
        num_tones = len(self.plan.frequencies)
        
        # 1. First differential
        D = np.zeros(num_tones - 1, dtype=np.complex128)
        for i in range(num_tones - 1):
            D[i] = Y[i+1] * np.conj(Y[i])
            
        # 2. Dual differential
        DD = np.zeros(num_tones - 2, dtype=np.complex128)
        for i in range(num_tones - 2):
            # DD_i = D_{i+1} * D_i^*
            DD[i] = D[i+1] * np.conj(D[i])
            
        # 3. Extract I, Q and phases
        I_vals = np.real(DD)
        Q_vals = np.imag(DD)
        
        # theta_i = atan2(Q_i, I_i)
        phases = np.zeros(num_tones - 2)
        for i in range(num_tones - 2):
            phases[i] = np.atan2(Q_vals[i], I_vals[i])
            
        return phases, I_vals, Q_vals


class PhaseUnwrapper:
    """Handles 2pi phase wrapping and ambiguity resolution."""
    
    def __init__(self, method: str = "physical_constraints"):
        self.method = method

    def unwrap(
        self,
        wrapped_phases: np.ndarray,
        prev_phases: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Unwraps phase measurements modulo 2pi.
        If prev_phases is available, uses temporal tracking to prevent phase jumps.
        """
        unwrapped = np.copy(wrapped_phases)
        
        if prev_phases is not None and len(prev_phases) == len(wrapped_phases):
            for i in range(len(wrapped_phases)):
                diff = wrapped_phases[i] - prev_phases[i]
                # Map diff to [-pi, pi]
                diff_mapped = (diff + np.pi) % (2.0 * np.pi) - np.pi
                unwrapped[i] = prev_phases[i] + diff_mapped
        else:
            # Default unwrap (keeps principal phase or uses standard np.unwrap)
            unwrapped = np.unwrap(wrapped_phases)
            
        return unwrapped
