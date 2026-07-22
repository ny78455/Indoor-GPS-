# subcarrier_grid.py
import numpy as np
from typing import Dict, List, Optional
from VLCL_AI.communication.subcarrier import Subcarrier, SubcarrierPurpose

class SubcarrierGrid:
    """
    Manages the OFDM subcarrier grid configuration and indexing.
    Supports flexible, trace-level bandwidth allocation for future research.
    """
    
    def __init__(
        self,
        fft_size: int = 256,
        total_bandwidth: float = 20e6,
        sample_rate: float = 50e6,
        guard_low: int = 4,
        guard_high: int = 4,
        pilot_spacing: int = 16,
        reserve_localization: bool = True
    ):
        self.fft_size = fft_size
        self.total_bandwidth = total_bandwidth
        self.sample_rate = sample_rate
        self.guard_low = guard_low
        self.guard_high = guard_high
        self.pilot_spacing = pilot_spacing
        self.reserve_localization = reserve_localization
        
        self.subcarriers: Dict[int, Subcarrier] = {}
        self._build_grid()

    @property
    def subcarrier_spacing(self) -> float:
        """Returns the subcarrier spacing in Hz (sample_rate / fft_size)."""
        return self.sample_rate / self.fft_size

    def _build_grid(self):
        """Initializes the OFDM subcarriers and their assigned purposes."""
        # Subcarrier bandwidth spacing
        subcarrier_spacing = self.total_bandwidth / self.fft_size
        
        for k in range(self.fft_size):
            # Center frequency for subcarrier k relative to baseband (0 to Fs)
            freq = k * (self.sample_rate / self.fft_size)
            
            # Default state
            purpose = SubcarrierPurpose.COMMUNICATION
            active = True
            pilot = False
            reserved = False
            
            # 1. DC Carrier (k=0)
            if k == 0:
                purpose = SubcarrierPurpose.DC
                active = False
                
            # 2. Nyquist/middle carrier (k = N/2)
            elif k == self.fft_size // 2:
                purpose = SubcarrierPurpose.GUARD
                active = False
                
            # 3. Guard bands (low edge and high edge)
            elif k < self.guard_low:
                purpose = SubcarrierPurpose.GUARD
                active = False
            elif k >= self.fft_size - self.guard_high:
                purpose = SubcarrierPurpose.GUARD
                active = False
                
            # 4. Localization reservation k in [10, 20] or similar (e.g. k=10, 11, 12, 13, 14, 15)
            elif self.reserve_localization and (5 <= k <= 9):
                purpose = SubcarrierPurpose.LOCALIZATION_RESERVED
                active = False
                reserved = True
                
            # 5. Pilots (assigned every 'pilot_spacing' index within communication band)
            elif k % self.pilot_spacing == 0:
                purpose = SubcarrierPurpose.PILOT
                pilot = True
                
            self.subcarriers[k] = Subcarrier(
                index=k,
                center_frequency=freq,
                bandwidth=subcarrier_spacing,
                active=active,
                pilot=pilot,
                reserved=reserved,
                purpose=purpose
            )

    def get_subcarriers_by_purpose(self, purpose: SubcarrierPurpose) -> List[Subcarrier]:
        return [sc for sc in self.subcarriers.values() if sc.purpose == purpose]

    def get_active_indices(self) -> List[int]:
        """Returns indices of active communication subcarriers (excluding guards, DC, pilots, reserved)."""
        return [k for k, sc in self.subcarriers.items() if sc.active and sc.purpose == SubcarrierPurpose.COMMUNICATION]

    def get_pilot_indices(self) -> List[int]:
        return [k for k, sc in self.subcarriers.items() if sc.pilot]

    def to_dict(self) -> List[dict]:
        """Returns list representation of grid for frontend representation."""
        return [
            {
                "index": sc.index,
                "center_frequency": sc.center_frequency,
                "bandwidth": sc.bandwidth,
                "power": sc.power,
                "modulation_order": sc.modulation_order,
                "assigned_user": sc.assigned_user,
                "active": sc.active,
                "pilot": sc.pilot,
                "purpose": sc.purpose.value
            }
            for sc in self.subcarriers.values()
        ]
