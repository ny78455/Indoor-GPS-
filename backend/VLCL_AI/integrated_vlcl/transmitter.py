# transmitter.py
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from VLCL_AI.communication.bit_generator import BitGenerator
from VLCL_AI.communication.qam import QAMModem
from VLCL_AI.communication.ofdm import OFDMModulator
from VLCL_AI.communication.dco_ofdm import DCOOFDM
from VLCL_AI.communication.exceptions import OFDMError
from VLCL_AI.integrated_vlcl.spectrum_partitioner import SpectrumPartitioner
from VLCL_AI.integrated_vlcl.power_mapper import MultiLedPowerMapper

class IntegratedVLCLTransmitter:
    """
    Unified Transmitter for Integrated Visible Light Communication and Localization (VLCL).
    Generates composite signals x_i(t) = x_comm_i(t) + x_loc_i(t) for each LED i,
    adding DC bias and clipping to satisfy physical LED dynamic range constraints.
    """
    
    def __init__(
        self,
        partitioner: SpectrumPartitioner,
        power_mapper: MultiLedPowerMapper,
        modem: QAMModem,
        modulator: OFDMModulator,
        dco_engine: DCOOFDM,
        bit_generator: BitGenerator
    ):
        self.partitioner = partitioner
        self.power_mapper = power_mapper
        self.modem = modem
        self.modulator = modulator
        self.dco_engine = dco_engine
        self.bit_generator = bit_generator
        
        self.fft_size = self.partitioner.grid.fft_size
        self.cp_length = self.modulator.cp_length

    def modulate_communication_led(
        self,
        led_id: int,
        bits: np.ndarray,
        modulation_order: int = 16
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Modulates communication bits specifically on the subcarriers assigned to LED i's SG.
        Places zeros on all other subcarriers, and ensures Hermitian symmetry.
        """
        g_id = led_id  # By default group g corresponds to LED g
        sc_indices = self.partitioner.comm_groups.get(g_id, [])
        
        if len(sc_indices) == 0:
            # No subcarriers allocated to this LED. Return zero waveform.
            num_samples = self.fft_size + self.cp_length
            return np.zeros(num_samples), np.zeros((1, self.fft_size), dtype=complex), bits
            
        k = self.modem.bits_per_symbol(modulation_order)
        
        # Determine independent positive subcarriers assigned to this LED's group
        half_n = self.fft_size // 2
        independent_pos = sorted([idx for idx in sc_indices if 0 < idx < half_n])
        num_pos = len(independent_pos)
        
        if len(bits) == 0:
            # Generate dummy bits
            bits = self.bit_generator.generate(10 * k * num_pos)
            
        qam_symbols = self.modem.modulate(bits, modulation_order)
        
        # Group into OFDM frames
        num_frames = int(np.ceil(len(qam_symbols) / num_pos))
        padded_len = num_frames * num_pos
        padded_symbols = np.zeros(padded_len, dtype=complex)
        padded_symbols[:len(qam_symbols)] = qam_symbols
        
        frames_qam = padded_symbols.reshape(num_frames, num_pos)
        
        # Build frequency grid
        freq_grid = np.zeros((num_frames, self.fft_size), dtype=complex)
        
        # Place symbols on positive carriers and apply Hermitian symmetry
        for f_idx in range(num_frames):
            freq_grid[f_idx, independent_pos] = frames_qam[f_idx]
            for k_bin in range(1, half_n):
                freq_grid[f_idx, self.fft_size - k_bin] = np.conj(freq_grid[f_idx, k_bin])
                
            freq_grid[f_idx, 0] = 0.0 + 0.0j
            freq_grid[f_idx, half_n] = 0.0 + 0.0j
            
        # Compute IFFT
        time_frames = np.fft.ifft(freq_grid, axis=1)
        time_frames_real = np.real(time_frames)
        
        # Add Cyclic Prefix
        cp_frames = time_frames_real[:, -self.cp_length:]
        time_frames_with_cp = np.hstack((cp_frames, time_frames_real))
        
        # Flatten
        continuous_waveform = time_frames_with_cp.flatten()
        
        return continuous_waveform, freq_grid, bits

    def generate_localization_led(
        self,
        led_id: int,
        num_samples: int,
        initial_phase: float = 0.0
    ) -> np.ndarray:
        """
        Synthesizes the analog-like localization tones mapped to LED i in the time domain.
        """
        sample_rate = self.partitioner.grid.sample_rate
        t = np.arange(num_samples) / sample_rate
        
        x_loc = np.zeros(num_samples, dtype=float)
        
        # Find which tones are mapped to this LED
        for tone_idx, freq in enumerate(self.partitioner.plan.frequencies):
            tone_id = tone_idx + 1
            mapped_leds = self.power_mapper.tone_to_led_map.get(tone_id, [])
            
            if led_id in mapped_leds:
                # Retrieve configured power for this tone on this LED
                subcarrier_spacing = self.partitioner.grid.sample_rate / self.fft_size
                bin_idx = int(round(freq / subcarrier_spacing))
                power = self.power_mapper.power_matrix[led_id - 1, bin_idx]
                
                # Align frequency to the nearest subcarrier to maintain strict orthogonality
                freq_aligned = bin_idx * subcarrier_spacing
                
                # Superpose sinusoid with correct 2/N scaling to match the IFFT power of communication subcarriers
                omega = 2.0 * np.pi * freq_aligned
                x_loc += (2.0 * np.sqrt(power) / self.fft_size) * np.sin(omega * t + initial_phase)
                
        return x_loc

    def transmit(
        self,
        bits_dict: Dict[int, np.ndarray],
        modulation_order_dict: Optional[Dict[int, int]] = None,
        initial_phase: float = 0.0
    ) -> Tuple[Dict[int, np.ndarray], Dict[int, Dict[str, Any]], Dict[int, np.ndarray], Dict[int, np.ndarray]]:
        """
        Runs the complete integrated transmission chain for all K LEDs.
        
        Returns:
            unipolar_signals (dict): LED ID -> unipolar clipped drive signal.
            clipping_metrics (dict): LED ID -> clipping/power metrics.
            transmitted_bits (dict): LED ID -> payload bits actually transmitted.
            frequency_grids (dict): LED ID -> frequency-domain symbols.
        """
        unipolar_signals = {}
        clipping_metrics = {}
        transmitted_bits = {}
        frequency_grids = {}
        
        orders = modulation_order_dict or {led_id: 16 for led_id in range(1, self.power_mapper.num_leds + 1)}
        
        # Step 1 & 2: Process each LED separately
        for led_id in range(1, self.power_mapper.num_leds + 1):
            bits = bits_dict.get(led_id, np.array([], dtype=int))
            mod_order = orders.get(led_id, 16)
            
            # 1. Modulate communication subcarriers
            x_comm, freq_grid, actual_bits = self.modulate_communication_led(led_id, bits, mod_order)
            num_samples = len(x_comm)
            
            # 2. Synthesize localization tones
            x_loc = self.generate_localization_led(led_id, num_samples, initial_phase)
            
            # 3. Superpose components
            x_comp = x_comm + x_loc
            
            # 4. DC Bias and Clipping (DCO Engine)
            clipped_signal, metrics = self.dco_engine.process_transmitter_waveform(x_comp)
            
            # Save outputs
            unipolar_signals[led_id] = clipped_signal
            clipping_metrics[led_id] = metrics
            transmitted_bits[led_id] = actual_bits
            frequency_grids[led_id] = freq_grid
            
        return unipolar_signals, clipping_metrics, transmitted_bits, frequency_grids
