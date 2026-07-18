# raytracer.py
import numpy as np
from typing import List, Dict, Any, Tuple
from VLCL_AI.physics.lambertian import radiation_pattern

class RayTracer:
    def __init__(self, room_dims: List[float], ray_count: int = 100, max_bounces: int = 2):
        self.room_dims = room_dims
        self.ray_count = ray_count
        self.max_bounces = max_bounces
        
    def generate_rays_from_led(
        self,
        led_pos: np.ndarray,
        led_normal: np.ndarray,
        m: float,
        power: float
    ) -> List[np.ndarray]:
        """
        Generates sample directions for 'ray_count' rays according to the Lambertian distribution.
        """
        rays = []
        # Find coordinate frame with led_normal as z-axis
        z_axis = led_normal / np.linalg.norm(led_normal)
        if np.abs(z_axis[0]) < 0.9:
            x_axis = np.cross(z_axis, [1.0, 0.0, 0.0])
        else:
            x_axis = np.cross(z_axis, [0.0, 1.0, 0.0])
        x_axis /= np.linalg.norm(x_axis)
        y_axis = np.cross(z_axis, x_axis)
        
        for _ in range(self.ray_count):
            # Generate Lambertian distributed angles
            # theta distributed as cos^m(theta)
            u = np.random.rand()
            theta = np.arccos(u ** (1.0 / (m + 1.0)))
            phi = 2 * np.pi * np.random.rand()
            
            # Local direction
            dx = np.sin(theta) * np.cos(phi)
            dy = np.sin(theta) * np.sin(phi)
            dz = np.cos(theta)
            
            # Global direction
            global_dir = dx * x_axis + dy * y_axis + dz * z_axis
            global_dir /= np.linalg.norm(global_dir)
            
            rays.append(global_dir)
            
        return rays

    def intersect_room(self, origin: np.ndarray, direction: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculates intersection point and normal of a ray colliding with the room boundaries.
        Returns: (intersection_point, normal, distance)
        """
        W, L, H = self.room_dims
        t_min = float('inf')
        norm_min = np.zeros(3)
        
        # Check X walls
        if direction[0] != 0:
            for x_val, n in [(0.0, [1.0, 0.0, 0.0]), (W, [-1.0, 0.0, 0.0])]:
                t = (x_val - origin[0]) / direction[0]
                if t > 1e-5 and t < t_min:
                    pt = origin + t * direction
                    if 0 <= pt[1] <= L and 0 <= pt[2] <= H:
                        t_min = t
                        norm_min = np.array(n)
                        
        # Check Y walls
        if direction[1] != 0:
            for y_val, n in [(0.0, [0.0, 1.0, 0.0]), (L, [-1.0, 0.0, 0.0])]:
                t = (y_val - origin[1]) / direction[1]
                if t > 1e-5 and t < t_min:
                    pt = origin + t * direction
                    if 0 <= pt[0] <= W and 0 <= pt[2] <= H:
                        t_min = t
                        norm_min = np.array(n)
                        
        # Check Z walls
        if direction[2] != 0:
            for z_val, n in [(0.0, [0.0, 0.0, 1.0]), (H, [0.0, 0.0, -1.0])]:
                t = (z_val - origin[2]) / direction[2]
                if t > 1e-5 and t < t_min:
                    pt = origin + t * direction
                    if 0 <= pt[0] <= W and 0 <= pt[1] <= L:
                        t_min = t
                        norm_min = np.array(n)
                        
        return origin + t_min * direction, norm_min, t_min

    def intersect_cylinder_obstacle(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        cyl_center: np.ndarray,
        cyl_radius: float,
        cyl_height: float
    ) -> Tuple[float, np.ndarray]:
        """
        Calculates Ray-Cylinder intersection (analytical).
        cylinder axis is vertical (aligned along Z axis, from z=0 to z=cyl_height).
        """
        # project onto XY plane
        ox, oy = origin[0] - cyl_center[0], origin[1] - cyl_center[1]
        dx, dy = direction[0], direction[1]
        
        a = dx**2 + dy**2
        if a < 1e-12:
            return float('inf'), np.zeros(3)
            
        b = 2 * (ox * dx + oy * dy)
        c = ox**2 + oy**2 - cyl_radius**2
        
        disc = b**2 - 4*a*c
        if disc < 0:
            return float('inf'), np.zeros(3)
            
        t1 = (-b - np.sqrt(disc)) / (2*a)
        t2 = (-b + np.sqrt(disc)) / (2*a)
        
        for t in [t1, t2]:
            if t > 1e-5:
                # check Z bounds
                z_hit = origin[2] + t * direction[2]
                if 0 <= z_hit <= cyl_height:
                    hit_point = origin + t * direction
                    # normal vector at cylinder surface
                    normal = np.array([hit_point[0] - cyl_center[0], hit_point[1] - cyl_center[1], 0.0])
                    normal /= np.linalg.norm(normal)
                    return t, normal
                    
        return float('inf'), np.zeros(3)

    def trace_rays(
        self,
        leds: List[Dict[str, Any]],
        obstacles: List[Dict[str, Any]],
        receiver_pos: np.ndarray,
        receiver_fov_rad: float,
        receiver_normal: np.ndarray
    ) -> Dict[str, Any]:
        """
        Traces rays from all active LEDs, tracking collisions and reflections.
        """
        traced_led_paths = {}
        blocked_ray_count = 0
        total_rays = 0
        
        for led in leds:
            led_id = led["id"]
            pos = np.array(led["position"])
            norm = np.array(led.get("orientation", [0.0, 0.0, -1.0]))
            power = led.get("power", 20.0)
            m = led.get("lambertian_order", 1.0)
            
            ray_dirs = self.generate_rays_from_led(pos, norm, m, power)
            paths = []
            
            for d in ray_dirs:
                current_origin = pos.copy()
                current_dir = d.copy()
                current_intensity = power / self.ray_count
                
                path_pts = [current_origin.tolist()]
                total_rays += 1
                
                # Check intersection with obstacle (e.g. human blocker)
                blocked = False
                for obs in obstacles:
                    if obs.get("type") == "cylinder" or "obs_human" in str(obs.get("id")):
                        cyl_pos = np.array(obs["position"])
                        cyl_rad = obs.get("radius", 0.3)
                        cyl_h = obs.get("height", 1.8)
                        
                        t_obs, norm_obs = self.intersect_cylinder_obstacle(
                            current_origin, current_dir, cyl_pos, cyl_rad, cyl_h
                        )
                        
                        # Room boundary intersection to check if obstacle is closer
                        room_hit, _, t_room = self.intersect_room(current_origin, current_dir)
                        
                        if t_obs < t_room:
                            # Ray hit obstacle!
                            hit_pt = current_origin + t_obs * current_dir
                            path_pts.append(hit_pt.tolist())
                            blocked = True
                            blocked_ray_count += 1
                            break
                            
                if not blocked:
                    # Let's hit room boundary
                    room_hit, _, _ = self.intersect_room(current_origin, current_dir)
                    path_pts.append(room_hit.tolist())
                    
                paths.append({
                    "points": path_pts,
                    "intensity": current_intensity,
                    "blocked": blocked
                })
                
            traced_led_paths[led_id] = paths
            
        return {
            "traced_paths": traced_led_paths,
            "blocked_rays": blocked_ray_count,
            "total_rays": total_rays,
            "blockage_probability": blocked_ray_count / total_rays if total_rays > 0 else 0.0
        }
