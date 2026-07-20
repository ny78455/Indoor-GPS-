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

The Python AI core (`/backend/VLCL_AI`) is divided into four highly specialized modules. They work in tandem to create a true digital twin: a fast spatial awareness engine (Module 1), a rigorous electromagnetic calculation engine (Module 2), an end-to-end communication DSP engine (Module 3), and an advanced A-DPDOA localization engine (Module 4).

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

---

### Module 3: The Communication Engine (DCO-OFDM)
**Location**: `/backend/VLCL_AI/communication`

Module 3 chains directly onto the Physics Engine. Once the frequency-selective optical channel gain is calculated, the Communication Engine simulates the end-to-end digital signal processing (DSP) required to transmit data via light.

#### 1. DCO-OFDM Modulation
Visible light requires real and positive signals. The engine employs **Direct Current Biased Optical Orthogonal Frequency Division Multiplexing (DCO-OFDM)**. It maps random bits to QAM constellations, forces Hermitian symmetry on the subcarrier grid to ensure a real-valued time-domain signal, and applies a DC bias to keep the waveform strictly positive before clipping.

#### 2. Digital Transceiver Chain
* **Transmitter**: QAM Modulation → IFFT → Cyclic Prefix Addition → DC Bias & Clipping.
* **Channel Interface**: The resulting electrical waveform is passed through the LED's low-pass frequency response model and convolved with the optical multi-path impulse response from Module 2.
* **Receiver**: ADC Quantization → Synchronization → Cyclic Prefix Removal → FFT → Frequency Domain Equalization (Zero-Forcing or MMSE) → QAM Demodulation.

#### 3. High-Level Telemetry KPIs
The engine outputs live, real-world communication metrics:
* **Bit Error Rate (BER)**: Empirical (simulated bit errors) vs Analytical (Shannon bound).
* **Error Vector Magnitude (EVM)**: Measures the distortion of received QAM symbols on the constellation map.
* **Peak-to-Average Power Ratio (PAPR)** and **Clipping Ratio**: Evaluates signal distortion caused by the limited dynamic range of the LEDs.
* **Sum Rate & Spectral Efficiency**: Raw data rates in Mbps and bandwidth efficiency in bps/Hz.

---

### Module 4: The Localization Engine (A-DPDOA)
**Location**: `/backend/VLCL_AI/localization`

Module 4 operates in parallel with Module 3, consuming the physical channel characteristics to estimate the mobile receiver's 3D coordinates.

#### 1. Asynchronous Differential Phase Difference of Arrival (A-DPDOA)
Unlike standard Time of Arrival (ToA) which requires strict transmitter-receiver clock synchronization, A-DPDOA relies on phase differences between received pilot tones from multiple LEDs. By transmitting distinct frequencies ($f_1, f_2, \dots$) from each LED, the receiver measures the phase of each tone. The phase differences between pairs of LEDs are then converted into distance differences.

#### 2. Signal Processing and Phase Unwrapping
The engine implements advanced DSP for localization:
* **Pilot Tone Extraction**: Extracts the complex IQ phase components of specific pilot subcarriers used for localization.
* **Phase Unwrapping**: Resolves the $2\pi$ phase ambiguity inherent in periodic signals to compute the true flight-time phase delay.
* **Distance Difference Calculation**: Converts the unwrapped phase difference between two LEDs into a physical distance difference $\Delta d_{ij} = \frac{c}{2\pi f_{ij}} \Delta \phi_{ij}$.

#### 3. Position Solver (Gauss-Newton Optimization)
Using the distance differences (a hyperbolic geometry problem), the engine employs a non-linear Least Squares optimization algorithm (Gauss-Newton or Levenberg-Marquardt). It iteratively refines an initial guess $(X_0, Y_0, Z_0)$ to find the optimal 3D coordinates $(X, Y, Z)$ that minimize the residual error of the hyperbolic equations.

