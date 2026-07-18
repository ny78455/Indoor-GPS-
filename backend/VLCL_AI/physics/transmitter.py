# transmitter.py
from dataclasses import dataclass, field
from typing import List, Optional
from VLCL_AI.physics.lambertian import lambertian_order
from VLCL_AI.physics.constants import DEFAULT_WAVELENGTH

@dataclass
class LEDTransmitter:
    id: int
    position: List[float]
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, -1.0])
    power: float = 20.0  # Transmit power (W)
    bias_current: float = 0.5  # Bias current (A)
    frequency: float = 100000.0  # Hz
    beam_angle: float = 60.0  # Degree (semi-angle at half power)
    wavelength: float = DEFAULT_WAVELENGTH  # m
    communication_enabled: bool = True
    localization_enabled: bool = True
    
    @property
    def lambertian_order(self) -> float:
        return lambertian_order(self.beam_angle)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "position": self.position,
            "orientation": self.orientation,
            "power": self.power,
            "bias_current": self.bias_current,
            "frequency": self.frequency,
            "beam_angle": self.beam_angle,
            "wavelength": self.wavelength,
            "lambertian_order": self.lambertian_order,
            "communication_enabled": self.communication_enabled,
            "localization_enabled": self.localization_enabled
        }
