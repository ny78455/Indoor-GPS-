# High-Fidelity 3D Digital Twin: Integrated Visible Light Communication & Localization (VLCL)

This repository houses a high-fidelity **3D Digital Twin and Physics Simulation Engine** developed to study and test **Integrated Visible Light Communication and Localization (VLCL)** inside indoor environments.

The project has been refactored into a decoupled **monorepo workspace** with isolated Frontend (React/Vite) and Backend (Express/Python) environments.

---

![alt text](image.png)

## 🛠️ System Architecture

The application separates UI representation, network capabilities, and raw physics simulations into modular layers:

```
                      +------------------------------------------+
                      |         React 19 SPA Frontend           |
                      |   (Vite, ThreeJS, Tailwind, Lucide)      |
                      +-------------------+----------------------+
                                          |
                                          | HTTP REST Checks
                                          | (Proxy: /api -> localhost:3001)
                                          v
                      +-------------------+----------------------+
                      |          Express Server backend          |
                      |        (Node TS, tsx, esbuild)           |
                      +-------------------+----------------------+
                                          |
                                          | Child Process (exec)
                                          | Python .venv Router
                                          v
                      +-------------------+----------------------+
                      |      VLCL Physics Simulator Engine       |
                      |  (NumPy, SciPy, Loguru, Rich, Plotly)    |
                      +------------------------------------------+
```

### 1. Frontend (`/frontend`)

* **Technologies**: React 19, Vite, TypeScript, Three.js, TailwindCSS.
* **Responsibility**: Presents the interactive 3D digital laboratory environment. It visualizes normal vectors, light emission cones, mobile receiver vectors, and ray-casted Line-Of-Sight (LOS) obstruction vectors. It synchronizes changes to simulation parameters and shows live simulation logs inside an in-browser retro-monospace console.
* **Vite Configurations**: Proxies `/api` network calls to the Node server (port 3000/3001) during standalone client hot-reloading workouts.

### 2. Backend Server (`/backend`)

* **Technologies**: Axios/Express, TypeScript, esbuild.
* **Responsibility**: Integrates client requests, hosts compiled static SPA files with Vite middleware, and handles core subprocess execution:
  * **YAML Config REST**: Reads/Writes default configuration presets from disk (`VLCL_AI/configs/default.yaml`).
  * **Subprocess Execution Router**: Executed from either root or backend folders, it automatically scans for isolated virtual Python environments (`backend/.venv/bin/python3`) and invokes the simulator engine safely.

### 3. Simulation AI Core (`/backend/VLCL_AI`)

* **Technologies**: Python 3, NumPy, SciPy, PyYAML.
* **Responsibility**: Calculates physical properties of the room and generates logs and 3D digital twin output assets.

---

## 🔬 Simulation AI Core Architecture

The Python AI core (`/backend/VLCL_AI`) is divided into two highly specialized modules. They work in tandem to create a true digital twin: a fast spatial awareness engine (Module 1), and a rigorous electromagnetic calculation engine (Module 2).

---

### Module 1: The Environment Simulation Engine
**Location**: `/backend/VLCL_AI/environment`

This engine acts as the "director" of the digital twin. It manages spatial awareness, configuration states, and bounding-box level interactions. It focuses on the macroscopic geometry of the room and the progression of time.

#### 1. Room Geometry and Spatial State
The indoor space is defined as a 3D bounding box ($W \times L \times H$). The Simulation Engine handles coordinate mapping and tracking all entities (LEDs, receivers, obstacles) within this grid. It uses simple analytic geometry to compute raw distances and directional vectors between any two points.

#### 2. Mobility and Trajectory Patterns
It controls the kinetic movement of the receiver. Based on predefined models (like `RandomWaypoint`, `Linear`, or `Static`), it calculates velocity, acceleration, and updates the receiver's $(x, y, z)$ position on every time step ($dt$).

#### 3. Bounding-Box Obstacle Intersections
Physical obstacles (like cylinders representing human researchers or rectangular partitions) are tracked by the simulation engine. It performs primary ray-tracing to test if a 3D line segment (from an LED to a receiver) intersects an obstacle's bounding shape. If intersected, the simulation engine flags a **Line-of-Sight (LOS) blockage** for that specific transmission path.

