# state.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class IntegratedVLCLState:
    """
    Immutable representation of the physical-layer state for integrated VLCL simulation.
    Combines simultaneous multi-user communications and A-DPDOA localization.
    """
    simulation_time: float
    
    # LED-specific communication and transmitter metrics
    # LED ID -> results (decoded_bits, empirical_ber, bit_errors, etc.)
    communication_results: Dict[int, Dict[str, Any]]
    
    # Localization processing branch results
    # (estimated_position, solver_meta, raw_phases, unwrapped_phases, error_3d_m)
    localization_results: Dict[str, Any]
    
    # Transmitter status per LED
    papr_per_led: Dict[int, float]
    clipping_ratio_per_led: Dict[int, float]
    dc_bias_per_led: Dict[int, float]
    
    # Metadata and status
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the integrated state into a serializable dictionary."""
        # Convert NumPy arrays to lists for JSON compatibility
        comm_summary = {}
        for led_id, res in self.communication_results.items():
            comm_summary[led_id] = {
                "num_transmitted_bits": int(res.get("num_transmitted_bits", 0)),
                "bit_errors": int(res.get("bit_errors", 0)),
                "empirical_ber": float(res.get("empirical_ber", 0.0)),
                "num_recovered_symbols": len(res.get("equalized_symbols", []))
            }
            
        loc_summary = {
            "estimated_position": self.localization_results.get("estimated_position"),
            "error_3d_m": float(self.localization_results.get("error_3d_m", 0.0)),
            "success": bool(self.localization_results.get("success", False))
        }
        
        return {
            "simulation_time": self.simulation_time,
            "communications": comm_summary,
            "localization": loc_summary,
            "transmitter": {
                "papr_db": {str(k): float(v) for k, v in self.papr_per_led.items()},
                "clipping_ratio_pct": {str(k): float(v) for k, v in self.clipping_ratio_per_led.items()},
                "dc_bias_volts": {str(k): float(v) for k, v in self.dc_bias_per_led.items()}
            },
            "metadata": self.metadata
        }
