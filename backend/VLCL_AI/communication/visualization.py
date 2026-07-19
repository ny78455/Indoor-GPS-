# visualization.py
import numpy as np
from typing import Dict, Any, List, Optional
from VLCL_AI.communication.state import CommunicationState
from VLCL_AI.communication.constellation import get_constellation_data

def get_visualization_payload(state: CommunicationState) -> Dict[str, Any]:
    """
    Constructs high-fidelity lightweight visualization datasets.
    Downsamples huge continuous waveforms to prevent overloading network pipes.
    """
    if not state:
        return {}
        
    # Downsample time-domain waveforms to at most 1000 points for Web visualization
    tx_wave = state.ofdm_tx_waveform
    rx_wave = state.ofdm_rx_waveform
    
    step_tx = max(1, len(tx_wave) // 1000)
    step_rx = max(1, len(rx_wave) // 1000)
    
    tx_wave_ds = tx_wave[::step_tx]
    rx_wave_ds = rx_wave[::step_rx]
    
    # Structure equalized constellation coordinates
    rx_constellation = []
    tx_constellation = []
    
    for rx_sym, tx_sym in zip(state.qam_rx_symbols, state.qam_tx_symbols):
        rx_constellation.append({
            "i": float(rx_sym.real),
            "q": float(rx_sym.imag)
        })
        tx_constellation.append({
            "i": float(tx_sym.real),
            "q": float(tx_sym.imag)
        })
        
    # Spectrum allocation data
    # Map subcarrier indices, center frequencies, power, and assigned purpose
    spectrum_data = []
    for k in range(len(state.subcarrier_bandwidths)):
        # Determine purpose and active status
        purpose = "UNUSED"
        active = False
        
        # We can map back from active communication, pilot, guard, DC bands
        if k in state.active_subcarriers:
            purpose = "COMMUNICATION"
            active = True
        elif k == 0:
            purpose = "DC"
        elif k == len(state.subcarrier_bandwidths) // 2:
            purpose = "GUARD"
        elif k % 16 == 0:  # Nominal pilot spacing
            purpose = "PILOT"
            active = True
        elif 5 <= k <= 9:  # Localization reserved band
            purpose = "LOCALIZATION_RESERVED"
            
        spectrum_data.append({
            "index": k,
            "center_frequency_mhz": float(k * (50.0 / len(state.subcarrier_bandwidths))), # assuming Fs=50MHz
            "power": float(state.subcarrier_powers[k]) if k < len(state.subcarrier_powers) else 0.0,
            "modulation_order": int(state.modulation_orders[k]),
            "snr_db": float(state.snr_per_subcarrier[k]) if k < len(state.snr_per_subcarrier) else 0.0,
            "ber": float(state.ber_per_subcarrier[k]) if k < len(state.ber_per_subcarrier) else 0.0,
            "purpose": purpose,
            "active": active
        })
        
    return {
        "tx_waveform_downsampled": tx_wave_ds.tolist(),
        "rx_waveform_downsampled": rx_wave_ds.tolist(),
        "tx_constellation": tx_constellation[:200],  # cap at 200 points for fast rendering
        "rx_constellation": rx_constellation[:400],  # cap at 400 points
        "spectrum": spectrum_data,
        "papr_db": float(state.papr),
        "clipping_ratio_pct": float(state.clipping_ratio),
        "sum_rate_mbps": float(state.sum_rate / 1e6),
        "effective_throughput_mbps": float(state.effective_throughput / 1e6),
        "spectral_efficiency": float(state.spectral_efficiency)
    }
