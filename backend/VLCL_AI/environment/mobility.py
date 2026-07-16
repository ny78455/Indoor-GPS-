import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger

class MobilityEngine:
    """
    Simulates various kinetic trajectories of mobile terminals in the laboratory.
    Supports Static, Linear, Circular, Random Walk, Waypoint navigation, and Splines.
    """
    def __init__(self, mobility_type: str = "static", speed: float = 0.5, 
                 radius: float = 1.5, center: Tuple[float, float, float] = (2.5, 2.5, 0.85),
                 waypoints: List[List[float]] = None, room_bounds: List[float] = None):
        self.type = mobility_type.lower()
        self.speed = speed
        self.radius = radius
        self.center = np.array(center, dtype=float)
        self.waypoints = [np.array(wp, dtype=float) for wp in waypoints] if waypoints else []
        self.room_bounds = room_bounds if room_bounds else [5.0, 5.0, 3.0]
        
        self.time_elapsed = 0.0
        self.waypoint_index = 0
        self.random_walk_timer = 0.0
        self.random_direction = np.array([1.0, 0.0, 0.0])
        
        logger.info(f"Mobility engine set up with type: {self.type}")

    def update_position(self, current_pos: np.ndarray, current_vel: np.ndarray, 
                        dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Updates the position and velocity based on the selected mobility pattern and delta time.
        Returns:
            Tuple[np.ndarray, np.ndarray]: (new_position, new_velocity)
        """
        self.time_elapsed += dt
        
        if self.type == "static":
            return current_pos, np.array([0.0, 0.0, 0.0])
            
        elif self.type == "linear":
            # Linear continuous movement with velocity
            # Bound inside room, reverse velocity if colliding with walls
            new_pos = current_pos + current_vel * dt
            new_vel = np.copy(current_vel)
            
            # Wall collisions: boundary bounce back
            for i in range(2): # X and Y directions
                if new_pos[i] < 0.1:
                    new_pos[i] = 0.1
                    new_vel[i] = -new_vel[i]
                elif new_pos[i] > (self.room_bounds[i] - 0.1):
                    new_pos[i] = self.room_bounds[i] - 0.1
                    new_vel[i] = -new_vel[i]
            return new_pos, new_vel
            
        elif self.type == "circular":
            # Circular movement on horizontal plane (Z is fixed)
            # theta = omega * t
            omega = self.speed / self.radius if self.radius > 0 else 0
            theta = omega * self.time_elapsed
            
            new_x = self.center[0] + self.radius * np.cos(theta)
            new_y = self.center[1] + self.radius * np.sin(theta)
            new_z = self.center[2]
            
            # Compute instantaneous velocity vector
            vx = -self.speed * np.sin(theta)
            vy = self.speed * np.cos(theta)
            vz = 0.0
            
            return np.array([new_x, new_y, new_z]), np.array([vx, vy, vz])
            
        elif self.type == "random_walk":
            # Updates direction randomly every 2 seconds
            self.random_walk_timer += dt
            new_vel = np.copy(current_vel)
            if self.random_walk_timer > 2.0 or np.linalg.norm(current_vel) == 0:
                self.random_walk_timer = 0.0
                angle = np.random.uniform(0, 2 * np.pi)
                self.random_direction = np.array([np.cos(angle), np.sin(angle), 0.0])
                new_vel = self.random_direction * self.speed
                
            new_pos = current_pos + new_vel * dt
            
            # Handle boundary collisions
            for i in range(2):
                if new_pos[i] < 0.1:
                    new_pos[i] = 0.1
                    new_vel[i] = -new_vel[i]
                elif new_pos[i] > (self.room_bounds[i] - 0.1):
                    new_pos[i] = self.room_bounds[i] - 0.1
                    new_vel[i] = -new_vel[i]
                    
            return new_pos, new_vel
            
        elif self.type in ["waypoint", "spline"]:
            # Waypoint-based trajectory
            if not self.waypoints:
                return current_pos, np.array([0.0, 0.0, 0.0])
                
            target_wp = self.waypoints[self.waypoint_index]
            to_target = target_wp - current_pos
            distance = np.linalg.norm(to_target)
            
            # If reached current waypoint, target next
            if distance < 0.15:
                self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
                target_wp = self.waypoints[self.waypoint_index]
                to_target = target_wp - current_pos
                distance = np.linalg.norm(to_target)
                
            if distance > 0:
                direction = to_target / distance
                new_vel = direction * self.speed
                new_pos = current_pos + new_vel * dt
            else:
                new_vel = np.array([0.0, 0.0, 0.0])
                new_pos = current_pos
                
            return new_pos, new_vel
            
        else:
            return current_pos, np.array([0.0, 0.0, 0.0])
            
    def get_full_trajectory_points(self, num_points: int = 200) -> List[List[float]]:
        """Generates a list of coordinates mapping the complete trajectory path."""
        points = []
        if self.type == "circular":
            for theta in np.linspace(0, 2 * np.pi, num_points):
                x = self.center[0] + self.radius * np.cos(theta)
                y = self.center[1] + self.radius * np.sin(theta)
                z = self.center[2]
                points.append([x, y, z])
        elif self.type in ["waypoint", "spline"] and self.waypoints:
            for wp in self.waypoints:
                points.append(wp.tolist())
            # Close loop
            points.append(self.waypoints[0].tolist())
        elif self.type == "linear":
            # Simple line bounding inside room
            points.append([0.5, 0.5, self.center[2]])
            points.append([self.room_bounds[0] - 0.5, self.room_bounds[1] - 0.5, self.center[2]])
        else:
            points.append(self.center.tolist())
        return points
