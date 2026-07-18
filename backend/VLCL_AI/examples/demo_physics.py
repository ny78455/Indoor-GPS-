# demo_physics.py
import os
import sys
import time
from loguru import logger
from rich.console import Console
from rich.table import Table

# Add project root to path to ensure relative imports work when executing directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from VLCL_AI.environment.config import ConfigurationManager
from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.obstacle import create_obstacle
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.mobility import MobilityEngine
from VLCL_AI.environment.simulator import VLCLSimulator, SimulationClock
from VLCL_AI.physics.physics_engine import PhysicsEngine
from VLCL_AI.physics.raytracer import RayTracer

def run_physics_demo():
    console = Console()
    console.print("[bold cyan]===================================================================[/bold cyan]")
    console.print("[bold cyan]   VLCL High-Fidelity Optical Wireless Physics Engine (Module 2)   [/bold cyan]")
    console.print("[bold cyan]===================================================================[/bold cyan]")
    
    # 1. Load configuration
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "default.yaml")
    logger.info(f"Loading configurations from {config_file}")
    cfg_manager = ConfigurationManager(config_file)
    cfg = cfg_manager.get_config()
    
    # 2. Build Scene components
    room = Room(
        width=cfg.room.width,
        length=cfg.room.length,
        height=cfg.room.height,
        wall_reflectivity=cfg.room.wall_reflectivity,
        floor_reflectivity=cfg.room.floor_reflectivity,
        ceiling_reflectivity=cfg.room.ceiling_reflectivity
    )
    
    receiver = Receiver(
        position=cfg.receiver.position,
        orientation=cfg.receiver.orientation,
        velocity=cfg.receiver.velocity,
        acceleration=cfg.receiver.acceleration,
        fov=cfg.receiver.fov,
        apd_size=cfg.receiver.apd_size,
        noise=cfg.receiver.noise,
        gain=cfg.receiver.gain,
        roll=cfg.receiver.roll,
        pitch=cfg.receiver.pitch,
        yaw=cfg.receiver.yaw
    )
    
    led_list = []
    for led_cfg in cfg.leds:
        led = LED(
            led_id=led_cfg.id,
            position=led_cfg.position,
            orientation=led_cfg.orientation,
            power=led_cfg.power,
            bias_current=led_cfg.bias_current,
            frequency=led_cfg.frequency,
            lambertian_order=led_cfg.lambertian_order,
            beam_angle=led_cfg.beam_angle,
            fov=led_cfg.fov,
            communication_enabled=led_cfg.communication_enabled,
            localization_enabled=led_cfg.localization_enabled
        )
        led_list.append(led)
        
    scene = Scene(room=room, receiver=receiver, leds=led_list)
    for obs_cfg in cfg.obstacles:
        scene.add(create_obstacle(obs_cfg.to_dict()))
        
    # 3. Instantiate Engines
    mobility_engine = MobilityEngine(
        mobility_type=cfg.mobility.type,
        speed=cfg.mobility.speed,
        radius=cfg.mobility.radius,
        center=cfg.mobility.center,
        waypoints=cfg.mobility.waypoints,
        room_bounds=[room.width, room.length, room.height]
    )
    
    clock = SimulationClock(time_step=0.05, speed_factor=1.0)
    simulator = VLCLSimulator(scene=scene, mobility_engine=mobility_engine, clock=clock)
    
    physics_engine = PhysicsEngine(config_path=config_file)
    ray_tracer = RayTracer(room_dims=[room.width, room.length, room.height], ray_count=100)
    
    # 4. Simulation Loop
    total_frames = 100
    simulator.start()
    
    table = Table(title="Live Optical Physics & Signal Telemetry Log")
    table.add_column("Frame", justify="center", style="cyan")
    table.add_column("Sim Time (s)", justify="center", style="magenta")
    table.add_column("Average SNR (dB)", justify="right", style="green")
    table.add_column("Total Recv Power (uW)", justify="right", style="yellow")
    table.add_column("Blockage Prob", justify="right", style="red")
    table.add_column("Visible LEDs", justify="center", style="cyan")
    
    for frame in range(1, total_frames + 1):
        env_state = simulator.step()
        
        # Step Physics Engine (Module 2)
        physics_state = physics_engine.step(env_state)
        
        # Step Ray Tracer (Module 2)
        ray_results = ray_tracer.trace_rays(
            leds=[led.to_dict() for led in led_list],
            obstacles=env_state.obstacles,
            receiver_pos=env_state.receiver_position,
            receiver_normal=env_state.receiver_orientation,
            receiver_fov_rad=cfg.receiver.fov
        )
        
        if frame % 10 == 0 or frame == 1:
            avg_snr = physics_state.metrics["average_snr"]
            tot_pwr_uw = physics_state.metrics["total_optical_power"] * 1e6
            block_p = ray_results["blockage_probability"]
            visible_count = physics_state.metrics["visible_leds"]
            
            table.add_row(
                str(env_state.frame_index),
                f"{env_state.current_time:.2f}",
                f"{avg_snr:.2f}",
                f"{tot_pwr_uw:.2f}",
                f"{block_p * 100:.1f}%",
                str(visible_count)
            )
            
        time.sleep(0.005)
        
    simulator.stop()
    console.print(table)
    console.print("[bold green]✓ High-fidelity Physics Simulation Run Completed Successfully![/bold green]")

if __name__ == "__main__":
    run_physics_demo()
