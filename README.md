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

The Python AI core (`/backend/VLCL_AI`) is divided into five highly specialized modules. They work in tandem to create a true digital twin: a fast spatial awareness engine (Module 1), a rigorous electromagnetic calculation engine (Module 2), an end-to-end communication DSP engine (Module 3), an advanced A-DPDOA localization engine (Module 4), and a unified Integrated Engine (Module 5).

---

### Module 1: The Environment Simulation Engine
**Location**: `/backend/VLCL_AI/environment`

This engine acts as the "director" of the digital twin. It owns **geometry and spatial state only** — no optical physics, no channel gains. The canonical data flow is:

```
EnvironmentSimulator.get_state()
        │
        ▼
EnvironmentState          ← geometry primitives only
  angles in RADIANS
  room_dims, led_orientations, led_beam_angles
        │
        ▼
PhysicsEngine.compute(env_state)    ← Module 2 owns all optics
```

#### 1. Room Geometry and Spatial State
The indoor space is defined as a 3D bounding box ($W \times L \times H$). All angular quantities are stored and passed in **radians** — the single canonical unit throughout internal computation. Conversion from configuration degrees to radians occurs exactly once at the environment boundary.

The `EnvironmentState` carries geometric primitives used by downstream modules:
- `incident_angles_rad` — receiver-side incidence angle $\psi$ [rad] per LED
- `irradiance_angles_rad` — transmitter-side irradiance angle $\phi$ [rad] per LED
- `room_dims` — $[W, L, H]$ in metres
- `led_orientations` — unit normal vectors $\hat{n}_{tx,i}$
- `led_beam_angles` — half-power beam angle $\theta_{1/2}$ in degrees (primitive, unconverted)

> **Architecture rule**: `EnvironmentState` does **not** contain `dc_gains` or `lambertian_order`. Those are computed exclusively in Module 2.

#### 2. LED Transmitter Primitive
The `LED` class stores only the **primitive** `beam_angle` (degrees). It does **not** compute the Lambertian order $m$ — that derivation is Module 2's responsibility.

#### 3. Mobility and Trajectory Patterns
Controls kinematic movement of the receiver. Based on predefined models (`RandomWaypoint`, `Linear`, or `Static`), it calculates velocity, acceleration, and updates the receiver's $(x, y, z)$ position on every time step ($dt$).

#### 4. Bounding-Box Obstacle Intersections
Physical obstacles (cylinders, rectangular partitions) are tracked. Ray-tracing tests if the line segment from an LED to a receiver intersects an obstacle bounding shape, flagging a **Line-of-Sight (LOS) blockage** for that path.

#### 5. Simulation Orchestrator
The `VLCLSimulator` class manages the lifecycle loop: stepping through frames, updating mobility, gathering the macroscopic geometric state, and passing it to Module 2 for physics computation.

---

### Module 2: The High-Fidelity Physics Engine
**Location**: `/backend/VLCL_AI/physics`

Module 2 consumes `EnvironmentState` (geometry-only) and performs all optoelectronic calculations. It is the **sole owner** of optical channel gains.

#### 1. Lambertian Order Derivation
The Lambertian emission order $m$ is derived **in this module** from the LED's primitive `beam_angle` supplied in `EnvironmentState`:

$$
m = \frac{-\ln(2)}{\ln(\cos(\theta_{1/2}))}
$$

Where $\theta_{1/2}$ is the semi-angle at half-power (degrees, converted to radians internally). This derivation never occurs in Module 1.

#### 2. Geometry and Line-Of-Sight Channel Gain $H(0)$
Using angles received in **radians** from `EnvironmentState`, Module 2 computes the **Lambertian DC Optical Gain**:

$$
H(0) = \begin{cases}
\dfrac{(m+1)\,A_{apd}}{2\pi d^2} \cos^m(\phi)\; g(\psi)\; T_s(\psi)\; \cos(\psi) & \text{if } 0 \le \psi \le \text{FOV} \\
0 & \text{if } \psi > \text{FOV}
\end{cases}
$$

