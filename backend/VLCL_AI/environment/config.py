import os
import yaml
from typing import Dict, Any, List
from dataclasses import dataclass, field
from loguru import logger

@dataclass
class RoomConfig:
    width: float = 5.0
    length: float = 5.0
    height: float = 3.0
    wall_reflectivity: float = 0.8
    floor_reflectivity: float = 0.2
    ceiling_reflectivity: float = 0.5

@dataclass
class LEDConfig:
    id: int
    position: List[float]
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, -1.0])
    power: float = 20.0
    bias_current: float = 0.5
    frequency: float = 100000.0
    lambertian_order: float = 1.0
    beam_angle: float = 60.0
    fov: float = 60.0
    communication_enabled: bool = True
    localization_enabled: bool = True

@dataclass
class ReceiverConfig:
    position: List[float] = field(default_factory=lambda: [2.5, 2.5, 0.85])
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    acceleration: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    fov: float = 70.0
    apd_size: float = 1e-4
    noise: float = 1e-14
    gain: float = 1.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

@dataclass
class MobilityConfig:
    type: str = "static"
    speed: float = 0.5
    radius: float = 1.5
    center: List[float] = field(default_factory=lambda: [2.5, 2.5, 0.85])
    waypoints: List[List[float]] = field(default_factory=lambda: [])

@dataclass
class ObstacleConfig:
    id: str
    type: str
    position: List[float]
    rotation: List[float]
    scale: List[float]
    reflectivity: float = 0.3
    material: str = "generic"

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

@dataclass
class VLCLConfig:
    room: RoomConfig = field(default_factory=RoomConfig)
    leds: List[LEDConfig] = field(default_factory=list)
    receiver: ReceiverConfig = field(default_factory=ReceiverConfig)
    mobility: MobilityConfig = field(default_factory=MobilityConfig)
    obstacles: List[ObstacleConfig] = field(default_factory=list)

class ConfigurationManager:
    """Loads, validates, and stores YAML/JSON configs for the simulation."""
    
    def __init__(self, filepath: str = None):
        self.config = VLCLConfig()
        if filepath:
            self.load_config(filepath)
            
    def load_config(self, filepath: str):
        if not os.path.exists(filepath):
            logger.warning(f"Config path {filepath} not found. Using defaults.")
            return
            
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            room_data = data.get("room", {})
            for fld in ["width", "length", "height", "wall_reflectivity", "floor_reflectivity", "ceiling_reflectivity"]:
                if fld in room_data and room_data[fld] is not None:
                    room_data[fld] = float(room_data[fld])
            room = RoomConfig(**room_data)
            
            leds = []
            for led_data in data.get("leds", []):
                for fld in ["power", "bias_current", "frequency", "lambertian_order", "beam_angle", "fov"]:
                    if fld in led_data and led_data[fld] is not None:
                        led_data[fld] = float(led_data[fld])
                leds.append(LEDConfig(**led_data))
                
            rx_data = data.get("receiver", {})
            for fld in ["fov", "apd_size", "noise", "gain", "roll", "pitch", "yaw"]:
                if fld in rx_data and rx_data[fld] is not None:
                    rx_data[fld] = float(rx_data[fld])
            receiver = ReceiverConfig(**rx_data)
            
            mob_data = data.get("mobility", {})
            for fld in ["speed", "radius"]:
                if fld in mob_data and mob_data[fld] is not None:
                    mob_data[fld] = float(mob_data[fld])
            mobility = MobilityConfig(**mob_data)
            
            obstacles = []
            for obs_data in data.get("obstacles", []):
                obstacles.append(ObstacleConfig(**obs_data))
                
            self.config = VLCLConfig(
                room=room,
                leds=leds,
                receiver=receiver,
                mobility=mobility,
                obstacles=obstacles
            )
            logger.info(f"Configuration loaded successfully from {filepath}")
        except Exception as e:
            logger.error(f"Error loading configuration from {filepath}: {e}. Falling back to default.")
            
    def get_config(self) -> VLCLConfig:
        return self.config