#### 4. Simulation Orchestrator
The `Simulator` class sits here. It manages the lifecycle loop: stepping through frames, updating mobility, gathering the macroscopic state of the `Scene`, and piping this data into either the frontend visualizer or down into the Physics Engine for deep analysis.

---

### Module 2: The High-Fidelity Physics Engine
**Location**: `/backend/VLCL_AI/physics`

While Module 1 handles *where* things are, Module 2 handles *how light behaves* between them. The Physics Engine executes advanced electromagnetic calculations to simulate optical wireless communication channels, acting as a rigorous digital twin of physical optoelectronics.

#### 1. Advanced Transmitter Modeling (Ceiling-Mounted LEDs)
Each LED transmitter acts as a lambertian emitter. The emission radiation profile is characterized by its **Lambertian Order** $m$, calculated from the semi-angle emission beam ($\theta_{1/2}$):

$$
m = \frac{-\ln(2)}{\ln(\cos(\theta_{1/2}))}
$$

The physics engine tracks subcarrier frequency modulation, DC bias, and projects optical radiation down with a specified optical power output ($P_{tx}$).

#### 2. Optoelectronic Receiver Node (Photodiode)
The mobile photodiode platform translates optical power into electrical signals. It evaluates:
* **Active Area ($A_{apd}$)**: Physical capture plane size in $m^2$.
* **Optical Concentrator**: Lenses that amplify incoming signal gain $g(\psi)$ based on the refractive index ($n$).
* **Optical Filter**: Transmission gain $T_s(\psi)$ for specific wavelengths.
* **Responsivity ($R$)**: The conversion efficiency (in A/W) of optical power to electrical current, resulting in a photodiode current: $I_{pd} = R \times P_{rx}$.

#### 3. Geometry and Line-Of-Sight Channel Loss
The Physics Engine calculates the **Lambertian Direct Current Optical Gain ($H(0)$)**:

$$
H(0) = \begin{cases} 
\frac{(m + 1) A_{apd}}{2\pi d^2} \cos^m(\phi) g(\psi) T_s(\psi) \cos(\psi) & \text{if } 0 \le \psi \le \text{FOV} \\ 
0 & \text{if } \psi > \text{FOV} 
\end{cases}
$$

Where:
* $d$: Euclidean distance.
* $\phi$: Angle of irradiance relative to the transmitter normal vector.
* $\psi$: Angle of incidence relative to the receiver normal vector.

#### 4. Multi-path Reflectivity and Raytracing (NLOS)
The physics engine features a dedicated raytracer that tracks Non-Line-Of-Sight (NLOS) reflections. Using surface reflection coefficients ($\rho_W, \rho_C, \rho_F$), it calculates multi-path propagation and impulse delay spread caused by light bouncing off walls and floors before reaching the receiver, maintaining signal integrity even when primary LOS is blocked.

#### 5. Noise Models & Signal-to-Noise Ratio (SNR)
It computes physical environmental noises acting upon the receiver hardware:
* **Thermal Noise ($\sigma^2_{thermal}$)**: Generated by the receiver's circuitry, dependent on temperature ($T_k$) and bandwidth ($B$).
* **Shot Noise ($\sigma^2_{shot}$)**: Generated by ambient background light ($P_{bg}$) and the signal itself.

The final electrical **Signal-to-Noise Ratio (SNR)** output is calculated in decibels (dB):

$$
\text{SNR}_{\text{dB}} = 10 \log_{10}\left( \frac{(R \cdot P_{rx})^2}{\sigma^2_{thermal} + \sigma^2_{shot}} \right)
$$

## ⚡ Execution and Interface Commands

The workspace provides workspace-wide scripts via `package.json` to handle installs and builds across both folders:

### 1. Installations

Install dependencies for both frontend and backend sub-packages in one command:

```bash
npm install
```

### 2. Running local Development Server

To launch the integrated server (Express serving hot-reloading client via middleware):

```bash
npm run dev
# Or run on an alternative port:
PORT=3001 npm run dev
```

### 3. Setup Virtual Environment (Recommended for Simulator Backend)

To isolate dependencies for the Python simulation engine:

