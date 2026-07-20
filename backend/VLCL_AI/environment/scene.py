import numpy as np
from typing import List, Dict, Any, Union
from loguru import logger

from .room import Room
from .led import LED, LEDArray
from .receiver import Receiver
from .obstacle import Obstacle, create_obstacle
from .geometry import GeometryEngine

class Scene:
    """
    Manages all physical objects (room, ceiling emitters, receiver, obstacles)
    within the 3D experimental setup workspace.
    """
    def __init__(self, room: Room, receiver: Receiver, leds: List[LED] = None):
        self.room = room
        self.receiver = receiver
        self.led_array = LEDArray(leds)
        self.obstacles: Dict[str, Obstacle] = {}
        
        logger.info("Scene Manager initialized.")

    def add(self, obj: Union[LED, Obstacle]):
        """Adds an LED or Obstacle to the scene workspace."""
        if isinstance(obj, LED):
            self.led_array.add_led(obj)
        elif isinstance(obj, Obstacle):
            self.obstacles[obj.id] = obj
            logger.info(f"Added obstacle '{obj.id}' of type '{obj.type}' to scene.")
        else:
            logger.error("Unsupported object type added to Scene.")

    def remove(self, obj_id: Union[int, str]):
        """Removes an LED (integer id) or Obstacle (string id) from the scene."""
        if isinstance(obj_id, int):
            self.led_array.remove_led(obj_id)
        elif isinstance(obj_id, str):
            if obj_id in self.obstacles:
                del self.obstacles[obj_id]
                logger.info(f"Removed obstacle '{obj_id}' from scene.")
        else:
            logger.error("Invalid object ID key type.")

    def update(self, delta_time: float, mobility_engine: Any = None):
        """Updates the positions, kinematics, and alignments of entities in the scene."""
        # 1. Update receiver kinematics using mobility engine if provided
        if mobility_engine:
            new_pos, new_vel = mobility_engine.update_position(
                self.receiver.position, self.receiver.velocity, delta_time
            )
            # Resolve wall collisions
            collided, resolved_pos = GeometryEngine.check_room_boundaries_collision(
                new_pos, [self.room.width, self.room.length, self.room.height]
            )
            self.receiver.position = resolved_pos
            self.receiver.velocity = new_vel if not collided else -new_vel
        else:
            # Physics step fallback
            self.receiver.move(delta_time, max_bounds=np.array([self.room.width, self.room.length, self.room.height]))

    def get_geometric_metrics(self) -> Dict[str, Any]:
        """
        Computes distances, irradiance, incidence angles, visibility state,
        and LOS matrix for all LEDs in the room.

        ANGULAR UNIT CONTRACT (M1-ENV-ANGLE-001):
          incident_angles_rad and irradiance_angles_rad are in RADIANS.
          FOV comparisons are made against np.radians(self.receiver.fov)
          because receiver.fov is stored in degrees (config boundary).

        NOTE: dc_gains field has been REMOVED (M1-ENV-002).
          H(0) channel gain is exclusively computed by Module 2 (PhysicsEngine).
          Callers that need channel gain must call PhysicsEngine.compute(env_state).
        """
        distances = {}
        incidents_rad = {}
        irradiances_rad = {}
        visibility_matrix = {}
        los_matrix = {}
        blocking_obstacles = {}

        # Pre-convert receiver FOV to radians once (config boundary)
        rx_fov_rad = np.radians(self.receiver.fov)

        for led_id, led in self.led_array.leds.items():
            # 1. Base geometric distance
            dist = GeometryEngine.distance(led.position, self.receiver.position)
            distances[led_id] = float(dist)

            # 2. Emission and incident angles — returned in RADIANS (M1-ENV-ANGLE-001)
            phi_rad, psi_rad = GeometryEngine.calculate_angles(
                led.position, led.orientation,
                self.receiver.position, self.receiver.orientation
            )
            irradiances_rad[led_id] = float(phi_rad)
            incidents_rad[led_id] = float(psi_rad)

            # 3. FOV and cone containment visibility
            # Compare in radians (both sides now in radians — M1-ENV-ANGLE-001)
            led_fov_rad = np.radians(led.fov)
            rx_visible = psi_rad <= rx_fov_rad
            tx_visible = phi_rad <= led_fov_rad
            visibility_matrix[led_id] = bool(rx_visible and tx_visible and led.active)

            # 4. Obstacle LOS blockages
            is_los, blocking_obs_id = GeometryEngine.is_visible_los(
                led.position, self.receiver.position, list(self.obstacles.values())
            )
            los_matrix[led_id] = bool(is_los)
            blocking_obstacles[led_id] = blocking_obs_id if blocking_obs_id else ""

            # NOTE: dc_gains (H(0)) computation removed — M1-ENV-002.
            # Module 2 (PhysicsEngine) is the sole owner of channel gain.

        return {
            "distances": distances,
            "incident_angles_rad": incidents_rad,    # RADIANS (M1-ENV-ANGLE-001)
            "irradiance_angles_rad": irradiances_rad, # RADIANS (M1-ENV-ANGLE-001)
            # dc_gains REMOVED (M1-ENV-002) — use PhysicsState.los_gains instead
            "visibility_matrix": visibility_matrix,
            "los_matrix": los_matrix,
            "blocking_obstacles": blocking_obstacles,
            # INT-001: per-LED primitives for Module 2 consumption
            "led_orientations": {lid: led.orientation.tolist() for lid, led in self.led_array.leds.items()},
            "led_beam_angles": {lid: led.beam_angle for lid, led in self.led_array.leds.items()},
        }

        
    def render(self) -> Dict[str, Any]:
        """Exports full scene structure specs for interactive Web/Plotly visualization."""
        return {
            "room": self.room.to_dict(),
            "leds": self.led_array.to_list(),
            "receiver": self.receiver.to_dict(),
            "obstacles": [obs.to_dict() for obs in self.obstacles.values()]
        }