#### 4. Confidence and Quality Metrics
The engine provides comprehensive telemetry on the localization quality:
* **3D Positioning Error & RMSE**: Calculates instantaneous and running root-mean-square errors against the true position.
* **Confidence Score**: Evaluates the geometric dilution of precision (GDOP) and solver residuals to assign a 0-100% confidence level.

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
│       ├── communication/
│       │   ├── adc.py
│       │   ├── ber.py
│       │   ├── bit_generator.py
│       │   ├── channel_equalizer.py
│       │   ├── channel_interface.py
│       │   ├── config.py
│       │   ├── constellation.py
│       │   ├── dco_ofdm.py
│       │   ├── engine.py
│       │   ├── evm.py
│       │   ├── exceptions.py
│       │   ├── frame.py
│       │   ├── led_frequency_response.py
│       │   ├── metrics.py
│       │   ├── ofdm.py
│       │   ├── packet.py
│       │   ├── pre_equalizer.py
│       │   ├── qam.py
│       │   ├── rate.py
│       │   ├── receiver.py
│       │   ├── snr.py
│       │   ├── state.py
│       │   ├── subcarrier.py
│       │   ├── subcarrier_grid.py
│       │   ├── subcarrier_group.py
│       │   ├── synchronization.py
│       │   ├── transmitter.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── localization/
│       │   ├── calibration.py
│       │   ├── channel_interface.py
│       │   ├── config.py
│       │   ├── engine.py
│       │   ├── exceptions.py
│       │   ├── filters.py
│       │   ├── frequency_plan.py
│       │   ├── metrics.py
│       │   ├── phase_estimator.py
│       │   ├── position_solver.py
│       │   ├── signal_generator.py
│       │   ├── state.py
│       │   ├── validation.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── examples/
│       │   ├── demo_environment.py
│       │   └── __init__.py
│       ├── logs/
│       │   └── simulation_3d.html
│       └── tests/
│           ├── test_localization_engine.py
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
            ├── CommunicationPanel.tsx
            ├── ControlPanel.tsx
            ├── DebugOverlay.tsx
            ├── FormulaPanel.tsx
            ├── IllustrationPanel.tsx
            ├── LocalizationPanel.tsx
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
  * `communication/`: Module 3: End-to-end VLC Communication (DCO-OFDM) Engine.
    * `adc.py`: Analog-to-Digital converter quantization and clipping.
    * `ber.py`: Bit Error Rate calculations (empirical vs theoretical).
    * `bit_generator.py`: Generates pseudo-random payloads.
    * `channel_equalizer.py`: Zero-Forcing (ZF) and Minimum Mean Square Error (MMSE) frequency domain equalizers.
    * `channel_interface.py`: Bridges the digital signal and the analog physics propagation model.
    * `config.py`: Module configurations (FFT size, sample rate, bandwidth, CP ratio).
    * `constellation.py`: QAM constellation generation and normalization.
    * `dco_ofdm.py`: Handles DC biasing and signal clipping for unipolar LED driving.
    * `engine.py`: Central `CommunicationEngine` orchestrator that chains all components.
    * `evm.py`: Error Vector Magnitude (EVM) calculation logic.
    * `exceptions.py`: Module-specific error definitions.
    * `frame.py`: Dataclass representations of a single OFDM frame.
    * `led_frequency_response.py`: First-order low-pass filter modeling of the LED frequency bandwidth limitations.
    * `metrics.py`: Aggregates the high-level KPIs like sum rate, PAPR, clipping ratio, and EVM.
    * `ofdm.py`: Core OFDM Modulator and Demodulator using FFT/IFFT and Cyclic Prefix.
    * `packet.py`: Higher-layer networking definitions.
    * `pre_equalizer.py`: Transmitter pre-equalization to flatten the channel response beforehand.
    * `qam.py`: High-level QAM Modem handling Gray coding mapping and demapping.
    * `rate.py`: Calculates Shannon capacity bounds, effective throughput, and spectral efficiency.
    * `receiver.py`: Wraps all receive-side DSP (ADC → Sync → OFDM Demod → Equalizer → QAM Demap).
    * `snr.py`: Communication-specific electrical SNR logic.
    * `state.py`: Defines the `CommunicationState` data structure returned every frame.
    * `subcarrier.py`, `subcarrier_grid.py`, `subcarrier_group.py`: Manages the frequency spectrum allocation (Data vs Pilot vs Null).
    * `synchronization.py`: Simulates symbol timing synchronization.
    * `transmitter.py`: Wraps all transmit-side DSP (QAM Map → OFDM Mod → DCO Bias).
    * `visualization.py`: Constellation diagrams and spectrum plotters.
    * `__init__.py`: Module initializer.
  * `localization/`: Module 4: A-DPDOA Indoor Localization Engine.
    * `calibration.py`: Pre-computes initial phase offsets and calibration data.
    * `channel_interface.py`: Bridges the physical multi-path channel with localization pilot tones.
    * `config.py`: Module configurations (solver parameters, frequencies).
    * `engine.py`: Central `LocalizationEngine` orchestrator chaining phase estimation and position solving.
    * `exceptions.py`: Module-specific error definitions for localization failures.
    * `filters.py`: Signal filtering for precise phase extraction.
    * `frequency_plan.py`: Assigns distinct pilot frequencies to different LEDs.
    * `metrics.py`: Aggregates positioning errors, RMSE, and confidence scores.
    * `phase_estimator.py`: Extracts and unwraps phase data from IQ signals.
    * `position_solver.py`: Non-linear Least Squares (Gauss-Newton) optimization for hyperbolic positioning.
    * `signal_generator.py`: Generates the transmitted pilot tones.
    * `state.py`: Defines the `LocalizationState` data structure returned every frame.
    * `validation.py`: Verifies geometry and line-of-sight requirements for solving.
    * `visualization.py`: 2D/3D plots of hyperbolic intersections and position estimates.
    * `__init__.py`: Module initializer.
  * `examples/`: Example simulation scripts.
    * `demo_environment.py`: Executable Python entry script running the timeline loop for a sample space.
    * `__init__.py`: Module initializer.
  * `logs/`: Directory for output logs and generated artifacts.
    * `simulation_3d.html`: Pre-generated interactive 3D plot of the simulation environment.
  * `tests/`: Unit tests for the simulation engine.
    * `test_localization_engine.py`: Unit tests specifically for the A-DPDOA localization mechanics.
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
    * `CommunicationPanel.tsx`: Telemetry dashboard for OFDM communication KPIs (BER, EVM, SNR).
    * `ControlPanel.tsx`: UI panel for toggling simulation parameters, editing values, and triggering runs.
    * `DebugOverlay.tsx`: Displays real-time logs and debug information in a retro-monospace console.
    * `FormulaPanel.tsx`: Educational component presenting mathematical equations related to VLCL.
    * `IllustrationPanel.tsx`: Renders visual diagrams and graphical explanations for VLCL concepts.
    * `LocalizationPanel.tsx`: Telemetry dashboard for the A-DPDOA localization engine (estimated position, RMSE).
    * `ThreeCanvas.tsx`: Contains the Three.js scene setup for the interactive 3D digital laboratory rendering.