Where:
- $d$: Euclidean distance [m]
- $\phi$: Irradiance angle from the LED normal (in **radians**, supplied by Module 1)
- $\psi$: Incidence angle at the receiver normal (in **radians**, supplied by Module 1)
- $A_{apd}$: Photodiode active area [m²]
- $T_s(\psi)$: Optical filter transmission gain

**Optical Concentrator Gain** (Snell's law, $\psi$ within FOV):
$$
g(\psi) = \frac{n^2}{\sin^2(\text{FOV})}
$$

Where $n$ is the refractive index of the concentrator lens.

> **Unit contract**: If the angles $\phi$ or $\psi$ are passed in degrees, `cos(15°) ≈ 0.966` is silently interpreted as `cos(15 rad) ≈ −0.76`, producing near-zero gain. Module 2 trusts that Module 1 has already converted to radians — enforced by regression test `T-M1-ANGLE-002`.

#### 3. Optoelectronic Receiver Node
- **Active Area ($A_{apd}$)**: Physical capture plane size in m²
- **Concentrator Gain $g(\psi)$**: Amplifies incoming signal based on refractive index $n$ and FOV
- **Responsivity ($R$)**: Conversion efficiency [A/W] → photodiode current $I_{pd} = R \times P_{rx}$

#### 4. Multi-path Reflectivity and NLOS Gain
A dedicated raytracer computes first-order NLOS reflection gain by discretising the 6 room surfaces. Each wall element $ds$ acts as a secondary Lambertian emitter ($m=1$). The `room_dims` are sourced from `EnvironmentState.room_dims` — not hardcoded.

#### 5. Noise Models & Signal-to-Noise Ratio
- **Thermal Noise** $\sigma^2_{th}$: From receiver circuitry, dependent on temperature $T_k$ and bandwidth $B$
- **Shot Noise** $\sigma^2_{sh}$: From ambient background light $P_{bg}$ and signal current

$$
\text{SNR}_{\text{dB}} = 10\log_{10}\!\left(\frac{(R \cdot P_{rx})^2}{\sigma^2_{th} + \sigma^2_{sh}}\right)
$$

---

### Module 3: The Communication Engine (DCO-OFDM)
**Location**: `/backend/VLCL_AI/communication`

Module 3 chains onto the Physics Engine. Once frequency-selective optical channel gains are computed, the Communication Engine runs end-to-end DSP to simulate data transmission via light.

#### 1. DCO-OFDM Modulation
VLC requires real, positive signals. The engine uses **DCO-OFDM**: maps bits to **square QAM** constellations (M ∈ {4, 16, 64}), forces Hermitian symmetry to ensure a real-valued IFFT output, and applies a DC bias before clipping.

> **Modulation constraint**: Only square M-QAM (M = 4, 16, 64) is supported. The analytical BER formula does **not** apply to non-square constellations (M = 8, 32). These are explicitly blocked with a `VLCLCommunicationError`.

#### 2. Communication SNR per Subcarrier (Paper Eq. 1)

$$
\gamma_{k,n}^{co} = \frac{\eta^2\,\mu^2 \left(\displaystyle\sum_{i=1}^{L} \sqrt{P_{n,i}}\; H_{i,n,k}\right)^2}{\sigma^2}
$$

Where:
- $P_{n,i}$: Electrical power allocated to subcarrier $n$ at LED $i$ [W]
- $\sqrt{P_{n,i}}$: Optical amplitude (electrical power → optical field → current)
- $H_{i,n,k}$: Optical channel gain from LED $i$ to user $k$ on subcarrier $n$
- $\mu$: Photodiode responsivity [A/W]
- $\sigma^2$: Total noise variance [A²]
- $\eta$: System scaling efficiency factor

> **Critical (M3-COM-002)**: The summation is $\sum \sqrt{P}\cdot H$, **not** $\sum P \cdot H$. The square-root reflects that electrical power converts to optical amplitude, not optical power, before the channel gain is applied.

#### 3. Analytical BER — Square M-QAM

$$
P_b \approx \frac{4}{\log_2 M}\left(1 - \frac{1}{\sqrt{M}}\right) \cdot \frac{1}{2}\operatorname{erfc}\!\left(\sqrt{\frac{3\,\gamma}{2(M-1)}}\right)
$$

For M = 2 (BPSK): $P_b = \frac{1}{2}\operatorname{erfc}(\sqrt{\gamma})$

The `strict=True` parameter on `BERCalculator.compute_empirical()` raises `VLCLCommunicationError` if the transmitted and received bit sequences have different lengths, catching framing/alignment errors early in validation pipelines.

#### 4. Digital Transceiver Chain
- **Transmitter**: QAM Modulation → IFFT → Cyclic Prefix Addition → DC Bias & Clipping
- **Channel**: LED first-order low-pass $H_{LED}(f) = \frac{1}{1 + j f/f_c}$ × optical gain $H(0)$; physical noise sampled with `noise_seed=None` (truly random per call)
- **Receiver**: ADC → Synchronisation → CP Removal → FFT → ZF/MMSE Equalisation → QAM Demodulation

#### 5. High-Level Telemetry KPIs
- **BER**: Empirical (bit comparison) and Analytical (erfc formula above)
- **EVM**: Distortion of received QAM symbols on the constellation
- **PAPR** and **Clipping Ratio**: LED dynamic range evaluation
- **Sum Rate & Spectral Efficiency**: Mbps and bps/Hz

---

### Module 4: The Localization Engine (A-DPDOA)
**Location**: `/backend/VLCL_AI/localization`

Module 4 operates in parallel with Module 3, consuming physical channel characteristics to estimate the mobile receiver's 3D coordinates.

#### 1. Asynchronous Differential Phase Difference of Arrival (A-DPDOA)
Unlike ToA (requires clock sync), A-DPDOA measures **phase differences** between pilot tones received from multiple LEDs. Five distinct frequencies $(f_1, \dots, f_5)$ are transmitted; their phase differences are converted to distance differences via:

$$
\Delta d_{ij} = \frac{c}{2\pi f_{ij}}\,\Delta\phi_{ij}
$$

#### 2. Linear System — Equation 16 (Paper)
The three dual-differential phase measurements form a linear system:

$$
\mathbf{A} \cdot \boldsymbol{\delta d} = \boldsymbol{\theta}_{measured}
$$

Where $\mathbf{A}$ is a $3 \times (N-1)$ coefficient matrix built from tone frequencies and LED assignments.

**Sign Convention (mandatory cross-file invariant)**:

| Location | Convention |
|---|---|
| `channel_interface.py` | `received_phase = −ω·τ` (standard physics: $s(t−\tau) \leftrightarrow e^{-j\omega\tau}$) |
| `position_solver.py` | `A_code = −A_{paper} \cdot \frac{2\pi}{c}` (explicit negation to compensate) |

> **Warning**: Do **not** change the sign in only one of these two files. The invariant is enforced by regression test `T-M4-004`.

#### 3. Signal Processing and Phase Unwrapping
- **Pilot Tone Extraction**: Complex IQ phase of specific pilot subcarriers
- **Phase Unwrapping**: Resolves $2\pi$ ambiguity using inter-frame temporal tracking. A jump of $>\pi$ rad between frames is corrected to the nearest equivalent in $(-\pi, +\pi]$. Verified to handle jumps $> 2\pi$ (test `T-M4-007`)
- **`rx_bandwidth`**: Configurable parameter on `LocalizationChannelInterface` (default 50 MHz)

#### 4. Position Solver (Trust-Region Least Squares)
Using distance differences (hyperbolic geometry), the engine minimises:

$$
\min_{\mathbf{p}} \sum_{(j,\text{ref})}\left(\|\mathbf{p} - \mathbf{p}_{j}\| - \|\mathbf{p} - \mathbf{p}_{\text{ref}}\| - \Delta d_{j,\text{ref}}\right)^2
$$

with soft-$\ell_1$ robust loss and box bounds $[0, W] \times [0, L] \times [0, H]$. Supports `2D_fixed_height` (solves $x, y$ with fixed $z$) and full `3D` modes.

> **Ground-truth firewall (M4-LOC-014)**: `PositionSolver` accepts only a plain `dict` of distance differences. It has zero imports from `environment.state` and cannot access the true `receiver_position`. Enforced by static source inspection test `T-M4-008`.

#### 5. Confidence and Quality Metrics
- **3D Positioning Error & RMSE**: Instantaneous and running root-mean-square errors
- **Confidence Score**: Based on solver residuals and geometric dilution of precision (GDOP)

---

### Module 5: Integrated Engine
**Location**: `/backend/VLCL_AI/integrated_vlcl`

Module 5 serves as the Master Coordinator. It integrates the communication and localization pipelines into a single step-by-step physical-layer execution.

#### 1. Spectrum Partitioner & Multi-LED Power Mapper
- Divides available OFDM subcarriers between communication groups and localization pilot tones.
- Assigns specific localization pilot frequencies to specific LEDs and dynamically allocates remaining power for communication streams.

#### 2. Composite Processing
- Merges the separate signal generation branches from Module 3 and Module 4.
- Runs the composite signals through clipping (DCO-OFDM DC Bias mapping) and the multi-path optical channel simultaneously.
- At the receiver side, it isolates the respective signals in the frequency domain, passing them to the dedicated DSPs for demodulation (Communication) and phase unwrapping (Localization).

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
├── IMPLEMENTATION_STATUS.md          ← live audit requirement register
├── MODULES_1_TO_4_REPAIR_REPORT.md   ← post-repair closure document
├── backend/
│   ├── package.json
│   ├── server.ts
│   ├── tsconfig.json
│   └── VLCL_AI/
│       ├── main.py
│       ├── README.md
│       ├── requirements.txt
│       ├── configs/
│       │   ├── default.yaml
│       │   └── paper_reference.yaml  ← Section IV simulation parameters (provenance-tagged)
│       ├── environment/
│       │   ├── config.py
│       │   ├── coordinate_system.py
│       │   ├── geometry.py           ← angles in radians; no dc_gains
│       │   ├── led.py                ← stores beam_angle only; no lambertian_order
│       │   ├── mobility.py
│       │   ├── obstacle.py
│       │   ├── receiver.py           ← geometry only; no physics methods
│       │   ├── room.py
│       │   ├── scene.py              ← FOV checked in radians; no H(0) step
│       │   ├── simulator.py          ← get_state() returns geometry only
│       │   ├── state.py              ← incident_angles_rad, irradiance_angles_rad;
│       │   │                            room_dims, led_orientations, led_beam_angles;
│       │   │                            no dc_gains field
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── physics/
│       │   ├── attenuation.py
│       │   ├── channel_estimator.py
│       │   ├── concentrator.py       ← g(ψ) = n²/sin²(FOV) — Snell's law
│       │   ├── constants.py          ← SPEED_OF_LIGHT canonical source
│       │   ├── lambertian.py         ← lambertian_order(beam_angle) derived here
│       │   ├── multipath.py
│       │   ├── noise.py
│       │   ├── optical_channel.py    ← H(0) with correct radians input
│       │   ├── optical_power.py
│       │   ├── photodiode.py
│       │   ├── physics_engine.py     ← consumes EnvironmentState primitives;
│       │   │                            derives m; sources room_dims from env_state
│       │   ├── propagation.py
│       │   ├── raytracer.py
│       │   ├── receiver_model.py
│       │   ├── reflection.py         ← NLOS: audited PASS
│       │   ├── signal.py
│       │   ├── snr.py
│       │   ├── transmitter.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── communication/
│       │   ├── adc.py
│       │   ├── ber.py                ← strict=True raises on length mismatch
│       │   ├── bit_generator.py
│       │   ├── channel_equalizer.py
│       │   ├── channel_interface.py  ← noise_seed=None (non-deterministic)
│       │   ├── config.py
│       │   ├── constellation.py
│       │   ├── dco_ofdm.py
│       │   ├── engine.py
│       │   ├── evm.py
│       │   ├── exceptions.py
│       │   ├── frame.py
│       │   ├── led_frequency_response.py  ← H(f)=1/(1+jf/fc): audited PASS
│       │   ├── metrics.py
│       │   ├── ofdm.py
│       │   ├── packet.py
│       │   ├── pre_equalizer.py
│       │   ├── qam.py                ← square QAM only: {4, 16, 64}
│       │   ├── rate.py
│       │   ├── receiver.py
│       │   ├── snr.py                ← Σ√P·H formula (M3-COM-002); eta_scaling param
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
│       │   ├── channel_interface.py  ← rx_bandwidth configurable; sign convention doc
│       │   ├── config.py
│       │   ├── engine.py             ← room_bounds from env_state.room_dims
│       │   ├── exceptions.py
│       │   ├── filters.py            ← Butterworth BPF: audited PASS
│       │   ├── frequency_plan.py
│       │   ├── metrics.py
│       │   ├── phase_estimator.py
│       │   ├── position_solver.py
│       │   ├── signal_generator.py
│       │   ├── state.py
│       │   ├── validation.py
│       │   ├── visualization.py
│       │   └── __init__.py
│       ├── integrated_vlcl/
│       │   ├── engine.py             ← Integrated Master Coordinator
│       │   ├── power_mapper.py       ← Distributes optical power between comms and loc
│       │   ├── receiver.py
│       │   ├── spectrum_partitioner.py
│       │   ├── state.py
│       │   ├── transmitter.py
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
  * `environment/`: Module 1: Environment Simulation Engine — geometry and spatial state only.
    * `config.py`: Loads and parses `default.yaml` into structured configurations.
    * `coordinate_system.py`: Manages the 3D coordinate logic and mapping.
    * `geometry.py`: `GeometryEngine.calculate_angles()` returns **radians**; no optical physics.
    * `led.py`: LED transmitter — stores `beam_angle` [degrees] only; **no** Lambertian order computation.
    * `mobility.py`: Mobility patterns and movement vectors for the receiver.
    * `obstacle.py`: Ray-tracing mathematical obstacle intersection logic for LOS blockage.
    * `receiver.py`: Photodiode geometry (position, normal, FOV); **no** physics methods.
    * `room.py`: Physical dimensions and reflection properties of the simulated room.
    * `scene.py`: Aggregate simulation scene; FOV check in radians; no H(0) step.
    * `simulator.py`: `get_state()` returns `EnvironmentState` (geometry only).
    * `state.py`: `EnvironmentState` — `incident_angles_rad`, `irradiance_angles_rad`, `room_dims`, `led_orientations`, `led_beam_angles`; **no** `dc_gains`.
    * `visualization.py`: 3D plotting and output generation.
    * `__init__.py`: Module initializer.
  * `physics/`: Module 2: High-fidelity Physics Simulation Engine simulating optical/electromagnetic propagation.
    * `attenuation.py`: Calculates optical attenuation and propagation delays.
    * `channel_estimator.py`: Estimates overall channel quality and bandwidth constraints.
    * `concentrator.py`: Optical concentrator gain $g(\psi) = n^2 / \sin^2(\text{FOV})$ (Snell's law).
    * `constants.py`: Physical constants — canonical `SPEED_OF_LIGHT` source (no literals elsewhere).
    * `lambertian.py`: `lambertian_order(beam_angle)` derivation — owned exclusively by Module 2.
    * `multipath.py`: Multi-path propagation calculations and impulse responses.
    * `noise.py`: Thermal and shot noise evaluation based on temperature and ambient light.
    * `optical_channel.py`: `compute_los_dc_gain()` — H(0) formula with correct radian angles.
    * `optical_power.py`: Receiver optical power calculations.
    * `photodiode.py`: Photodiode responsivity and electrical current conversion logic.
    * `physics_engine.py`: Central `PhysicsEngine` orchestrator; sources `beam_angle`, `led_normal`, `room_dims` from `EnvironmentState`.
    * `propagation.py`: Base optical propagation utilities.
    * `raytracer.py`: Advanced ray-tracing engine to support multi-reflection bounces.
    * `receiver_model.py`: High-fidelity models combining photodiode arrays and optical filters.
    * `reflection.py`: First-order NLOS Lambertian reflectance — audited PASS.
    * `signal.py`: Signal strength evaluation and electrical signal processing.
    * `snr.py`: Comprehensive Signal-to-Noise Ratio (SNR) and capacity calculations.
    * `transmitter.py`: Transmitter power array dynamics.
    * `visualization.py`: Python-side plotting tools specific to physics parameters.
    * `__init__.py`: Module initializer.
  * `communication/`: Module 3: End-to-end VLC Communication (DCO-OFDM) Engine.
    * `adc.py`: Analog-to-Digital converter quantization and clipping.
    * `ber.py`: BER calculations — empirical (with `strict=True` length enforcement) and analytical square M-QAM.
    * `bit_generator.py`: Generates pseudo-random payloads.
    * `channel_equalizer.py`: Zero-Forcing (ZF) and MMSE frequency-domain equalizers.
    * `channel_interface.py`: Physical channel propagation; `noise_seed=None` by default (truly random noise).
    * `config.py`: Module configurations (FFT size, sample rate, bandwidth, CP ratio).
    * `constellation.py`: Square QAM constellation generation and normalization ({4, 16, 64}).
    * `dco_ofdm.py`: DC biasing and signal clipping for unipolar LED driving.
    * `engine.py`: Central `CommunicationEngine` orchestrator.
    * `evm.py`: Error Vector Magnitude (EVM) calculation.
    * `exceptions.py`: Module-specific error definitions including `VLCLCommunicationError`.
    * `frame.py`: Dataclass representations of a single OFDM frame.
    * `led_frequency_response.py`: $H_{LED}(f) = 1/(1 + jf/f_c)$ — first-order LP; audited PASS.
    * `metrics.py`: Aggregates KPIs: sum rate, PAPR, clipping ratio, EVM.
    * `ofdm.py`: Core OFDM Modulator/Demodulator using FFT/IFFT and Cyclic Prefix.
    * `packet.py`: Higher-layer networking definitions.
    * `pre_equalizer.py`: Transmitter pre-equalization to flatten the channel response.
    * `qam.py`: QAM Modem with Gray coding; supports M ∈ {4, 16, 64} only.
    * `rate.py`: Shannon capacity bounds, effective throughput, and spectral efficiency.
    * `receiver.py`: Receive-side DSP (ADC → Sync → OFDM Demod → Equalizer → QAM Demap).
    * `snr.py`: **Communication SNR** — $\gamma = \eta^2 \mu^2 (\sum \sqrt{P}\cdot H)^2 / \sigma^2$ (Paper Eq. 1).
    * `state.py`: `CommunicationState` data structure returned every frame.
    * `subcarrier.py`, `subcarrier_grid.py`, `subcarrier_group.py`: Frequency spectrum allocation.
    * `synchronization.py`: Symbol timing synchronization.
    * `transmitter.py`: Transmit-side DSP (QAM Map → OFDM Mod → DCO Bias).
    * `visualization.py`: Constellation diagrams and spectrum plotters.
    * `__init__.py`: Module initializer.
  * `localization/`: Module 4: A-DPDOA Indoor Localization Engine.
    * `calibration.py`: Pre-computes initial phase offsets and calibration data.
    * `channel_interface.py`: Bridges physical multi-path channel with localization pilot tones; `rx_bandwidth` configurable; sign convention documented.
    * `config.py`: Module configurations (solver parameters, frequencies).
    * `engine.py`: Central `LocalizationEngine`; sources `room_bounds` from `env_state.room_dims`.
    * `exceptions.py`: Module-specific error definitions for localization failures.
    * `filters.py`: Butterworth BPF/LPF with zero-phase `sosfiltfilt` — audited PASS.
    * `frequency_plan.py`: Assigns distinct pilot frequencies $(f_1 \dots f_5)$ to LEDs.
    * `metrics.py`: Aggregates positioning errors, RMSE, and confidence scores.
    * `phase_estimator.py`: IQ extraction, `PhaseUnwrapper` (handles jumps $> 2\pi$).
    * `position_solver.py`: Trust-Region Least Squares; $\mathbf{A}_{code} = -\mathbf{A}_{paper}\cdot(2\pi/c)$; zero `EnvironmentState` imports (ground-truth firewall).
    * `signal_generator.py`: Generates transmitted pilot tones.
    * `state.py`: `LocalizationState` data structure returned every frame.
    * `validation.py`: Verifies geometry and LOS requirements for solving.
    * `visualization.py`: 2D/3D plots of hyperbolic intersections and position estimates.
    * `__init__.py`: Module initializer.
  * `examples/`: Example simulation scripts.
    * `demo_environment.py`: Executable Python entry script running the timeline loop for a sample space.
    * `__init__.py`: Module initializer.
  * `logs/`: Directory for output logs and generated artifacts.
    * `simulation_3d.html`: Pre-generated interactive 3D plot of the simulation environment.
  * `tests/`: Unit tests — **83 tests, 0 regressions**.
    * `test_ber.py`: BER empirical and analytical tests.
    * `test_communication_chain.py`: End-to-end loopback test.
    * `test_dco_ofdm.py`: DCO-OFDM biasing and PAPR tests.
    * `test_equalization.py`: ZF and MMSE equalizer tests.
    * `test_frequency_response.py`: LED low-pass cutoff test.
    * `test_localization_engine.py`: A-DPDOA phase and solver tests.
    * `test_module2_integration.py`: Module 2 receiver mobility integration.
    * `test_ofdm.py`: OFDM Hermitian symmetry and loopback.
    * `test_phase_b_c_audit.py`: **16 tests** — angular unit contract (T-M1-ANGLE), Module 1 ownership boundary, H(0) physics (T-M2-001), INT-001 integration.
    * `test_phase_g_h_i_audit.py`: **34 tests** — SNR sqrt fix (T-M3-COM-002), BER strict mode, sign convention invariant (T-M4-004), phase unwrapper (T-M4-007), ground-truth firewall (T-M4-008).
    * `test_physics.py`: Lambertian, LOS gain, noise, and SNR.
    * `test_qam.py`: QAM constellation, normalization, loopback.
    * `test_rate.py`: Rate calculator tests.
    * `test_simulation.py`: Simulation geometry, visibility, mobility.
    * `test_subcarriers.py`: Subcarrier grid initialisation.
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
    * `IntegratedPanel.tsx`: Telemetry dashboard for the Integrated Module 5 Engine (combined Comms & Loc metrics).
    * `LocalizationPanel.tsx`: Telemetry dashboard for the A-DPDOA localization engine (estimated position, RMSE).
    * `ThreeCanvas.tsx`: Contains the Three.js scene setup for the interactive 3D digital laboratory rendering.
