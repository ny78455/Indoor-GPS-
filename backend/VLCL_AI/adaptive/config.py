# config.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AdaptiveConfig:
    """
    Configuration dataclass for Module 6 Adaptive Modulation and Subcarrier Allocation.
    """
    ber_max: float = 3.8e-3                     # Target BER target (Paper Sec. IV)
    supported_modulations: List[int] = field(
        default_factory=lambda: [2, 4, 16, 64, 256]
    )                                          # Supported modulation orders (M)
    mode: str = "ADAPTIVE"                      # "ADAPTIVE" or "STATIC"
    default_static_modulation: int = 16        # Modulation order used in STATIC mode
    feedback_delay_s: float = 0.0              # Simulation CSI feedback delay (seconds)
    total_bandwidth_hz: float = 20.0e6          # Total communication bandwidth (Hz)
    fft_size: int = 256                         # OFDM FFT size
    cp_ratio: float = 0.25                      # Cyclic prefix ratio
    
    @property
    def subcarrier_bandwidth_hz(self) -> float:
        return self.total_bandwidth_hz / self.fft_size

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AdaptiveConfig":
        return cls(
            ber_max=float(d.get("ber_max", 3.8e-3)),
            supported_modulations=list(d.get("supported_modulations", [2, 4, 16, 64, 256])),
            mode=str(d.get("mode", "ADAPTIVE")),
            default_static_modulation=int(d.get("default_static_modulation", 16)),
            feedback_delay_s=float(d.get("feedback_delay_s", 0.0)),
            total_bandwidth_hz=float(d.get("total_bandwidth_hz", 20.0e6)),
            fft_size=int(d.get("fft_size", 256)),
            cp_ratio=float(d.get("cp_ratio", 0.25))
        )
