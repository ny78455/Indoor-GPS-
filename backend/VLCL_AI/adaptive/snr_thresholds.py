# snr_thresholds.py
import numpy as np
from scipy.optimize import brentq
from typing import Dict, List, Tuple, Any
from VLCL_AI.communication.ber import BERCalculator

class SNRThresholdTable:
    """
    Computes and caches SNR threshold tables for BER-constrained adaptive modulation.
    
    For a given BER_max and modulation order M, solves:
        BER_analytical(M, gamma_th) - BER_max = 0
    using scipy.optimize.brentq.
    
    Provenance tags:
        PAPER_DERIVED: Scientifically derived root solving BER(M, gamma_th) = BER_max.
        PAPER_EXPLICIT: Directly quoted from reference paper tables.
        CONFIGURED_ASSUMPTION: Default fallback values if numerical solver fails.
    """

    def __init__(self, ber_max: float = 3.8e-3, supported_modulations: List[int] = None):
        self.ber_max = ber_max
        self.supported_modulations = supported_modulations or [2, 4, 16, 64, 256]
        self._thresholds_linear: Dict[int, float] = {}
        self._provenance: Dict[int, str] = {}
        self._build_table()

    def _build_table(self):
        """Derives exact SNR thresholds for each supported modulation order."""
        for M in sorted(self.supported_modulations):
            try:
                # Solve BER(M, gamma) = BER_max
                # Lower bound 0.0 (or small epsilon), upper bound 1e6 (60 dB)
                def obj_func(gamma_lin):
                    return float(BERCalculator.compute_analytical_qam(gamma_lin, M)) - self.ber_max

                # Check if upper bound gives BER < BER_max
                if obj_func(1e6) > 0:
                    # Very strict BER_max, unachievable even at 60 dB
                    gamma_th = 1e6
                else:
                    gamma_th = brentq(obj_func, 1e-6, 1e6, xtol=1e-8, maxiter=100)

                self._thresholds_linear[M] = float(gamma_th)
                self._provenance[M] = "PAPER_DERIVED"
            except Exception:
                # Fallback heuristics if root solver fails
                # BPSK ~ 3 dB, 4-QAM ~ 6.5 dB, 16-QAM ~ 13.5 dB, 64-QAM ~ 19.5 dB, 256-QAM ~ 25.5 dB
                fallback_db = {2: 3.0, 4: 6.8, 16: 13.8, 64: 19.8, 256: 25.8}.get(M, 30.0)
                self._thresholds_linear[M] = float(10.0 ** (fallback_db / 10.0))
                self._provenance[M] = "CONFIGURED_ASSUMPTION"

    def get_threshold_linear(self, M: int) -> float:
        """Returns linear SNR threshold for modulation order M."""
        if M not in self._thresholds_linear:
            raise ValueError(f"Modulation order M={M} not present in threshold table.")
        return self._thresholds_linear[M]

    def get_threshold_db(self, M: int) -> float:
        """Returns SNR threshold in dB for modulation order M."""
        return 10.0 * np.log10(self.get_threshold_linear(M))

    def get_all_thresholds_linear(self) -> Dict[int, float]:
        return dict(self._thresholds_linear)

    def get_provenance(self, M: int) -> str:
        return self._provenance.get(M, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation for telemetry/reporting."""
        return {
            "ber_max": self.ber_max,
            "thresholds_db": {M: self.get_threshold_db(M) for M in sorted(self._thresholds_linear.keys())},
            "thresholds_linear": {M: self._thresholds_linear[M] for M in sorted(self._thresholds_linear.keys())},
            "provenance": dict(self._provenance)
        }
