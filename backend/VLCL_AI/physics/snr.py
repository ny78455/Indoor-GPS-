# snr.py
import numpy as np
from typing import Dict, Union

def compute_snr(
    signal_current: Union[float, np.ndarray],
    noise_variance: Union[float, np.ndarray]
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Computes electrical and optical SNR.
    Electrical SNR = (I_photo)^2 / sigma_noise^2
    Optical SNR = I_photo / sigma_noise
    """
    # Guard against zero noise
    noise_var = np.where(noise_variance > 0, noise_variance, 1e-24)
    noise_std = np.sqrt(noise_var)
    
    # Calculate electrical SNR (linear & dB)
    elec_snr_linear = (signal_current ** 2) / noise_var
    elec_snr_db = 10.0 * np.log10(np.where(elec_snr_linear > 0, elec_snr_linear, 1e-12))
    
    # Calculate optical SNR (linear & dB)
    opt_snr_linear = signal_current / noise_std
    opt_snr_db = 10.0 * np.log10(np.where(opt_snr_linear > 0, opt_snr_linear, 1e-12))
    
    if isinstance(signal_current, np.ndarray):
        return {
            "electrical_snr_linear": elec_snr_linear,
            "electrical_snr_db": elec_snr_db,
            "optical_snr_linear": opt_snr_linear,
            "optical_snr_db": opt_snr_db
        }
    else:
        return {
            "electrical_snr_linear": float(elec_snr_linear),
            "electrical_snr_db": float(elec_snr_db),
            "optical_snr_linear": float(opt_snr_linear),
            "optical_snr_db": float(opt_snr_db)
        }
