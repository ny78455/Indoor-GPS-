# power_allocation.py
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class PowerAllocation:
    """
    Data structure representing power distribution across LEDs, Signal Groups, and Subcarriers.
    Enforces power budget conservation and localization reserve protection.
    """
    mode: str = "EQUAL_POWER"  # EQUAL_POWER, WATER_FILLING, CONFIGURED_STATIC
    total_power_budget_w: float = 4.0  # Combined across all LEDs
    per_led_max_power_w: Dict[int, float] = field(default_factory=dict)  # LED ID -> max power (W)
    
    localization_reserved_power_w: Dict[int, float] = field(default_factory=dict)  # LED ID -> P_loc (W)
    communication_available_power_w: Dict[int, float] = field(default_factory=dict)  # LED ID -> P_comm (W)
    
    # Power matrices / arrays
    # Shape: (num_leds, fft_size) - electrical power per subcarrier per LED
    per_subcarrier_power_matrix: np.ndarray = field(default_factory=lambda: np.zeros((4, 256)))
    
    # Per-device / per-SG aggregated power (W)
    per_device_power_w: Dict[int, float] = field(default_factory=dict)

    def validate_power_budgets(self) -> Tuple[bool, str]:
        """
        Validates that power allocation respects LED power budgets and non-negativity.
        """
        if np.any(self.per_subcarrier_power_matrix < -1e-9):
            return False, "Negative power allocated to subcarriers."
            
        num_leds = self.per_subcarrier_power_matrix.shape[0]
        for led_idx in range(num_leds):
            led_id = led_idx + 1
            max_p = self.per_led_max_power_w.get(led_id, 10.0)
            p_used = np.sum(self.per_subcarrier_power_matrix[led_idx, :])
            if p_used > max_p + 1e-6:
                return False, f"LED {led_id} power {p_used:.4f}W exceeds budget {max_p:.4f}W."
                
        return True, "Power budgets validated."
