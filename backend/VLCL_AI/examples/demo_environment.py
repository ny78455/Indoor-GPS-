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
from VLCL_AI.environment.visualization import Offline3DVisualizer
from VLCL_AI.physics.physics_engine import PhysicsEngine

def run_demo():
    console = Console()
    console.print("[bold cyan]=======================================================[/bold cyan]")
    console.print("[bold cyan]   VLCL Research Lab 3D Digital Twin Simulation Engine  [/bold cyan]")
    console.print("[bold cyan]=======================================================[/bold cyan]")
    
    # 1. Load configuration
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "default.yaml")
    logger.info(f"Loading YAML simulation configurations from {config_file}")
    cfg_manager = ConfigurationManager(config_file)
    cfg = cfg_manager.get_config()
    
    # 2. Build Room, Receiver, LEDs, Obstacles from loaded config
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
    
    # Add obstacles from config
    for obs_cfg in cfg.obstacles:
        obstacle = create_obstacle(obs_cfg.to_dict())
        scene.add(obstacle)
        
    # 3. Instantiate Mobility and Simulator
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
    physics_engine = PhysicsEngine()
    
    # 4. Instantiate Visualizer
    visualizer = Offline3DVisualizer(room_dims=[room.width, room.length, room.height])
    
    # 5. Execute Simulation Frame Loop (Simulate 10 seconds of runtime = 200 frames)
    total_frames = 200
    logger.info(f"Starting real-time simulation run loop for {total_frames} frames...")
    simulator.start()
    
    table = Table(title="Live Simulation Terminal Telemetry Snapshot (Sampled)")
    table.add_column("Frame", justify="center", style="cyan")
    table.add_column("Sim Time (s)", justify="center", style="magenta")
    table.add_column("Rx Position (X, Y, Z)", style="green")
    table.add_column("LED 1 SNR/Pwr", style="yellow")
    table.add_column("LED 2 SNR/Pwr", style="yellow")
    table.add_column("LOS Blockages", style="red")
    
    for frame in range(1, total_frames + 1):
        # Step simulation physics
        env_state = simulator.step()
        phys_state = physics_engine.compute(env_state)
        
        # Save trajectory coordinates for 3D visualizer trace map
        visualizer.add_trajectory_point(env_state.receiver_position)
        
        # Sample log print every 20 frames to avoid terminal clutter
        if frame % 20 == 0 or frame == 1:
            blockages_str = ", ".join([f"LED {lid}: blocked" for lid, val in env_state.visibility_matrix.items() if not env_state.los_matrix[lid]])
            if not blockages_str:
                blockages_str = "None (Full Clear LOS)"
                
            # Safely get LED 1 and LED 2 data (handles both integer and string IDs) from physics state
            l1_snr = phys_state.snrs.get(1, phys_state.snrs.get("1", 0.0))
            l1_pwr = phys_state.received_powers.get(1, phys_state.received_powers.get("1", 0.0))
            
            l2_snr = phys_state.snrs.get(2, phys_state.snrs.get("2", 0.0))
            l2_pwr = phys_state.received_powers.get(2, phys_state.received_powers.get("2", 0.0))
            
            table.add_row(
                str(env_state.frame_index),
                f"{env_state.current_time:.2f}",
                f"[{env_state.receiver_position[0]:.2f}, {env_state.receiver_position[1]:.2f}, {env_state.receiver_position[2]:.2f}]",
                f"{l1_snr:.1f}dB / {l1_pwr:.1e}W",
                f"{l2_snr:.1f}dB / {l2_pwr:.1e}W",
                blockages_str
            )
            
        # Optional short sleep to simulate real-time rendering intervals if desired
        time.sleep(0.005)
        
    simulator.stop()
    console.print(table)
    
    # 6. Export beautiful offline 3D interactive plot
    html_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "simulation_3d.html")
    exported_path = visualizer.generate_interactive_html(scene.render(), env_state, filename=html_file)
    
    console.print(f"[bold green]Simulation run completed successfully![/bold green]")
    console.print(f"[bold green]High-fidelity interactive 3D Web Digital Twin exported to: {exported_path}[/bold green]")
    
if __name__ == "__main__":
    run_demo()
