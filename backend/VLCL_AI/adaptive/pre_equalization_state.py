# pre_equalization_state.py
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class PreEqualizationState:
    """
    Data structure capturing pre-equalization filter status, power scaling, and distortion metrics.
    """
    mode: str = "REGULARIZED"  # NONE, ZERO_FORCING, REGULARIZED, PAPER_WEIGHTED
    max_gain_db: float = 10.0  # Max gain cap in dB
    max_gain_linear: float = 3.1622776601683795  # 10^(10/20)
    regularization_lambda: float = 1e-4
    
    # Pre-equalization coefficient matrix (shape: num_leds, fft_size)
    coefficients_matrix: np.ndarray = field(default_factory=lambda: np.ones((4, 256), dtype=complex))
    
    # Waveform quality and physical stress metrics
    papr_before_db: Dict[int, float] = field(default_factory=dict)
    papr_after_db: Dict[int, float] = field(default_factory=dict)
    clipping_ratio: Dict[int, float] = field(default_factory=dict)
    gain_saturated_subcarriers: Dict[int, List[int]] = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.mode.upper() != "NONE"
