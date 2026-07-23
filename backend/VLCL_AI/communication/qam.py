# qam.py
import numpy as np
from typing import Union, List, Dict
from VLCL_AI.communication.exceptions import ModulationError

class QAMModem:
    """
    Vectorized QAM Modulator and Demodulator supporting BPSK, 4-QAM, 16-QAM, 64-QAM, and 256-QAM.
    Uses Gray-coding and ensures unit average symbol energy (E[|X|^2] = 1).
    """
    
    def __init__(self):
        # Precompute constellations and Gray mapping for supported M-QAM
        self.supported_M = {2, 4, 16, 64, 256}
        self._constellations = {}
        self._bit_mappings = {}  # int -> bit string or array
        self._symbol_mappings = {} # bit string -> complex symbol
        
        for M in self.supported_M:
            self._generate_constellation(M)

    def bits_per_symbol(self, M: int) -> int:
        """Returns log2(M) bits per symbol."""
        if M == 0:
            return 0
        if M not in self.supported_M:
            raise ModulationError(f"M={M} is not supported. Supported: {self.supported_M}")
        return int(np.log2(M))

    def _generate_constellation(self, M: int):
        """Generates Gray-coded and normalized constellation for M-QAM/BPSK."""
        k = self.bits_per_symbol(M)
        
        if M == 2:  # BPSK special case
            # 0 -> -1, 1 -> 1
            symbols = np.array([-1.0 + 0j, 1.0 + 0j], dtype=complex)
            self._constellations[2] = symbols
            self._symbol_mappings[2] = {"0": symbols[0], "1": symbols[1]}
            return
            
        # For square QAM: M = 4, 16, 64, 256
        k_half = k // 2
        L = 2 ** k_half  # Number of levels per axis
        
        # Standard Gray code for L levels
        # E.g. for L=4: [0, 1, 3, 2] which corresponds to levels [-3, -1, 1, 3]
        gray_codes = []
        for i in range(L):
            gray_codes.append(i ^ (i >> 1))
            
        # Sort or map them so they correspond to linear levels from -L+1 to L-1 with step 2
        # We want the mapping to preserve the Gray property along the linear levels
        levels = np.arange(-L + 1, L, 2, dtype=float)
        
        # Map gray integer code to level
        # E.g. gray_codes list: indices 0 to L-1 map to levels
        # We want a bit representation of length k_half
        bit_to_level = {}
        for idx, g_val in enumerate(gray_codes):
            # Format to binary string of length k_half
            bin_str = format(g_val, f'0{k_half}b')
            bit_to_level[bin_str] = levels[idx]
            
        # Combine I and Q to form 2D QAM
        symbols_list = []
        sym_map = {}
        for b_i, val_i in bit_to_level.items():
            for b_q, val_q in bit_to_level.items():
                bit_str = b_i + b_q
                sym = complex(val_i, val_q)
                symbols_list.append(sym)
                sym_map[bit_str] = sym
                
        symbols = np.array(symbols_list, dtype=complex)
        
        # Normalize to unit average energy: E[|X|^2] = 1
        avg_energy = np.mean(np.abs(symbols) ** 2)
        norm_factor = 1.0 / np.sqrt(avg_energy)
        
        normalized_symbols = symbols * norm_factor
        normalized_sym_map = {b: s * norm_factor for b, s in sym_map.items()}
        
        self._constellations[M] = normalized_symbols
        self._symbol_mappings[M] = normalized_sym_map

    def get_constellation(self, M: int) -> np.ndarray:
        """Returns the normalized constellation points array."""
        if M not in self.supported_M:
            raise ModulationError(f"M={M} is not supported. Supported: {self.supported_M}")
        return self._constellations[M]

    def modulate(self, bits: np.ndarray, M: int) -> np.ndarray:
        """
        Modulates input bits (0 or 1) into complex QAM symbols.
        Uses fast vectorized lookup.
        """
        if M not in self.supported_M:
            raise ModulationError(f"M={M} is not supported. Supported: {self.supported_M}")
            
        bits = np.asarray(bits, dtype=np.uint8)
        k = self.bits_per_symbol(M)
        
        if len(bits) % k != 0:
            # Pad bits with zeros if length is not a multiple of bits_per_symbol
            pad_len = k - (len(bits) % k)
            bits = np.concatenate([bits, np.zeros(pad_len, dtype=np.uint8)])
            
        num_symbols = len(bits) // k
        
        # Reshape to group bits per symbol
        bit_groups = bits.reshape(num_symbols, k)
        
        # Convert each bit group to a string key for our precomputed map
        # Vectorized optimization using powers of 2 for fast index computation
        if M == 2:
            indices = bit_groups[:, 0]
            return self._constellations[2][indices]
            
        # For square QAM
        k_half = k // 2
        # I component bits are first k_half, Q component bits are next k_half
        pow_2 = 2 ** np.arange(k_half - 1, -1, -1)
        
        # Calculate decimal value of I and Q bits
        val_i = np.dot(bit_groups[:, :k_half], pow_2)
        val_q = np.dot(bit_groups[:, k_half:], pow_2)
        
        # Reconstruct the Gray code mapping indices
        # Since we precomputed the constellation array by nesting b_i then b_q,
        # the index in self._constellations[M] is: val_i * L + val_q
        L = 2 ** k_half
        sym_indices = val_i * L + val_q
        
        return self._constellations[M][sym_indices]

    def demodulate(self, symbols: np.ndarray, M: int) -> np.ndarray:
        """
        Demodulates complex symbols to bit array (Maximum Likelihood detection).
        Vectorized nearest-neighbor decision.
        """
        if M not in self.supported_M:
            raise ModulationError(f"M={M} is not supported. Supported: {self.supported_M}")
            
        symbols = np.asarray(symbols, dtype=complex)
        k = self.bits_per_symbol(M)
        constellation = self._constellations[M]
        
        # Vectorized minimum Euclidean distance search
        # Expand dimensions to broadcast: (len(symbols), 1) - (1, len(constellation))
        diff = symbols[:, np.newaxis] - constellation[np.newaxis, :]
        distances = np.abs(diff) ** 2
        closest_indices = np.argmin(distances, axis=1)
        
        # Convert closest indices back to bits
        # We can reconstruct the bit string from the index
        if M == 2:
            return closest_indices.astype(np.uint8)
            
        k_half = k // 2
        L = 2 ** k_half
        
        # Decouple the index into val_i and val_q
        val_i = closest_indices // L
        val_q = closest_indices % L
        
        # Convert decimal values back to binary bit groups
        bits_i = ((val_i[:, np.newaxis] & (1 << np.arange(k_half - 1, -1, -1))) > 0).astype(np.uint8)
        bits_q = ((val_q[:, np.newaxis] & (1 << np.arange(k_half - 1, -1, -1))) > 0).astype(np.uint8)
        
        # Concatenate I and Q bits for each symbol, then flatten
        return np.hstack((bits_i, bits_q)).flatten()
