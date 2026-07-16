import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger
from .coordinate_system import CoordinateSystem

class LED:
    """
    Represents an individual physical LED emitter in the Integrated VLCL system.
    """
    def __init__(self, led_id: int, position: np.ndarray, orientation: np.ndarray,
                 power: float = 20.0, bias_current: float = 0.5, frequency: float = 100000.0,
                 lambertian_order: float = 1.0, beam_angle: float = 60.0, fov: float = 60.0,
                 communication_enabled: bool = True, localization_enabled: bool = True):
        self.id = led_id
        self.position = np.array(position, dtype=float)
        self.orientation = CoordinateSystem.normalize_vector(orientation)
        self.power = power  # Transmit Optical Power (W)
        self.bias_current = bias_current  # DC bias current (A)
        self.frequency = frequency  # Subcarrier frequency for localization/communication identification (Hz)
        self.lambertian_order = lambertian_order  # Lambertian order (m)
        self.beam_angle = beam_angle  # Semi-angle at half power (degrees)
        self.fov = fov  # Field of View cone angle (degrees)
        self.active = True
        self.communication_enabled = communication_enabled
        self.localization_enabled = localization_enabled
        
        # Calculate Lambertian order if not specified explicitly
        if self.lambertian_order <= 1.0 and beam_angle < 90.0:
            # m = -ln(2) / ln(cos(theta_half))
            rad_half = np.radians(beam_angle)
            if np.cos(rad_half) > 0:
                self.lambertian_order = -np.log(2.0) / np.log(np.cos(rad_half))
                
        logger.info(f"Initialized LED {self.id} at {self.position.tolist()} with power {self.power}W (Lambertian Order: {self.lambertian_order:.2f})")

    def turn_on(self):
        self.active = True
        logger.debug(f"LED {self.id} turned ON")

    def turn_off(self):
        self.active = False
        logger.debug(f"LED {self.id} turned OFF")

    def update_power(self, power: float):
        self.power = power
        logger.debug(f"LED {self.id} power updated to {power}W")

    def rotate(self, roll: float, pitch: float, yaw: float):
        """Rotates the LED transmitter vector."""
        R = CoordinateSystem.get_rotation_matrix(roll, pitch, yaw)
        self.orientation = CoordinateSystem.normalize_vector(R @ self.orientation)
        logger.debug(f"LED {self.id} rotated. New orientation: {self.orientation.tolist()}")

    def move(self, new_position: np.ndarray):
        self.position = np.array(new_position, dtype=float)
        logger.debug(f"LED {self.id} moved to {self.position.tolist()}")

    def generate_light_cone_points(self, height: float = 2.0, num_points: int = 20) -> List[np.ndarray]:
        """Generates 3D coordinates representing the boundaries of the emission cone."""
        # Find orthogonal vectors to form circle
        z_axis = self.orientation
        if np.allclose(z_axis, [0, 0, 1]) or np.allclose(z_axis, [0, 0, -1]):
            x_axis = np.array([1, 0, 0])
        else:
            x_axis = np.cross(z_axis, [0, 0, 1])
        x_axis = CoordinateSystem.normalize_vector(x_axis)
        y_axis = CoordinateSystem.normalize_vector(np.cross(z_axis, x_axis))
        
        # Radius at distance height
        cone_radius = height * np.tan(np.radians(self.fov / 2.0))
        points = []
        for theta in np.linspace(0, 2 * np.pi, num_points):
            offset = height * z_axis + cone_radius * (np.cos(theta) * x_axis + np.sin(theta) * y_axis)
            points.append(self.position + offset)
        return points

    def generate_coverage_area(self, receiver_height: float) -> Tuple[np.ndarray, float]:
        """Calculates center point and radius of coverage circle at a specific height level."""
        # Calculate intersection of orientation ray with plane Z = receiver_height
        z_diff = receiver_height - self.position[2]
        if self.orientation[2] == 0:
            return self.position, 0.0 # Parallel to floor
            
        t = z_diff / self.orientation[2]
        if t < 0:
            return self.position, 0.0 # Facing away
            
        intersection_center = self.position + t * self.orientation
        # Approximate coverage radius
        distance = np.linalg.norm(intersection_center - self.position)
        radius = distance * np.tan(np.radians(self.fov / 2.0))
        return intersection_center, radius

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "position": self.position.tolist(),
            "orientation": self.orientation.tolist(),
            "power": self.power,
            "bias_current": self.bias_current,
            "frequency": self.frequency,
            "lambertian_order": self.lambertian_order,
            "beam_angle": self.beam_angle,
            "fov": self.fov,
            "active": self.active,
            "communication_enabled": self.communication_enabled,
            "localization_enabled": self.localization_enabled
        }


class LEDArray:
    """
    Manages and coordinates multiple LED emitters on the ceiling.
    """
    def __init__(self, leds: List[LED] = None):
        self.leds: Dict[int, LED] = {}
        if leds:
            for led in leds:
                self.add_led(led)

    def add_led(self, led: LED):
        self.leds[led.id] = led
        logger.debug(f"Added LED {led.id} to LEDArray")

    def remove_led(self, led_id: int):
        if led_id in self.leds:
            del self.leds[led_id]
            logger.debug(f"Removed LED {led_id} from LEDArray")

    def turn_all_on(self):
        for led in self.leds.values():
            led.turn_on()
        logger.debug("All array LEDs turned ON")

    def turn_all_off(self):
        for led in self.leds.values():
            led.turn_off()
        logger.debug("All array LEDs turned OFF")

    def update_all_powers(self, power_map: Dict[int, float]):
        for led_id, power in power_map.items():
            if led_id in self.leds:
                self.leds[led_id].update_power(power)

    def get_nearest_led(self, receiver_position: np.ndarray) -> LED:
        """Finds and returns the LED closest to the receiver's coordinates."""
        nearest_led = None
        min_dist = float('inf')
        for led in self.leds.values():
            dist = np.linalg.norm(led.position - receiver_position)
            if dist < min_dist:
                min_dist = dist
                nearest_led = led
        return nearest_led

    def broadcast_signals(self, signal_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """Simulates broadcasting data frame signals from LEDs to receiver."""
        broadcast_status = {}
        for led_id, led in self.leds.items():
            if led.active:
                broadcast_status[led_id] = {
                    "power": led.power,
                    "frequency": led.frequency,
                    "comm_enabled": led.communication_enabled,
                    "loc_enabled": led.localization_enabled,
                    "payload": signal_data
                }
        return broadcast_status

    def to_list(self) -> List[Dict[str, Any]]:
        return [led.to_dict() for led in self.leds.values()]
