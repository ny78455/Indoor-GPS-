# Integrated Visible Light Communication and Localization (VLCL) Simulation Environment (Module 1)

This package contains **Module 1 (Environment & 3D Physical Digital Twin)** of a research-grade simulation framework for indoor Visible Light Communication (VLC) and Localization systems. It is structured using object-oriented, highly scalable design patterns, enabling researchers to seamlessly integrate subsequent modules (such as optical channels, OFDM modulators, localization algorithms, resource allocators, and AI scheduling agents).

## Architecture Overview

```
VLCL_AI/
├── environment/
│   ├── config.py             # Parses/Validates configs (YAML)
│   ├── coordinate_system.py  # Roll/Pitch/Yaw rotational and coordinate transformations
│   ├── room.py               # Establishes Room boundaries and surface reflectivities
│   ├── led.py                # Single LED and array emission configurations
│   ├── receiver.py           # APD / PD mobile terminal mechanics
│   ├── obstacle.py           # Geometric obstruction primitives (Box, Cylinder, Sphere)
│   ├── geometry.py           # Distances, angles, and Lambertian optical link-loss calculations
│   ├── mobility.py           # Kinetic trajectories (Static, Linear, Circular, Random Walk, Waypoint)
│   ├── state.py              # Immutable snapshot dataclass representing simulation state per frame
│   ├── scene.py              # Central manager containing room, LEDs, obstacles, receiver
│   ├── simulator.py          # Frame clock, simulation ticks, and event dispatcher
│   └── visualization.py      # Plotly-based headless 3D web rendering engine
├── configs/
│   └── default.yaml          # Laboratory configuration presets
├── logs/                     # Saved outputs, telemetry files, and 3D web visualizations
├── tests/                    # Core mathematical unit tests
├── examples/
│   └── demo_environment.py   # Complete laboratory simulation run loop
└── main.py                   # Simulator entry wrapper
```

## Mathematical Foundations

### 1. Lambertian Optical Channel Model
The Line-of-Sight (LOS) optical channel DC gain $H(0)$ between an LED transmitter and the APD receiver is modeled as:

$$H(0) = \begin{cases} \frac{(m+1) A_{rx}}{2\pi d^2} \cos^m(\phi) T_s(\psi) g(\psi) \cos(\psi), & 0 \le \psi \le \Psi_{fov} \\ 0, & \psi > \Psi_{fov} \end{cases}$$

Where:
* $m$ is the Lambertian order of emission, related to the LED semi-angle at half power $\theta_{1/2}$:  
  $m = -\frac{\ln(2)}{\ln(\cos(\theta_{1/2}))}$
* $A_{rx}$ is the active physical area of the APD sensor (`apd_size`).
* $d$ is the Euclidean distance between the LED and receiver.
* $\phi$ is the angle of irradiance at the transmitter.
* $\psi$ is the angle of incidence at the receiver.
* $T_s(\psi)$ is the gain of the optical filter (assumed as 1.0).
* $g(\psi)$ is the gain of the optical concentrator (`gain`).

### 2. Rotational Orientation Transformations
The receiver orientation vector $\mathbf{n}_{rx}$ is calculated dynamically from its default upward normal $\mathbf{n}_0 = [0, 0, 1]^T$ using extrinsic ZYX rotation angles (Roll $\phi_{rx}$, Pitch $\theta_{rx}$, Yaw $\psi_{rx}$):

$$\mathbf{R} = \mathbf{R}_z(\psi_{rx}) \mathbf{R}_y(\theta_{rx}) \mathbf{R}_x(\phi_{rx})$$
$$\mathbf{n}_{rx} = \mathbf{R} \mathbf{n}_0$$

## Usage Instructions

### Running the Environment Demo
Run the provided demo simulation script. This starts the physics clock, animates the receiver through a circular trajectory, evaluates line-of-sight blockages against 3D furniture and humans, and outputs high-fidelity JSON telemetry alongside a fully interactive **3D Plotly Web Digital Twin**:

```bash
python3 VLCL_AI/main.py
```

### Accessing the Interactive 3D Digital Twin
After running the simulation, open the generated HTML file in any browser to rotate, pan, and inspect the laboratory setup in interactive 3D:
```bash
open VLCL_AI/logs/simulation_3d.html
```

### Running Unit Tests
Validate math calculations, rotations, collisions, and distance geometries:
```bash
python3 -m unittest VLCL_AI/tests/test_simulation.py
```

## Future Module Compatibility (API Contract)

To hook up future OFDM communications, A-DPDOA localization, or AI scheduling engines, simple call loops can be implemented as follows without modifying the environment architecture:

```python
from VLCL_AI.environment.config import ConfigurationManager
from VLCL_AI.environment.room import Room
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.mobility import MobilityEngine
from VLCL_AI.environment.simulator import VLCLSimulator

# Load scene
cfg = ConfigurationManager("VLCL_AI/configs/default.yaml").get_config()
scene = Scene(Room(...), Receiver(...), [...])
simulator = VLCLSimulator(scene, MobilityEngine(...))

# Run-step loop
for step in range(1000):
    # 1. Step environment physics
    state = simulator.step()
    
    # 2. Extract immutable status snapshot
    rx_pos = state.receiver_position
    gains = state.dc_gains  # Model 2 can directly use these gains to compute SNR
    los_matrix = state.los_matrix
    
    # 3. Apply OFDM Communication or Localization algorithms here!
```
