# evm.py
import numpy as np
from typing import Dict, Any, Union

def compute_evm(
    tx_symbols: np.ndarray,
    rx_symbols: np.ndarray
) -> Dict[str, float]:
    """
    Computes Error Vector Magnitude (EVM) between transmitted (reference) and received symbols.
    
    EVM_RMS = sqrt( sum(|S_rx - S_ref|^2) / sum(|S_ref|^2) )
    
    Returns:
        metrics (dict): Contains 'linear', 'percent', and 'db' EVM values.
    """
    tx = np.asarray(tx_symbols, dtype=complex)
    rx = np.asarray(rx_symbols, dtype=complex)
    
    if len(tx) != len(rx):
        min_len = min(len(tx), len(rx))
        tx = tx[:min_len]
        rx = rx[:min_len]
        
    if len(tx) == 0:
        return {"linear": 0.0, "percent": 0.0, "db": -100.0}
        
    # Error vector
    err_vector = rx - tx
    sum_sq_err = np.sum(np.abs(err_vector) ** 2)
    sum_sq_ref = np.sum(np.abs(tx) ** 2)
    
    if sum_sq_ref == 0:
        sum_sq_ref = 1e-12
        
    evm_linear = np.sqrt(sum_sq_err / sum_sq_ref)
    evm_pct = evm_linear * 100.0
    
    # EVM in dB: 20 * log10(EVM_linear)
    if evm_linear > 0:
        evm_db = 20.0 * np.log10(evm_linear)
    else:
        evm_db = -100.0
        
    return {
        "linear": float(evm_linear),
        "percent": float(evm_pct),
        "db": float(evm_db)
    }
