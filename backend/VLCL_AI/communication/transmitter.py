# transmitter.py
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from VLCL_AI.communication.bit_generator import BitGenerator
from VLCL_AI.communication.qam import QAMModem
from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid
from VLCL_AI.communication.ofdm import OFDMModulator
from VLCL_AI.communication.dco_ofdm import DCOOFDM
from VLCL_AI.communication.pre_equalizer import PreEqualizer
from VLCL_AI.communication.frame import CommunicationFrame
from VLCL_AI.communication.exceptions import OFDMError

class VLCTransmitter:
    """
    Manages the complete Visible Light Communication transmitter chain.
    Transforms raw information bits into physical drive signals forceiling LEDs.
    """
    
    def __init__(
        self,
        grid: SubcarrierGrid,
        modem: QAMModem,
        modulator: OFDMModulator,
        dco_engine: DCOOFDM,
        pre_equalizer: PreEqualizer,
        bit_generator: BitGenerator
    ):
        self.grid = grid
        self.modem = modem
        self.modulator = modulator
        self.dco_engine = dco_engine
        self.pre_equalizer = pre_equalizer
        self.bit_generator = bit_generator

    def transmit(
        self,
        bits: np.ndarray,
        user_id: int,
        modulation_order: int = 16,
        channel_response: Optional[np.ndarray] = None
    ) -> Tuple[CommunicationFrame, Dict[str, Any]]:
        """
        Executes the digital transmission chain for a single user/frame.
        
        Args:
            bits (np.ndarray): Information bits (if None, we generate a random stream).
            user_id (int): Destination user ID.
            modulation_order (int): QAM order to use.
            channel_response (np.ndarray): Estimated channel response H_n (used if Pre-EQ is enabled).
            
        Returns:
            frame (CommunicationFrame): Holds modulated waves and metadata.
            tx_metrics (dict): Stats on the transmitted frame.
        """
        # 1. Map bits to QAM symbols
        k = self.modem.bits_per_symbol(modulation_order)
        if bits is None or len(bits) == 0:
            # Generate random bits for testing
            bits = self.bit_generator.generate(1000 * k)
            
        qam_symbols = self.modem.modulate(bits, modulation_order)
        
        # 2. Assign subcarrier purposes in the grid
        active_sc_indices = np.array(self.grid.get_active_indices())
        pilot_indices = np.array(self.grid.get_pilot_indices())
        
        # Apply modulation order and user assignment to our active subcarriers in the grid
        for idx in active_sc_indices:
            sc = self.grid.subcarriers[idx]
            sc.modulation_order = modulation_order
            sc.assigned_user = user_id
            
        # 3. Apply transmitter pre-equalization if enabled and channel estimate is available
        if self.pre_equalizer.enabled and channel_response is not None:
            # We pre-equalize the symbols on each carrier
            # H_n response mapped to active carriers
            qam_symbols = self.pre_equalizer.pre_equalize(qam_symbols, channel_response)
            
        # 4. Modulate to OFDM real baseband waveform
        time_waveform, freq_grid = self.modulator.modulate(qam_symbols)
        
        # 5. Apply DC Biasing and Clipping (DCO-OFDM) for LED constraints
        unipolar_drive_waveform, clipping_metrics = self.dco_engine.process_transmitter_waveform(time_waveform)
        
        # Assemble communication frame
        frame = CommunicationFrame(
            frame_id=np.random.randint(1000, 9999),
            user_id=user_id,
            payload_bits=bits,
            modulation_order=modulation_order,
            subcarrier_indices=active_sc_indices,
            pilot_indices=pilot_indices,
            qam_symbols=qam_symbols,
            frequency_symbols=freq_grid,
            time_waveform=unipolar_drive_waveform,
            sample_rate=self.grid.sample_rate,
            cyclic_prefix_length=self.modulator.cp_length,
            metadata=clipping_metrics
        )
        
        return frame, clipping_metrics
