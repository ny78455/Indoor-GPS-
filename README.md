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

## 🔬 Mathematical & Simulation Model

The python engine (`VLCL_AI`) executes mathematical calculations to simulate optical wireless communication paths:

### 1. Room Geometry and Reflectivity

The indoor space is defined as a bounding box ($W \times L \times H$). Walls, ceilings, and floors are defined with specific reflection surface coefficients ($\rho_W, \rho_C, \rho_F$). These values determine multi-path reflections (Non-Line-Of-Sight path logs).

### 2. Transmitter (ceiling-mounted LEDs)

Each LED transmitter acts as a lambertian emitter. The emission radiation profile is characterized by its **Lambertian Order** $m$, calculated from the semi-angle emission beam ($\theta_{1/2}$):

$$
m = \frac{-\ln(2)}{\ln(\cos(\theta_{1/2}))}
$$

The LED projects optical radiation down with power output ($P_{tx}$), subcarrier frequency modulation, and DC bias values.

### 3. Optoelectronic Receiver Node

The mobile photodiode platform features:

* **Active Area ($A_{apd}$)**: Physical capture plane size in $m^2$.
* **Semi-angle Field of View ($\text{FOV}$)**: Evaluates reception capability. If the incident angle of incoming light beams exceeds the FOV boundary, signal reception drops to $0.0$.
* **Optical Path Gain**: Incorporates ambient noise levels ($W/\text{Hz}$) to measure Signal-to-Noise Ratio (SNR) in decibels:

$$
\text{SNR}_{\text{dB}} = 10 \log_{10}\left( \frac{\text{Signal Power}^2}{\text{Noise Power}} \right)
$$

### 4. Geometry and Line-Of-Sight Channel Loss

The simulator calculates the **Lambertian Direct Current Optical Gain ($H(0)$)**:

$$
H(0) = \begin{cases} 
\frac{(m + 1) A_{apd}}{2\pi d^2} \cos^m(\phi) g(\psi) \cos(\psi) & \text{if } 0 \le \psi \le \text{FOV} \\ 
0 & \text{if } \psi > \text{FOV} 
\end{cases}
$$

Where:

* $d$: Euclidean distance between Transmitter (Tx) and Receiver (Rx).
* $\phi$: Angle of irradiance relative to the transmitter normal vector.
* $\psi$: Angle of incidence relative to the receiver normal vector.
* $g(\psi)$: Optical concentrator gain.

### 5. Obstacles & Ray Tracing Blockage

Physical obstacles (like cylinders representing researchers or partitions) are registered inside the environment. The engine uses 3D analytical geometry to test line segments for intersections. If a ray intersects an obstacle, it logs a **Line-of-Sight (LOS) blockage** for that specific light path, automatically dropping $H(0)$ to zero and calculating NLOS reflections if enabled.

---

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
