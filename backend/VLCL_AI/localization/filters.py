# filters.py
import numpy as np
import scipy.signal as signal
from typing import List, Optional, Union
from VLCL_AI.localization.exceptions import SignalError

class LocalizationBandpassFilter:
    """Band-pass filter to isolate the delta f difference frequency component."""
    
    def __init__(
        self,
        center_freq_hz: float,
        bandwidth_hz: float,
        sample_rate_hz: float,
        filter_type: str = "butterworth",
        order: int = 4,
        offline_zero_phase: bool = True
    ):
        self.center_freq = float(center_freq_hz)
        self.bandwidth = float(bandwidth_hz)
        self.fs = float(sample_rate_hz)
        self.filter_type = filter_type.lower()
        self.order = int(order)
        self.offline_zero_phase = offline_zero_phase
        
        self.f_low = self.center_freq - self.bandwidth / 2.0
        self.f_high = self.center_freq + self.bandwidth / 2.0
        
        if self.f_low <= 0:
            raise SignalError(f"Bandpass filter lower cutoff must be positive, got {self.f_low} Hz.")
            
        if self.f_high >= self.fs / 2.0:
            raise SignalError(f"Bandpass filter upper cutoff {self.f_high} exceeds Nyquist frequency {self.fs/2.0} Hz.")
            
        self._init_filter()

    def _init_filter(self):
        if self.filter_type == "butterworth":
            # Design butterworth filter
            nyq = 0.5 * self.fs
            self.sos = signal.butter(
                self.order, 
                [self.f_low / nyq, self.f_high / nyq], 
                btype='bandpass', 
                output='sos'
            )
        elif self.filter_type == "fir":
            nyq = 0.5 * self.fs
            # Choose odd number of taps
            numtaps = self.order * 2 + 1
            self.taps = signal.firwin(
                numtaps, 
                [self.f_low / nyq, self.f_high / nyq], 
                pass_zero=False
            )
        elif self.filter_type == "fft_ideal":
            pass
        else:
            raise SignalError(f"Unsupported bandpass filter type: {self.filter_type}")

    def filter(self, x: np.ndarray) -> np.ndarray:
        """Filters the input signal array."""
        if self.filter_type == "fft_ideal":
            return self._filter_fft_ideal(x)
            
        if self.filter_type == "butterworth":
            if self.offline_zero_phase:
                return signal.sosfiltfilt(self.sos, x)
            else:
                return signal.sosfilt(self.sos, x)
                
        elif self.filter_type == "fir":
            if self.offline_zero_phase:
                # Use filtfilt equivalent for FIR
                return signal.filtfilt(self.taps, [1.0], x)
            else:
                return signal.lfilter(self.taps, [1.0], x)
                
        return x

    def _filter_fft_ideal(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        freqs = np.fft.fftfreq(n, d=1.0/self.fs)
        X = np.fft.fft(x)
        
        # Zero out components outside passband (both positive and negative frequencies)
        mask = (np.abs(freqs) >= self.f_low) & (np.abs(freqs) <= self.f_high)
        X[~mask] = 0.0
        
        return np.fft.ifft(X).real


class LocalizationLowpassFilter:
    """Low-pass filter to isolate the slowly varying or DC phase components."""
    
    def __init__(
        self,
        cutoff_hz: float,
        sample_rate_hz: float,
        filter_type: str = "butterworth",
        order: int = 4,
        offline_zero_phase: bool = True
    ):
        self.cutoff = float(cutoff_hz)
        self.fs = float(sample_rate_hz)
        self.filter_type = filter_type.lower()
        self.order = int(order)
        self.offline_zero_phase = offline_zero_phase
        
        if self.cutoff >= self.fs / 2.0:
            raise SignalError(f"Lowpass filter cutoff {self.cutoff} exceeds Nyquist frequency {self.fs/2.0} Hz.")
            
        self._init_filter()

    def _init_filter(self):
        if self.filter_type == "butterworth":
            nyq = 0.5 * self.fs
            self.sos = signal.butter(
                self.order, 
                self.cutoff / nyq, 
                btype='low', 
                output='sos'
            )
        elif self.filter_type == "fir":
            nyq = 0.5 * self.fs
            numtaps = self.order * 2 + 1
            self.taps = signal.firwin(
                numtaps, 
                self.cutoff / nyq, 
                pass_zero=True
            )
        elif self.filter_type == "fft_ideal":
            pass
        else:
            raise SignalError(f"Unsupported lowpass filter type: {self.filter_type}")

    def filter(self, x: np.ndarray) -> np.ndarray:
        """Filters the input signal array."""
        if self.filter_type == "fft_ideal":
            return self._filter_fft_ideal(x)
            
        if self.filter_type == "butterworth":
            if self.offline_zero_phase:
                return signal.sosfiltfilt(self.sos, x)
            else:
                return signal.sosfilt(self.sos, x)
                
        elif self.filter_type == "fir":
            if self.offline_zero_phase:
                return signal.filtfilt(self.taps, [1.0], x)
            else:
                return signal.lfilter(self.taps, [1.0], x)
                
        return x

    def _filter_fft_ideal(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        freqs = np.fft.fftfreq(n, d=1.0/self.fs)
        X = np.fft.fft(x)
        
        # Zero out components above cutoff
        mask = np.abs(freqs) <= self.cutoff
        X[~mask] = 0.0
        
        return np.fft.ifft(X).real


def trim_transients(signal_array: np.ndarray, fs: float, duration: float) -> np.ndarray:
    """
    Trims filter startup transients.
    For offline simulations of size N, we trim the first and last 10% of samples.
    """
    n = len(signal_array)
    trim_samples = int(0.10 * n)
    if trim_samples * 2 >= n:
        return signal_array
    return signal_array[trim_samples : n - trim_samples]