```bash
# 1. Create venv inside public backend root
python3 -m venv backend/.venv

# 2. Install numpy, scipy, loguru, rich, plotly
backend/.venv/bin/pip install -r backend/VLCL_AI/requirements.txt
```

The server will automatically route simulation requests to the virtual environment once `.venv` is present on disk.

### 4. Build Targets

To generate optimized production bundles:

```bash
# Build React static files and Node server script
npm run build
```

* Frontend files are built into `frontend/dist/`.
* Backend is compiled into `backend/dist/server.cjs` by **esbuild**.

---

## 📁 Project Directory Structure

```text
.
├── .env.example
├── .gitignore
├── bun.lock
├── image.png
├── metadata.json
├── package-lock.json
├── package.json
├── README.md
├── backend/
│   ├── package.json
│   ├── server.ts
│   ├── tsconfig.json
│   └── VLCL_AI/
│       ├── main.py
│       ├── README.md
│       ├── requirements.txt
│       ├── configs/
│       │   └── default.yaml
│       ├── environment/
│       │   ├── config.py
│       │   ├── coordinate_system.py
│       │   ├── geometry.py
│       │   ├── led.py
│       │   ├── mobility.py
│       │   ├── obstacle.py
│       │   ├── receiver.py
│       │   ├── room.py
│       │   ├── scene.py
│       │   ├── simulator.py
│       │   ├── state.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── physics/
│       │   ├── attenuation.py
│       │   ├── channel_estimator.py
│       │   ├── concentrator.py
│       │   ├── constants.py
│       │   ├── lambertian.py
│       │   ├── multipath.py
│       │   ├── noise.py
│       │   ├── optical_channel.py
│       │   ├── optical_power.py
│       │   ├── photodiode.py
│       │   ├── physics_engine.py
│       │   ├── propagation.py
│       │   ├── raytracer.py
│       │   ├── receiver_model.py
│       │   ├── reflection.py
│       │   ├── signal.py
│       │   ├── snr.py
│       │   ├── transmitter.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── examples/
│       │   ├── demo_environment.py
│       │   └── __init__.py
│       ├── logs/
│       │   └── simulation_3d.html
│       └── tests/
│           ├── test_simulation.py
│           └── __init__.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── index.css
        ├── main.tsx
        ├── types.ts
        └── components/
            ├── CodeViewer.tsx
            ├── ControlPanel.tsx
            ├── DebugOverlay.tsx
            ├── FormulaPanel.tsx
            ├── IllustrationPanel.tsx
            └── ThreeCanvas.tsx
```

### Detailed File Descriptions

#### Root Directory
* `.env.example`: Environment variables template indicating required configurations.
* `.gitignore`: Specifies intentionally untracked files to ignore for Git version control.
* `bun.lock`: Dependency lock file for the Bun package manager.
* `image.png`: Preview image for the README.
* `metadata.json`: Project metadata and configuration details.
* `package-lock.json`: Dependency lock file for NPM.
* `package.json`: Main workspace package configuration containing scripts for both frontend and backend (`npm run dev`, `npm run build`, etc.).
* `README.md`: Comprehensive project documentation file (this file).

