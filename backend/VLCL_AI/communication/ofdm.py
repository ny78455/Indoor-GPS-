# ofdm.py
import numpy as np
from typing import Tuple, List, Dict
from VLCL_AI.communication.exceptions import OFDMError
from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid

class OFDMModulator:
    """
    OFDM Modulator (Transmitter DSP) for IM/DD systems.
    Maps QAM symbols to active subcarriers, applies Hermitian symmetry,
    performs IFFT, and inserts Cyclic Prefix to produce a real-valued baseband signal.
    """
    
    def __init__(self, grid: SubcarrierGrid, cyclic_prefix_ratio: float = 0.125):
        self.grid = grid
        self.N = grid.fft_size
        self.cp_length = int(np.round(self.N * cyclic_prefix_ratio))
        if self.cp_length <= 0:
            raise OFDMError(f"Cyclic prefix ratio {cyclic_prefix_ratio} leads to 0 or negative CP length.")

    def modulate(self, qam_symbols: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Modulates a stream of complex QAM symbols into a real-valued time-domain waveform.
        Ensures strict Hermitian symmetry for IM/DD compatibility.
        
        Returns:
            time_waveform (np.ndarray): Real-valued time-domain signal.
            frequency_symbols (np.ndarray): The full symmetric frequency grid (for analysis).
        """
        active_indices = self.grid.get_active_indices()
        pilot_indices = self.grid.get_pilot_indices()
        
        # We place our communication symbols and pilots on the positive frequencies
        # Positive indices are in [1, N/2 - 1]
        half_n = self.N // 2
        allowed_pos_indices = [idx for idx in active_indices if 0 < idx < half_n]
        allowed_pilot_indices = [idx for idx in pilot_indices if 0 < idx < half_n]
        
        # Combine them as writable indices
        writable_indices = sorted(allowed_pos_indices + allowed_pilot_indices)
        num_writable = len(writable_indices)
        
        if len(qam_symbols) == 0:
            raise OFDMError("Cannot modulate empty QAM symbol array.")
            
        # Group QAM symbols into OFDM frames
        num_frames = int(np.ceil(len(qam_symbols) / num_writable))
        
        # Pad QAM symbols with zeros if needed
        total_required = num_frames * num_writable
        padded_symbols = np.zeros(total_required, dtype=complex)
        padded_symbols[:len(qam_symbols)] = qam_symbols
        
        frames_qam = padded_symbols.reshape(num_frames, num_writable)
        
        # Full frequency-domain grids (including Hermitian symmetry)
        freq_grid = np.zeros((num_frames, self.N), dtype=complex)
        
        # Map onto the grid
        for f_idx in range(num_frames):
            # Place symbols on positive frequency subcarriers
            freq_grid[f_idx, writable_indices] = frames_qam[f_idx]
            
            # Apply Hermitian symmetry for IM/DD real-valued output
            # X[N - k] = conj(X[k])
            for k in range(1, half_n):
                freq_grid[f_idx, self.N - k] = np.conj(freq_grid[f_idx, k])
                
            # Double-check: DC and Nyquist are 0
            freq_grid[f_idx, 0] = 0.0 + 0.0j
            freq_grid[f_idx, half_n] = 0.0 + 0.0j
            
        # Compute IFFT along axis=1
        time_frames = np.fft.ifft(freq_grid, axis=1)
        
        # Check that imaginary part is negligible
        max_imag = np.max(np.abs(np.imag(time_frames)))
        if max_imag > 1e-11:
            raise OFDMError(f"Hermitian symmetry violation: max imaginary component of IFFT is {max_imag}")
            
        # Keep only the real part (any residual is numerical noise)
        time_frames_real = np.real(time_frames)
        
        # Insert Cyclic Prefix
        # Copy the last cp_length samples of each frame to the front
        cp_frames = time_frames_real[:, -self.cp_length:]
        time_frames_with_cp = np.hstack((cp_frames, time_frames_real))
        
        # Flatten into a continuous stream
        continuous_waveform = time_frames_with_cp.flatten()
        
        return continuous_waveform, freq_grid


class OFDMDemodulator:
    """
    OFDM Demodulator (Receiver DSP).
    Extracts frames, removes CP, performs FFT, extracts active subcarriers,
    and returns complex symbols for equalization.
    """
    
    def __init__(self, grid: SubcarrierGrid, cyclic_prefix_ratio: float = 0.125):
        self.grid = grid
        self.N = grid.fft_size
        self.cp_length = int(np.round(self.N * cyclic_prefix_ratio))

    def demodulate(self, time_waveform: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Demodulates the time-domain waveform into complex frequency symbols.
        
        Returns:
            rx_qam_symbols (np.ndarray): Extracted communication symbols.
            freq_grid (np.ndarray): The demodulated full frequency grid.
        """
        frame_len = self.N + self.cp_length
        num_frames = len(time_waveform) // frame_len
        
        if num_frames == 0:
            raise OFDMError("Waveform too short to contain a single OFDM frame.")
            
        # Discard trailing samples that don't fit into a frame
        trimmed_waveform = time_waveform[:num_frames * frame_len]
        frames = trimmed_waveform.reshape(num_frames, frame_len)
        
        # Remove Cyclic Prefix
        frames_no_cp = frames[:, self.cp_length:]
        
        # Perform FFT. Note: Scaling is matched to np.fft.ifft()
        freq_grid = np.fft.fft(frames_no_cp, axis=1)
        
        # Extract active and pilot symbols
        active_indices = self.grid.get_active_indices()
        pilot_indices = self.grid.get_pilot_indices()
        half_n = self.N // 2
        
        allowed_pos_indices = [idx for idx in active_indices if 0 < idx < half_n]
        allowed_pilot_indices = [idx for idx in pilot_indices if 0 < idx < half_n]
        readable_indices = sorted(allowed_pos_indices + allowed_pilot_indices)
        
        # Extract symbols
        rx_symbols = freq_grid[:, readable_indices].flatten()
        
        return rx_symbols, freq_grid
