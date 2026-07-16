import time
from typing import Dict, Any, List, Callable
from loguru import logger

from .state import EnvironmentState
from .scene import Scene
from .mobility import MobilityEngine

class EventDispatcher:
    """Dispatches environment events to registered subscriber callback hooks."""
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {
            "receiver_moved": [],
            "led_updated": [],
            "obstacle_added": [],
            "simulation_started": [],
            "simulation_stopped": []
        }

    def subscribe(self, event_type: str, callback: Callable):
        if event_type in self._listeners:
            self._listeners[event_type].append(callback)
            logger.debug(f"Subscribed callback to event '{event_type}'")
        else:
            logger.warning(f"Event type '{event_type}' is not supported.")

    def dispatch(self, event_type: str, *args, **kwargs):
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error executing callback for event '{event_type}': {e}")


class SimulationClock:
    """Manages the tick, delta-time, pausing, speed scale, and frame rates."""
    def __init__(self, time_step: float = 0.05, speed_factor: float = 1.0):
        self.time_step = time_step
        self.speed_factor = speed_factor
        self.simulation_time = 0.0
        self.frame_index = 0
        self.is_paused = False
        
        self.last_real_time = time.perf_counter()
        self.fps = 60.0

    def tick(self) -> float:
        """
        Advances the clock by time_step * speed_factor if not paused.
        Returns:
            float: delta time added to simulation time.
        """
        now = time.perf_counter()
        real_dt = now - self.last_real_time
        self.last_real_time = now
        
        # Calculate real rolling FPS
        if real_dt > 0:
            current_fps = 1.0 / real_dt
            self.fps = 0.95 * self.fps + 0.05 * current_fps # low pass filter
            
        if self.is_paused:
            return 0.0
            
        added_time = self.time_step * self.speed_factor
        self.simulation_time += added_time
        self.frame_index += 1
        return added_time

    def pause(self):
        self.is_paused = True
        logger.info("Simulation clock paused.")

    def resume(self):
        self.is_paused = False
        self.last_real_time = time.perf_counter()
        logger.info("Simulation clock resumed.")

    def reset(self):
        self.simulation_time = 0.0
        self.frame_index = 0
        self.is_paused = False
        self.last_real_time = time.perf_counter()
        logger.info("Simulation clock reset.")

    def set_speed(self, factor: float):
        self.speed_factor = max(0.1, min(10.0, factor))
        logger.info(f"Simulation speed factor set to {self.speed_factor}x")


class VLCLSimulator:
    """
    Primary orchestrator of the Integrated VLCL system simulator.
    Integrates Scene, Clock, Mobility, and Events.
    """
    def __init__(self, scene: Scene, mobility_engine: MobilityEngine, 
                 clock: SimulationClock = None):
        self.scene = scene
        self.mobility_engine = mobility_engine
        self.clock = clock if clock else SimulationClock()
        self.events = EventDispatcher()
        
        logger.info("VLCL Simulator engine initiated.")

    def start(self):
        self.clock.resume()
        self.events.dispatch("simulation_started")
        logger.info("VLCL Simulator started.")

    def stop(self):
        self.clock.pause()
        self.events.dispatch("simulation_stopped")
        logger.info("VLCL Simulator stopped.")

    def step(self) -> EnvironmentState:
        """
        Advances the simulation by one clock tick.
        Updates physical positions, recalculates LOS blockages, and captures snapshot state.
        """
        dt = self.clock.tick()
        
        # 1. Update positions in scene
        if dt > 0:
            self.scene.update(dt, self.mobility_engine)
            self.events.dispatch("receiver_moved", self.scene.receiver.position)
            
        # 2. Recalculate physical and geometric parameters
        metrics = self.scene.get_geometric_metrics()
        
        # 3. Form and return the immutable EnvironmentState snapshot
        state = EnvironmentState(
            current_time=self.clock.simulation_time,
            frame_index=self.clock.frame_index,
            fps=self.clock.fps,
            
            receiver_position=self.scene.receiver.position.tolist(),
            receiver_orientation=self.scene.receiver.orientation.tolist(),
            receiver_velocity=self.scene.receiver.velocity.tolist(),
            receiver_acceleration=self.scene.receiver.acceleration.tolist(),
            receiver_angles={
                "roll": self.scene.receiver.roll,
                "pitch": self.scene.receiver.pitch,
                "yaw": self.scene.receiver.yaw
            },
            
            led_positions={led_id: led.position.tolist() for led_id, led in self.scene.led_array.leds.items()},
            led_powers={led_id: led.power for led_id, led in self.scene.led_array.leds.items()},
            led_active={led_id: led.active for led_id, led in self.scene.led_array.leds.items()},
            
            distances=metrics["distances"],
            incident_angles=metrics["incident_angles"],
            irradiance_angles=metrics["irradiance_angles"],
            dc_gains=metrics["dc_gains"],
            
            visibility_matrix=metrics["visibility_matrix"],
            los_matrix=metrics["los_matrix"],
            blocking_obstacles=metrics["blocking_obstacles"],
            
            obstacles=[obs.to_dict() for obs in self.scene.obstacles.values()]
        )
        return state

    def get_state(self) -> EnvironmentState:
        """Force captures a state snapshot of the current frame without advancing time."""
        metrics = self.scene.get_geometric_metrics()
        return EnvironmentState(
            current_time=self.clock.simulation_time,
            frame_index=self.clock.frame_index,
            fps=self.clock.fps,
            receiver_position=self.scene.receiver.position.tolist(),
            receiver_orientation=self.scene.receiver.orientation.tolist(),
            receiver_velocity=self.scene.receiver.velocity.tolist(),
            receiver_acceleration=self.scene.receiver.acceleration.tolist(),
            receiver_angles={"roll": self.scene.receiver.roll, "pitch": self.scene.receiver.pitch, "yaw": self.scene.receiver.yaw},
            led_positions={lid: led.position.tolist() for lid, led in self.scene.led_array.leds.items()},
            led_powers={lid: led.power for lid, led in self.scene.led_array.leds.items()},
            led_active={lid: led.active for lid, led in self.scene.led_array.leds.items()},
            distances=metrics["distances"],
            incident_angles=metrics["incident_angles"],
            irradiance_angles=metrics["irradiance_angles"],
            dc_gains=metrics["dc_gains"],
            visibility_matrix=metrics["visibility_matrix"],
            los_matrix=metrics["los_matrix"],
            blocking_obstacles=metrics["blocking_obstacles"],
            obstacles=[obs.to_dict() for obs in self.scene.obstacles.values()]
        )
