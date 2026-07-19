# constellation.py
from typing import Dict, Any, List
import numpy as np
from VLCL_AI.communication.qam import QAMModem

def get_constellation_data(M: int) -> List[Dict[str, float]]:
    """
    Returns the normalized constellation coordinates as a list of dictionaries.
    Useful for frontend plotting.
    """
    modem = QAMModem()
    constellation = modem.get_constellation(M)
    
    data = []
    # Find bit representation for each index
    k = modem.bits_per_symbol(M)
    if M == 2:
        for idx, sym in enumerate(constellation):
            data.append({
                "i": float(sym.real),
                "q": float(sym.imag),
                "bits": format(idx, '01b')
            })
    else:
        k_half = k // 2
        L = 2 ** k_half
        for idx, sym in enumerate(constellation):
            val_i = idx // L
            val_q = idx % L
            bin_i = format(val_i, f'0{k_half}b')
            bin_q = format(val_q, f'0{k_half}b')
            data.append({
                "i": float(sym.real),
                "q": float(sym.imag),
                "bits": bin_i + bin_q
            })
    return data
