# ber.py
import numpy as np
from scipy.special import erfc
from typing import Union, Tuple, Dict
from VLCL_AI.communication.exceptions import VLCLCommunicationError

class BERCalculator:
    """
    Computes and validates Bit Error Rate (BER) metrics.
    Provides two distinct operational modes:
    1. Empirical Mode (Monte Carlo bit-by-bit comparison).
    2. Analytical Mode (Theoretical formula for M-QAM).
    """

    @staticmethod
    def compute_empirical(tx_bits: np.ndarray, rx_bits: np.ndarray,
                          strict: bool = False) -> Tuple[float, int]:
        """
        Computes empirical BER by directly comparing transmitted and recovered bits.

        Args:
            tx_bits: Transmitted bit sequence.
            rx_bits: Received/decoded bit sequence.
            strict: If True, raise VLCLCommunicationError on length mismatch.
                    If False (default), silently trim to common length.
                    Use strict=True in research/validation pipelines to detect
                    framing or alignment errors early. (M3-COM-004)

        Returns:
            ber (float): Bit error rate.
            bit_errors (int): Number of bit errors.
        """
        tx = np.asarray(tx_bits, dtype=np.uint8)
        rx = np.asarray(rx_bits, dtype=np.uint8)

        if len(tx) != len(rx):
            if strict:
                raise VLCLCommunicationError(
                    f"M3-COM-004: BER length mismatch: tx={len(tx)} bits, rx={len(rx)} bits. "
                    f"Use strict=False to allow silent truncation (not recommended for validation)."
                )
            # Non-strict: trim to common length
            min_len = min(len(tx), len(rx))
            tx = tx[:min_len]
            rx = rx[:min_len]

        if len(tx) == 0:
            return 0.0, 0

        bit_errors = int(np.sum(tx != rx))
        ber = float(bit_errors / len(tx))

        return ber, bit_errors

    @staticmethod
    def compute_analytical_qam(snr_linear: Union[float, np.ndarray], M: int) -> Union[float, np.ndarray]:
        """
        Computes theoretical BER of M-QAM over AWGN.
        Uses numerically stable erfc-based approximation.
        
        Pb ≈ (4 / log2(M)) * (1 - 1/sqrt(M)) * 0.5 * erfc( sqrt( (3 * SNR) / (2 * (M - 1)) ) )
        """
        if M not in {2, 4, 16, 64, 256}:
            raise VLCLCommunicationError(f"Unsupported modulation order M={M} for analytical BER calculation.")
            
        snr_linear = np.asarray(snr_linear, dtype=float)
        # Avoid negative SNR values
        snr_linear = np.maximum(snr_linear, 0.0)
        
        k = np.log2(M)
        
        if M == 2:  # BPSK special case
            # Pb = 0.5 * erfc(sqrt(SNR))
            return 0.5 * erfc(np.sqrt(snr_linear))
            
        # Square QAM: 4-QAM, 16-QAM, 64-QAM, 256-QAM
        # Pre-factor
        coef = (4.0 / k) * (1.0 - 1.0 / np.sqrt(M))
        
        # Argument of Q-function (which is erfc(x/sqrt(2))/2)
        # Q(x) = 0.5 * erfc(x / sqrt(2))
        # inside Q is sqrt(3 * SNR_linear * log2(M) / (M - 1)) if SNR is Eb/N0.
        # If SNR is Es/N0 (electrical SNR of symbol), then:
        # Q( sqrt( 3 * SNR_sym / (M - 1) ) )
        # To map Q(x) to erfc(y): y = x / sqrt(2). So erfc( sqrt( 3 * SNR_sym / (2 * (M - 1)) ) )
        arg = np.sqrt(3.0 * snr_linear / (2.0 * (M - 1.0)))
        
        return 0.5 * coef * erfc(arg)