#### Backend (`/backend`)
* `package.json`: Node dependencies specific to the Express backend.
* `server.ts`: Express application handling HTTP routing, serving static files, and managing Python engine subprocesses.
* `tsconfig.json`: TypeScript configuration for the backend.
* `VLCL_AI/`: Core Simulation AI Engine written in Python.
  * `main.py`: Entry point for executing the simulation engine manually.
  * `README.md`: Documentation specific to the VLCL AI engine logic and execution.
  * `requirements.txt`: Python dependencies (NumPy, SciPy, Loguru, Rich, Plotly).
  * `configs/default.yaml`: Default configuration presets for the environment, LEDs, and receiver attributes.
  * `environment/`: Core simulation modules for the physics engine.
    * `config.py`: Loads and parses `default.yaml` into structured configurations with decimal notations.
    * `coordinate_system.py`: Manages the 3D coordinate logic and mapping.
    * `geometry.py`: Physics vector computations and Lambertian gain math.
    * `led.py`: Defines the LED transmitter behavior, power output, and Lambertian emission logic.
    * `mobility.py`: Handles mobility patterns and movement vectors for the receiver.
    * `obstacle.py`: Ray-tracing mathematical obstacle intersection logic for blocking Line-Of-Sight (LOS).
    * `receiver.py`: Noise computations, gain calculation, and Signal-to-Noise Ratio (SNR) evaluation.
    * `room.py`: Defines the physical dimensions and reflection properties of the simulated room.
    * `scene.py`: Manages the aggregate simulation scene, including walls, LEDs, obstacles, and receivers.
    * `simulator.py`: Coordinates the stepping and execution of the simulation timeline sequence.
    * `state.py`: Defines data structures to track the simulation state across time.
    * `visualization.py`: 3D plotting and output generation for assets (e.g., Plotly HTML).
    * `__init__.py`: Module initializer for the environment package.
  * `physics/`: Module 2: High-fidelity Physics Simulation Engine simulating optical/electromagnetic propagation.
    * `attenuation.py`: Calculates optical attenuation and propagation delays.
    * `channel_estimator.py`: Estimates overall channel quality and bandwidth constraints.
    * `concentrator.py`: Optical concentrator and lens gain calculations.
    * `constants.py`: Physical constants (Speed of light, Planck's constant, etc.).
    * `lambertian.py`: Advanced Lambertian radiation pattern modeling.
    * `multipath.py`: Multi-path propagation calculations and impulse responses.
    * `noise.py`: Thermal and shot noise evaluation based on temperature and ambient light.
    * `optical_channel.py`: Assembles DC gain matrices for LOS and NLOS paths.
    * `optical_power.py`: Receiver optical power calculations.
    * `photodiode.py`: Photodiode responsivity and electrical current conversion logic.
    * `physics_engine.py`: Central `PhysicsEngine` orchestrator wrapping all physics modules.
    * `propagation.py`: Base optical propagation utilities.
    * `raytracer.py`: Advanced ray-tracing engine to support multi-reflection bounces.
    * `receiver_model.py`: High-fidelity models combining photodiode arrays and optical filters.
    * `reflection.py`: Reflection coefficient tracking.
    * `signal.py`: Signal strength evaluation and electrical signal processing.
    * `snr.py`: Comprehensive Signal-to-Noise Ratio (SNR) and capacity calculations.
    * `transmitter.py`: Transmitter power array dynamics.
    * `visualization.py`: Python-side plotting tools specific to physics parameters.
    * `__init__.py`: Module initializer.
  * `examples/`: Example simulation scripts.
    * `demo_environment.py`: Executable Python entry script running the timeline loop for a sample space.
    * `__init__.py`: Module initializer.
  * `logs/`: Directory for output logs and generated artifacts.
    * `simulation_3d.html`: Pre-generated interactive 3D plot of the simulation environment.
  * `tests/`: Unit tests for the simulation engine.
    * `test_simulation.py`: Test suite validating simulation mechanics, ray-tracing, and mathematical calculations.
    * `__init__.py`: Module initializer.

#### Frontend (`/frontend`)
* `index.html`: Main HTML entry point for the Vite/React application.
* `package.json`: Node dependencies specific to the frontend application.
* `tsconfig.json`: TypeScript configuration for the frontend React app.
* `vite.config.ts`: Proxy settings (e.g., routing `/api` to backend) and Vite development configurations.
* `src/`: Source code for the React UI.
  * `App.tsx`: Main React application component handling state, layout, and top-level API event handlers.
  * `index.css`: Global stylesheet incorporating TailwindCSS utilities.
  * `main.tsx`: React DOM rendering entry point.
  * `types.ts`: TypeScript interface definitions corresponding to the frontend models and backend API structures.
  * `components/`: Reusable React components that make up the UI.
    * `CodeViewer.tsx`: Displays raw code or configuration files with syntax highlighting.
    * `ControlPanel.tsx`: UI panel for toggling simulation parameters, editing values, and triggering runs.
    * `DebugOverlay.tsx`: Displays real-time logs and debug information in a retro-monospace console.
    * `FormulaPanel.tsx`: Educational component presenting mathematical equations related to VLCL.
    * `IllustrationPanel.tsx`: Renders visual diagrams and graphical explanations for VLCL concepts.
    * `ThreeCanvas.tsx`: Contains the Three.js scene setup for the interactive 3D digital laboratory rendering.
