# MODULES 1–4 AUDIT AND REPAIR SPECIFICATION
### Integrated VLCL Digital Twin — Forensic Audit vs. Yang et al., "An Advanced Integrated Visible Light Communication and Localization System," IEEE Trans. Commun., vol. 71, no. 12, Dec. 2023.

Repository audited: `https://github.com/ny78455/Indoor-GPS-` (cloned and inspected directly; findings below are grounded in the actual source, not the README).

---

## 1. EXECUTIVE SUMMARY

This audit inspected the actual source code of Modules 1–4 (`backend/VLCL_AI/{environment,physics,communication,localization}`) against the reference paper's equations (1)–(18) and against internal consistency (README vs. code vs. tests).

**Headline result: one CRITICAL (P0), system-wide, verified bug was found that invalidates almost every physically-computed number in the simulator (channel gain, received power, SNR, BER, localization accuracy):**

> **M2-PHY-001 — Degrees passed as radians into `compute_los_dc_gain`.** `physics_engine.py` forwards `env_state.irradiance_angles` / `env_state.incident_angles` — which are produced in **degrees** by `environment/geometry.py::calculate_angles()` — directly into `optical_channel.py::compute_los_dc_gain(irradiance_angle_rad=..., incident_angle_rad=...)`, which expects **radians**. Because the FOV check (`incident_angle_rad > fov_rad`) compares a degree-valued number against a small radian threshold (~1.2 rad for 70°), nearly every legitimately visible LED is incorrectly treated as **outside the receiver's FOV** and gets `H(0)=0`. When an angle does slip through, `cos()` is evaluated on the wrong argument, so `cos(20°)` is computed as `cos(20 rad)` instead of `cos(0.349 rad)`. This corrupts LOS channel gain, received power, photocurrent, SNR, BER, localization SNR and, downstream, localization accuracy — for every frame, every LED, in every code path that uses `PhysicsEngine`.

In addition, two further **CONFIRMED, high-severity architecture bugs** were found in Module 1:

- **M1-ENV-001 — Dead code after `return` in `VLCLSimulator.get_state()`.** `self.physics.compute(state)` and the second `return` are unreachable, so any caller of `get_state()` (a snapshot without advancing the clock) receives a state whose `.physics` field is never populated.
- **M1-ENV-002 — Duplicated, non-canonical H(0) formula in Module 1.** `environment/geometry.py::calculate_lambertian_dc_gain()` independently re-implements the Lambertian LOS channel gain (Module 2's job) using the receiver's raw `.gain` attribute in place of the concentrator-gain formula `g(ψ) = n²/sin²(Ψc)`, and this duplicate is what actually populates `EnvironmentState.dc_gains` (via `Scene.get_geometric_metrics()` → `VLCLSimulator.step()/get_state()`). Meanwhile the canonical, correct implementation lives in `physics/optical_channel.py::compute_los_dc_gain()` and populates the separate `PhysicsState.los_gains` field. **The same simulation frame therefore carries two different, disagreeing H(0)-like values under two different field names** (`state.dc_gains` vs `state.physics["los_gains"]`), with no single source of truth.

On the positive side, several equation-critical paths were verified **algebraically, line-by-line, against the paper** and found to be **correct**:

- Communication BER (paper Eq. 2) — coefficient and erfc argument match exactly after simplification.
- Data-rate raw PHY rate (paper Eq. 3) — `Σ B_n log2(M_n)` matches exactly.
- OFDM Hermitian symmetry, DC/Nyquist nulling, and `n ∈ (0, N/2)` subcarrier indexing — correct and paper-consistent.
- QAM Gray coding and unit-energy normalization — correct.
- Photodiode `I = R·P·M` — correct.
- **Ground-truth firewall in Module 4 — verified clean.** `localization/engine.py` reads `environment_state.receiver_position` exactly once per frame, stores it only as `true_position_for_evaluation_only`, and never passes it into `DistanceDifferenceSolver` or `PositionSolver`. This is the single most safety-critical check in the whole audit (Part 43) and it **passes**.
- The A-DPDOA differential/dual-differential/I-Q/atan2 chain in `phase_estimator.py` and the Eq. (16) matrix in `position_solver.py` were **re-derived from scratch algebraically** (not copied from the paper OCR) and found to be **internally self-consistent**: the code uses a physically-standard `s(t−τ) ⇒ e^{-jωτ}` delay convention (the paper's Eq. (5)/(6) instead literally add `+ωτ`), and the Eq. (16) coefficient matrix carries an explicit compensating minus sign (`self.A = -self.A * (2π/c)`) that exactly cancels this convention difference. The net effect is mathematically correct, but it is a **documented deviation from the paper's literal sign convention** and must be protected by a regression test (see `T-M4-003`) so a future "fix to match the paper" does not silently break it.

Everything else is catalogued below with severity, evidence, and required fix. Given the scope of this audit (ordered by the task itself as ~90 parts across 4 modules plus cross-cutting concerns), **not every equation and file received the same depth of manual re-derivation**. Sections explicitly marked `VALIDATION GAP` were inspected structurally but not algebraically re-derived, and must receive that treatment before Module 5 begins (see Section 32).

---

## 2. SCOPE

In scope: `backend/VLCL_AI/{environment,physics,communication,localization,configs,tests,examples}`, `backend/VLCL_AI/main.py`, and the parts of `backend/server.ts` that wire these modules to the API (used only to determine *which* code paths are actually reachable/live vs. dead).

Out of scope (per task instructions): Module 5+ (integrated spectrum, adaptive controller), any AI/ML additions, frontend visual polish, and code modification (this is a specification, not a patch).

---

## 3. REFERENCE PAPER ARCHITECTURE

```
LED array (4 LEDs, ceiling-mounted, downward-pointing)
        │  DCO-OFDM communication subcarriers (N−L−1 of N)
        │  A-DPDOA localization tones f1..f5 (L+1 = 5 subcarriers, in "frequency holes")
        ▼
Indoor optical wireless channel (LOS Lambertian, δ² background noise)
        │
        ├── VLC receiver chain: PD → BSF → OFDM demod → QAM demod → bits
        │      SNR: γ_k,n^co = μ²(Σ_i √P_{n,i} H_{i,n,k})² / δ²         (Eq. 1)
        │      BER: (√M−1)/(√M log2√M) · erfc(√(3γ/(2(M−1))))            (Eq. 2)
        │      Rate: R_k = B_sub Σ_{n=1}^{N/2−1} ρ_{k,n} log2 M_n         (Eq. 3)
        │
        └── VLL receiver chain: PD → BPF(f1..f5) → non-LO differential
               phase-shift measurement → A-DPDOA trilateration
               S_i^Tx(t) = √P_i sin(2πf_i t + φ0)                        (Eq. 4)
               S_{i,k}^Rx(t) = √P_i H_{i,k} sin(ω_i t + ω_i t_{i,k} + φ0) (Eq. 5/6)
               → pairwise multiply → BPF → D_i(t)                        (Eq. 7–9)
               → dual differential → I/Q via LPF + Hilbert → atan2       (Eq. 10–15)
               → 3×3 linear system (AP frequency constraint) → Δd        (Eq. 16)
               → nonlinear trilateration → (x,y,z)
               → shifting-error mitigation (ITD/hardware bias calibration)
```

Physical topology detail load-bearing for Module 4 (easy to miss from the equations alone): **LED lamp 1 carries both f1 and f5** (Section II-A of the paper). This means `t_{5,k} = t_{1,k}` physically (same propagation path), which is why paper Eq. (15) uses `ω5·t1` (not `t5`). This is verified correctly implemented in the repo (see §10.2).

---

## 4. CURRENT REPOSITORY ARCHITECTURE (AS BUILT)

```
environment/                          physics/
  room.py            (Room dims)        lambertian.py        (m, radiation pattern)
  led.py             (LED, LEDArray)     concentrator.py      (g(ψ))
  receiver.py         *duplicated*       optical_channel.py   (H(0), CANONICAL)
  obstacle.py        (AABB/cylinder)     reflection.py        (NLOS)
  geometry.py         *duplicated H(0)*  photodiode.py        (I=RP·M)
  mobility.py        (Static/Linear/     noise.py             (shot/thermal/bg/elec)
                       RandomWaypoint...) snr.py               (electrical/optical SNR)
  scene.py           (owns Scene,        physics_engine.py    (PhysicsEngine.compute(),
                       calls duplicated                          CANONICAL orchestrator)
                       H(0))             channel_estimator.py, raytracer.py
  simulator.py        (VLCLSimulator,
                       EnvironmentState
                       producer; ALSO
                       calls PhysicsEngine)
  state.py            (EnvironmentState: dc_gains ⟵ Module-1 calc,
                                          physics ⟵ Module-2 calc — TWO SOURCES)

communication/                         localization/
  qam.py, ofdm.py, dco_ofdm.py           signal_generator.py   (Eq. 4, TX tones)
  ber.py (Eq. 2, CORRECT)                channel_interface.py (Eq. 5/6, apply H,τ,noise)
  rate.py (Eq. 3, CORRECT)               phase_estimator.py    (Eq. 7–15, re-derived OK)
  snr.py (Eq. 1, BUG: missing √)         position_solver.py    (Eq. 16, sign-compensated OK)
  channel_interface.py, pre_equalizer.py calibration.py        (shifting-error mitigation)
  (Eq. 18 primitive, correctly disabled  engine.py             (orchestrator; GT firewall OK)
   by default)                           validation.py, metrics.py, filters.py
```

`main.py` only launches `examples/demo_environment.py`; the real integration point is `backend/server.ts`, which instantiates `PhysicsEngine` directly (never `Scene.get_geometric_metrics()`), confirming that Module 1's duplicated H(0) path (`environment/geometry.py`) is *reachable* (via `VLCLSimulator`, used in `examples/demo_receiver_mobility.py` and `tests/test_simulation.py`) but *not currently exercised* by the live backend API. It is nonetheless a live landmine for anyone using `VLCLSimulator` directly (which is the documented, "intended" Module‑1 entry point per the README) or for Module 5 when it is built on top of `EnvironmentState.dc_gains` instead of `PhysicsState.los_gains`.

---

## 5. TARGET ARCHITECTURE FOR MODULES 1–4

```
EnvironmentState  (Module 1: pure geometry — positions, orientations, angles [deg],
                    distances, LOS boolean, room dims. NO physical gain/power/SNR
                    fields. dc_gains field REMOVED.)
        ↓
PhysicsEngine.compute(EnvironmentState) → PhysicsState   (Module 2: sole owner of
                    H(0), NLOS, delay, noise, SNR, received power, photocurrent)
        ├──────────────────────────────┐
        ▼                              ▼
CommunicationEngine                LocalizationEngine
  (Module 3: consumes                (Module 4: consumes PhysicsState.los_gains/
   PhysicsState.channel gains         total_gains/propagation_times ONLY; NEVER
   per-subcarrier via H_LED(f);       reads EnvironmentState.receiver_position
   owns Eq 1/2/3/18)                  except into true_position_for_evaluation_only)
```

Key correction versus current architecture: **Module 1 must not compute or store any channel-gain-like quantity.** `EnvironmentState.dc_gains` is removed; the only physically-meaningful gain lives in `PhysicsState`.

---

## 6. PAPER ASSUMPTIONS VS. SIMULATOR EXTENSIONS

| Item | Classification | Notes |
|---|---|---|
| LOS Lambertian H(0), Eq. (1)–(6) core forms | [PAPER-REQUIRED] | Must match exactly |
| BER Eq. (2), Rate Eq. (3) | [PAPER-REQUIRED] | Verified correct |
| A-DPDOA Eq. (4)–(16) | [PAPER-REQUIRED] | Verified (with documented sign-convention translation) |
| Shot/thermal/background/electronic noise breakdown | [PHYSICS-EXTENSION] | Paper only mentions δ² generically; code's 4-term breakdown is a reasonable, standard extension |
| NLOS multipath / ray tracing | [PHYSICS-EXTENSION] | Paper does not model this explicitly in the main equations |
| DC-bias = k·σ heuristic, clipping | [PHYSICS-EXTENSION] | Paper does not give a bias-selection formula |
| `phase_equivalent` (complex baseband) localization signal mode | [PHYSICS-EXTENSION] | Reasonable answer to PART 45 (Nyquist feasibility at 4–4.8 MHz); paper's own hardware is analog/real-waveform |
| 256-QAM support | [OPTIONAL] | Not in paper's M-set {2,4,8,16,32,64} |
| Joint adaptive modulation/subcarrier/power loop (Eq. 17), full pre-equalization | Explicitly **not implemented** (by design, per PART 88) | Only primitives exist (`pre_equalizer.py`, disabled by default) — correct scoping |

---

## 7. MODULE 1 AUDIT — Environment Simulation Engine

### 7.1 Architecture
`Room`, `LED`/`LEDArray`, `Receiver`, `Obstacle`, `GeometryEngine` (stateless static methods), `MobilityEngine`, `Scene` (composition root), `VLCLSimulator` (clock + event dispatch + `EnvironmentState` producer), `EnvironmentState` (frozen dataclass).

### 7.2 Geometry
`environment/geometry.py::GeometryEngine` is a clean, stateless utility class. `distance()` is correct Euclidean distance. `calculate_angles()` correctly computes φ (irradiance) via `arccos(v̂_tr · n̂_tx)` and ψ (incidence) via `arccos(-v̂_tr · n̂_rx)`, **returned in degrees**. This is fine internally, but **the degrees convention is not respected by downstream consumers** — see M2-PHY-001.

`is_visible_los()` performs a segment-vs-ray-vs-obstacle test with a `(0.01, ray_dist - 0.01)` open interval — reasonable floating-point tolerance handling for touching boundaries (Part 11). `check_room_boundaries_collision()` clamps to `[margin, bound-margin]` per axis — correct, deterministic.

**`calculate_lambertian_dc_gain()` (lines 78–106) should not exist in Module 1 at all** — see M1-ENV-002 below.

### 7.3 Coordinate System
`environment/coordinate_system.py`: origin = floor corner (0,0,0), Z = vertical height (matches paper's ceiling-mounted LED convention, `orientation=[0,0,-1]` for ceiling LEDs in `configs/default.yaml`), floor = z=0. Rotation matrices use standard R = Rz(yaw)·Ry(pitch)·Rx(roll) with degrees-in/radians-internally, consistently applied to both LED and Receiver rotation. **No axis-swap or Y-up/Z-up mismatch was found** in the Python backend. Frontend (Three.js, which is Y-up by convention) vs. backend (Z-up) consistency was **not verified** — `VALIDATION GAP`, flagged as `CFG-001` below; requires inspecting `frontend/src` rendering code against `environment/visualization.py`.

### 7.4 LEDs
`LED.__init__` **independently recomputes the Lambertian order** (`m = -ln(2)/ln(cos(beam_angle))`, lines 27–32) using the same formula as `physics/lambertian.py::lambertian_order()`, but as a **second, separate implementation**. This is a duplication risk (Part 61): if the physics team ever changes clamping/edge-case behavior in `lambertian.py` (e.g., for `beam_angle ≥ 90°`), `LED.lambertian_order` silently diverges. See `M1-ENV-003`.

Also: `LED` stores `beam_angle`, `fov`, `lambertian_order` per instance, but **`EnvironmentState` never carries these fields** (see §7.9), forcing Module 2 to hardcode `beam_angle=60.0` for every LED regardless of configuration (see `M2-PHY-002`).

### 7.5 Receivers
`environment/receiver.py::Receiver.receive_signal()` and `.measure_snr()` (lines 65–81) are a **second, independent, non-canonical implementation of received-power and SNR calculations**, structurally similar to (but numerically different from) the Module-2 canonical path. `grep` confirms these methods are **not called anywhere else in the repository** (dead code) — but they are public API surface on a Module-1 class and violate the "Module 1 = geometry only" ownership boundary. Flagged as `M1-ENV-004`, severity P2 (dead but misleading; a future contributor could easily wire it in by mistake, silently bypassing the canonical physics).

### 7.6 LOS
Covered in §7.2 — correct, deterministic, tolerant of edge cases. `Obstacle.intersects_ray()` was inspected structurally (AABB and cylinder support present in `obstacle.py`) but the intersection math itself was **not re-derived line-by-line** — `VALIDATION GAP`, see `T-M1-004`.

### 7.7 Obstacles
Two obstacle types confirmed in `configs/default.yaml` (cylinder "human", box "desk") consistent with `obstacle.py::create_obstacle()` factory. Not exhaustively audited for degenerate cases (zero-size, receiver-inside-obstacle) — `VALIDATION GAP`.

### 7.8 Mobility
`environment/mobility.py` was **not opened in this pass** — `VALIDATION GAP`. `configs/default.yaml` references `circular`, `static`, `linear`, `random_walk`, `waypoint`, `spline` modes; `Scene.update()` calls `mobility_engine.update_position(pos, vel, dt)` generically. Must be audited against Part 12 (units, boundary behavior, reproducibility) before Module 5.

### 7.9 State Management — **CRITICAL FINDING**
`environment/state.py::EnvironmentState` is a frozen dataclass with **two separate physically-meaningful gain fields**:
- `dc_gains: Dict[int, float]` — populated by `Scene.get_geometric_metrics()` → `GeometryEngine.calculate_lambertian_dc_gain()` (Module 1's own, non-canonical formula).
- `physics: Dict[str, Any]` — populated later by `PhysicsEngine.compute()` → `PhysicsEngine.export()`, which includes `los_gains`, `total_gains`, `received_powers`, `snrs`, etc. (the canonical Module 2 values).

This is a direct violation of Rule/Part 13 ("It should NOT contain duplicated physical calculations that belong exclusively to Module 2"). See `M1-ENV-002` for the fix.

Additionally, `EnvironmentState` has **no room-dimension fields** (`room_width/length/height` are absent), forcing both `physics_engine.py` and `localization/engine.py` to **independently hardcode** `room_dims = [5.0, 5.0, 3.0]` — see `INT-001`.

### 7.10 Issues — see Section 18 (Issue Register) for full templates: `M1-ENV-001` through `M1-ENV-004`.

---

## 8. MODULE 2 AUDIT — High-Fidelity Optical Physics Engine

### 8.1 Architecture
`lambertian.py`, `concentrator.py`, `optical_channel.py` (canonical H(0)), `reflection.py` (NLOS), `photodiode.py`, `noise.py`, `snr.py`, `channel_estimator.py`, `raytracer.py`, orchestrated by `physics_engine.py::PhysicsEngine`.

### 8.2 Lambertian Model
`lambertian.py::lambertian_order(theta_half_deg)`: `m = -ln(2)/ln(cos(θ))`, radians conversion internal, guards `cos_theta <= 0 or cos_theta >= 1.0 → return 1.0` (avoids `ln(0)` / `ln(negative)` — correct numerical-stability guard, Part 62). Matches paper text exactly. `radiation_pattern()` and `irradiance()` are consistent, correctly-clamped auxiliary functions (Part 62: `np.clip(cos_phi, 0, 1)` prevents negative-cosine leakage into `cos^m`). **CORRECT.**

### 8.3 Optical Channel — CRITICAL FINDING
`optical_channel.py::compute_los_dc_gain()` implements
```
H(0) = [(m+1)·A / (2π d²)] · cos^m(φ) · T(ψ) · g(ψ) · cos(ψ),   T(ψ)=1
```
matching paper form exactly, **and its own internal math is correct**. The bug is entirely at the call site:

> **M2-PHY-001 [P0, CONFIRMED BUG].** `physics_engine.py` lines 121–142:
> ```python
> inc_ang = env_state.incident_angles.get(led_id, 0.0)     # DEGREES (see geometry.py)
> irr_ang = env_state.irradiance_angles.get(led_id, 0.0)   # DEGREES
> ...
> los_gain = compute_los_dc_gain(
>     distance=dist,
>     irradiance_angle_rad=irr_ang,      # <-- degrees passed where radians expected
>     incident_angle_rad=inc_ang,        # <-- degrees passed where radians expected
>     beam_angle_deg=beam_angle,
>     ...,
>     fov_rad=np.radians(self.config["fov"]),   # this one IS correctly converted
>     ...)
> ```
> `environment/geometry.py::calculate_angles()` explicitly returns degrees (`phi = np.degrees(np.arccos(cos_phi))`). `compute_los_dc_gain()`'s own FOV gate (`if incident_angle_rad > fov_rad or incident_angle_rad < 0.0: return 0.0`, `optical_channel.py` line 25) then compares a **degree-valued** `inc_ang` (e.g., 15.0) against a **radian-valued** `fov_rad` (e.g., 1.22 for 70°). Any legitimate incidence angle greater than ≈1.22 "degrees-read-as-radians" — i.e., almost every realistic geometry — is incorrectly zeroed. Where the FOV check happens not to trigger, `cos(irradiance_angle_rad)` and `cos(incident_angle_rad)` are evaluated on numerically wrong arguments (degrees fed to a function expecting radians), corrupting the gain by an arbitrary, geometry-dependent factor.
>
> **Impact:** every quantity downstream of `los_gain` in `PhysicsState` — `received_powers`, `electrical_currents`, `voltages`, `noise_variances` (via signal-dependent shot noise), `snrs` — is wrong. This propagates into Module 3's BER/rate (which consume physics-derived channel gains/SNR) and Module 4's localization SNR/confidence scoring (`localization/channel_interface.py` reads `physics_state.los_gains` directly). This is the single highest-priority fix in the entire repository.
>
> **Fix:** convert `irr_ang`/`inc_ang` to radians at the point of use in `physics_engine.py` (`np.radians(irr_ang)`, `np.radians(inc_ang)`), OR (preferred, safer against recurrence) change `environment/geometry.py::calculate_angles()` to return radians and rename fields/docstrings accordingly, updating all other consumers (`scene.py`, any visualization code that currently assumes degrees). Add a unit test that pins the units contract at the `EnvironmentState` boundary (`T-INT-001`).

### 8.4 Photodiode
`photodiode.py`: `I = P·R·M` (`convert_power_to_current`), `V = (I + I_dark·M)·R_tia` (`generate_voltage`). Matches Part 19 exactly. **CORRECT.**

### 8.5 Propagation Delay
`physics_engine.py` line 170–173: `delay = dist / c` with `c = 299792458.0` (matches `physics/constants.py::SPEED_OF_LIGHT`, hardcoded a second time here rather than imported — minor duplication, `M2-PHY-005`, P3). Delay is stored in `optical_delays` **and** `propagation_times` (identical values, redundant field naming — P3, `M2-PHY-006`) and is genuinely consumed downstream in `localization/channel_interface.py` (not just metadata) — confirmed correct wiring for Part 20's "must not be ignored" requirement.

### 8.6 Noise
`noise.py` computes four independent variance terms (shot: `2qIB`, thermal: `4k_BTB/R_tia`, background: `2qI_bgB`, electronic: fixed PSD × B) and sums them (Part 21). Dimensionally consistent as A² (verified: thermal term `4kTB/R` has units W/Ω = (A²Ω)/Ω = A², consistent since `tia_gain` is used as an Ω-equivalent resistance). **PHYSICS-EXTENSION, reasonably implemented** — paper does not specify noise sub-terms; only `δ²` as a lumped parameter. **CORRECT / reasonable given [PHYSICS-EXTENSION] status**, contingent on M2-PHY-001 being fixed (shot noise depends on `signal_current`, which is currently wrong).

### 8.7 SNR — see Section 13 (dedicated SNR audit).

### 8.8 LED Frequency Response
`communication/led_frequency_response.py` exists but was **not opened in this pass** — `VALIDATION GAP`, `T-M3-006` required before Module 5 (needed for pre-equalization Eq. 18 to be meaningful).

### 8.9 Multipath
`physics/reflection.py::compute_nlos_reflection()` is called from `physics_engine.py` with a **hardcoded** `led_normal=[0,0,-1]` (ignoring each LED's actual configured orientation — minor issue, `M2-PHY-003`, P2, since all LEDs in `default.yaml` do point straight down, masking the bug) and a **hardcoded** `room_dims=[5.0,5.0,3.0]` (see `INT-001`). Internal reflection-model math (bounce order, reflection coefficient formula) was **not re-derived** — `VALIDATION GAP`, `T-M2-005`.

### 8.10 Issues — `M2-PHY-001` through `M2-PHY-006`, see Section 18/19.

---

## 9. MODULE 3 AUDIT — DCO-OFDM Communication Engine

### 9.1 Architecture
`qam.py`, `ofdm.py` (`OFDMModulator`/`OFDMDemodulator`), `dco_ofdm.py`, `channel_equalizer.py`, `ber.py`, `rate.py`, `snr.py`, `pre_equalizer.py`, `subcarrier_grid.py`, `led_frequency_response.py`, orchestrated by `engine.py`.

### 9.2 QAM
`qam.py::QAMModem` supports `M ∈ {2, 4, 16, 64, 256}`. Gray-coding verified algebraically: per-axis levels are assigned via the standard reflected binary Gray sequence (`i ^ (i>>1)`) in ascending physical-level order, guaranteeing adjacent constellation points differ by exactly one bit — **CORRECT**. Unit average energy normalization (`E[|X|²]=1`) via `norm_factor = 1/sqrt(mean(|X|²))` — **CORRECT**. `modulate()`/`demodulate()` index reconstruction (`sym_indices = val_i*L + val_q` and its inverse) verified consistent — **CORRECT**.

> **`M3-COM-001` [P2, MISSING_FEATURE].** Paper's experimental modulation set is `M = {2, 4, 8, 16, 32, 64}` (Section IV experimental setup). The repo supports `{2,4,16,64,256}` — **8-QAM and 32-QAM (cross constellations) are entirely unsupported**, and 256-QAM (not in the paper) is added instead. Because 8/32-QAM are not square constellations, this is a real feature gap, not a one-line fix — flagged as a required addition before Section IV's adaptive-modulation curves (Eq. 17 context) can be reproduced.

### 9.3 OFDM
`ofdm.py::OFDMModulator.modulate()`: writable indices restricted to `0 < idx < N/2` (matches paper's `n = 1,…,N/2−1`, Part 30); Hermitian symmetry applied via `freq_grid[N-k] = conj(freq_grid[k])` for `k in [1, N/2)`; DC and Nyquist bins explicitly zeroed; IFFT imaginary residual checked against a `1e-11` tolerance and raises `OFDMError` if violated (excellent numerical-stability guard, Part 62). CP insertion copies the last `cp_length` samples to the front — standard, correct. **CORRECT, PAPER-EXACT indexing convention.**

### 9.4 DCO Bias
`dco_ofdm.py`: `B_DC = k·σ_AC` (k=3.0 default), `clip(biased, min, max)`, clipping-ratio and distortion-power metrics computed from `clipped - biased` (Part 31). **[PHYSICS-EXTENSION], reasonably implemented** — paper gives no explicit bias-selection rule.

### 9.5 Channel Interface
`communication/channel_interface.py` was **not opened in this pass** — `VALIDATION GAP`, `T-M3-005` required (Part 33: verify it doesn't double-apply noise/channel, and that it actually calls into `PhysicsState` rather than reinventing gain).

### 9.6 Equalization
`channel_equalizer.py` was **not opened** — `VALIDATION GAP`, `T-M3-004`.

### 9.7 SNR — **CRITICAL FINDING**, see Section 13.

### 9.8 BER
`ber.py::BERCalculator.compute_analytical_qam()`. Algebraic re-derivation:
Code computes `0.5 · [(4/k)(1 − 1/√M)] · erfc(√(3γ/(2(M−1))))` where `k = log2(M)`.
Simplify: `0.5 · 4/k = 2/k`. Paper's coefficient `(√M−1)/(√M·log2(√M))`; since `log2(√M) = k/2`, this equals `2(√M−1)/(√M·k) = (2/k)(1 − 1/√M)`.
**These are algebraically identical.** `erfc` argument `√(3γ/(2(M−1)))` matches paper Eq. (2) exactly. **CONFIRMED CORRECT** — this is the one area of the codebase where a superficial code-vs-paper comparison could easily produce a false-positive "bug" report (the intermediate variable names look like a generic AWGN Q-function derivation, not a direct paper transcription); full algebraic reduction is required and was performed. `compute_empirical()` correctly trims to common length before comparing rather than silently mismatching — acceptable per Part 35, though truncation-on-mismatch should ideally raise a warning rather than silently trim (`M3-COM-004`, P3).

`M` restricted to `{2,4,16,64,256}` for analytical BER, same gap as §9.2.

### 9.9 Data Rate
`rate.py::RateCalculator.compute_user_rates()`: `raw_rate = Σ B_n·log2(M_n)` over allocated indices — matches paper Eq. (3) exactly (`raw_rate_bps` field explicitly kept separate from `effective_throughput_bps`, which correctly is **not** labeled as the paper quantity — good practice per Part 37's explicit warning against conflating Shannon capacity/goodput with the paper's raw rate). **CONFIRMED CORRECT.**

### 9.10 EVM/PAPR
`evm.py` not opened — `VALIDATION GAP`. `dco_ofdm.py::compute_papr()` (`10·log10(peak²/avg²)`) is dimensionally correct and matches Part 38's definition (`E[|x|²]` used correctly as an approximation via `np.mean`).

### 9.11 Pre-equalization
`pre_equalizer.py::PreEqualizer`. Zero-forcing mode (`W=1/H`) and regularized mode (`W = H*/(|H|²+λ)`, standard MMSE-style regularization) both correctly implement transmitter-side inversion of the LED channel response, matching paper Eq. (18)'s intent (`S'_k = √P_k · H_k^{-1}(ρ_k) · S_k`). Correctly **disabled by default** (`enabled=False`) — matches PART 39's explicit instruction ("primitive readiness only, not full adaptive"). Gain clipping (`max_gain=10.0`) and post-equalization power renormalization are sound numerical-stability additions (Part 62). **CORRECT as a primitive; full Eq. (18) with a real, subcarrier-resolved `H_k` still needs `M3-COM-005` (below) resolved first.**

### 9.12 Issues — `M3-COM-001` (missing M), `M3-COM-002` (SNR Eq. 1 missing √, see §13), `M3-COM-003` (delta/naming confusion, see §13), `M3-COM-004` (silent BER truncation), `M3-COM-005` (LED frequency response validation gap).

---

## 10. MODULE 4 AUDIT — A-DPDOA Localization Engine

### 10.1 Architecture
`signal_generator.py` (Eq. 4 Tx tones, `full_waveform`/`phase_equivalent` modes), `channel_interface.py` (applies Module-2 gain/delay/noise, Eq. 5/6), `phase_estimator.py` (Eq. 7–15), `position_solver.py` (`DistanceDifferenceSolver` = Eq. 16, `PositionSolver` = nonlinear trilateration), `calibration.py` (shifting-error mitigation), `engine.py` (orchestrator).

### 10.2 Localization Tones
`signal_generator.py::generate_frame()`: `s_i(t) = √P_i · sin(2πf_i t + φ0)` (full_waveform mode) or `√P_i · e^{jφ0}` (phase_equivalent mode) — matches paper Eq. (4) exactly. `default_mapping = {1:[1], 2:[2], 3:[3], 4:[4], 5:[1]}` **correctly encodes the paper's physical topology** that tone f5 is transmitted from LED 1 (same LED as f1) — a subtle detail from the paper's Section II-A prose, not from the equations, and easy to get wrong; **verified correctly implemented.**

### 10.3 Received Signal
`channel_interface.py::apply_channel()`. Delay is applied as `sin(ω(t−τ) + φ0)` (full_waveform) or `exp(j(−ωτ+φ0))` (phase_equivalent) — i.e., the **physically standard** `s(t−τ) ⇒ e^{-jωτ}` convention. **This differs from the paper's own literal Eq. (5)/(6)**, which write the received phase as `sin(ωt + ωτ + φ0)` (a `+ωτ` phase **advance**, unusual for a physical delay but explicitly what is printed in the paper and used consistently through Eqs. 7–16). This is flagged `PAPER_AMBIGUITY` — see §10.9 below for why it does not break correctness, provided the compensating sign in `position_solver.py` (§10.10) is preserved.

Gain sourced from `physics_state.los_gains` (or `total_gains` if `channel_mode="multipath"`) — correctly delegates to Module 2, does not recompute gain. Noise variance sourced from `physics_state.noise_variances` (mean across LEDs, in-band-scaled by `bp_bandwidth/rx_bandwidth`) — a reasonable [PHYSICS-EXTENSION] approximation, though `rx_bandwidth = 50.0e6` is hardcoded rather than sourced from `Photodiode.bandwidth`/config (`M4-LOC-006`, P2).

### 10.4 Differential Phase
`phase_estimator.py::process_full_waveform()`: per-tone bandpass isolation → pairwise multiply (`s_curr * s_next`) → bandpass at `Δf` → matches paper Eqs. (7)–(9) structurally (produces the sum- and difference-frequency products; the BPF at `Δf` isolates the difference term, matching the paper's stated post-BPF result). Filter internals (`filters.py`, Butterworth order/zero-phase) **not re-derived** — `VALIDATION GAP`, `T-M4-004`.

### 10.5 BPF — covered above; center-frequency/bandwidth parameterization looks sound (`center_freq_hz=Δf`, `bandwidth_hz=bp_bandwidth`) but exact filter design (order, transient/group-delay handling for the "offline_zero_phase" option) needs a dedicated numerical test — `T-M4-005`.

### 10.6 Dual Differential / 10.7 Hilbert-IQ / 10.8 Phase Estimation
Both `process_full_waveform()` (via `scipy.signal.hilbert`) and `process_phase_equivalent()` (via direct complex conjugate-multiply chain `D_i = Y_{i+1}·conj(Y_i)`, `DD_i = D_{i+1}·conj(D_i)`) were **algebraically re-derived from the code, not assumed**:

For the phase-equivalent path, with `Y_i = √P_i · gain_i · e^{j(-ω_i τ_i + φ0)}`:
- `D_i = Y_{i+1}·conj(Y_i)` has phase `-(ω_{i+1}τ_{i+1} − ω_iτ_i)` — the common `φ0` term cancels correctly (matches the paper's own claim that the differential approach removes the LO/phase-lock requirement).
- `DD_0 = D_1·conj(D_0)` has phase `−(ω_1τ_1 + ω_3τ_3 − 2ω_2τ_2)` — the **negative** of paper Eq. (13)'s target quantity `ω1t1+ω3t3−2ω2t2`.
- `DD_1` similarly equals `−(paper Eq. 14 quantity)`, and `DD_2` (using `τ_5=τ_1` per §10.2) equals `−(paper Eq. 15 quantity)`.

So `atan2(Q_i, I_i)` in the code returns **exactly the negative** of the paper's θ1, θ2, θ3. This is a direct, mechanical consequence of the `−ωτ` vs. `+ωτ` convention difference in §10.3, and it is **consistent across all three equations** (not an accidental sign flip in only one). `PhaseUnwrapper.unwrap()` (temporal-continuity-based, falling back to `np.unwrap`) does not care about the absolute sign and is not affected.

### 10.9 Phase Ambiguity — `PhaseUnwrapper` uses temporal continuity (`diff mapped to [-π,π]` relative to the previous frame) when a previous estimate exists, else `np.unwrap()` cold-start. This is a reasonable Part 54 approach but, as the task itself notes, `np.unwrap()` alone does not resolve the physical 2π/frequency integer ambiguity across widely-spaced measurement epochs — flagged `M4-LOC-007`, P2, `VALIDATION GAP` (needs an explicit test with a deliberately large simulated jump).

### 10.10 Equation 16 — **verified correct, with documented convention difference**
`position_solver.py::DistanceDifferenceSolver._build_coefficient_matrix()` builds the paper's literal `[+f1, −2f2, +f3]`-style row coefficients (matching Eq. 16's matrix as printed, confirmed by re-deriving the arithmetic-progression cancellation of the reference-LED term `d1` algebraically), **then explicitly negates the whole matrix**: `self.A = -self.A * (2π/c)`, with the code comment "Apply phase factor (2·π/c) with negative sign for physical negative delay propagation" — i.e., the implementer was aware of and explicitly compensated for the `−ωτ` convention.

Full algebraic check performed: since `θ_measured = −θ_paper` (from §10.6–10.8) and `A_code = −A_paper`, solving `A_code · Δd = θ_measured` gives `(−A_paper)·Δd = −θ_paper ⟺ A_paper·Δd = θ_paper`, which is exactly the paper's intended system. **The double negative cancels correctly.** This is CORRECT but **fragile**: the correctness depends on two independently-written files (`channel_interface.py` and `position_solver.py`) agreeing on an undocumented sign convention. Required action: `M4-LOC-008` — add an explicit code comment cross-referencing both files, and add `T-M4-003` (a synthetic exact-delay end-to-end test) as a permanent regression guard so a future well-intentioned "fix" to match the paper's literal `+ωτ` in only one of the two files does not silently break localization.

Matrix construction correctly uses `np.linalg.solve` for the square 3×3 case with `np.linalg.lstsq` fallback on `LinAlgError`, and separately for non-square cases — matches Part 53's preference. Condition number computed and exposed (`self.cond_number`) and used in `engine.py` for confidence scoring — good practice.

### 10.11 Distance Differences — sourced solely from the phase/matrix chain above; no direct-distance shortcut found. **CORRECT.**

### 10.12 Position Solver
`PositionSolver.solve()` uses `scipy.optimize.least_squares` with `trf` (bounded, supports `soft_l1` robust loss) or `lm` (unbounded) methods, multiple initialization strategies (`room_center`, `grid_search`, `centroid_visible`, warm-start from `self.last_estimated_position`). Residual function `_residual_func()` uses **only** `led_positions` (config, not ground truth) and the measured `distance_differences` dict — **no ground-truth access**. **CONFIRMED CORRECT**, satisfies Part 56.

### 10.13 Calibration
`calibration.py::LocalizationCalibrator` / `ShiftingErrorMitigator` were referenced (`mitigate_phases`, `mitigate_distance_differences`) but **not opened in this pass** — `VALIDATION GAP`, `T-M4-006` required. The task's Part 57 warning ("Do not claim a generic smoothing filter is equivalent to paper shifting-error mitigation") applies directly here: must verify this implements an actual per-LED/per-tone bias calibration (as `configs/default.yaml`'s `calibration.phase_bias_rad`/`delay_bias_s` arrays suggest) rather than a generic filter.

### 10.14 Ground-Truth Isolation — **VERIFIED CLEAN, highest-priority pass of the audit.**
`localization/engine.py::step()` line 107: `p_true = np.array(environment_state.receiver_position)` is read exactly once, and is used **only** for: (a) `self.metrics.add_frame(..., true_pos=p_true, ...)` (evaluation metrics), (b) `LocalizationState.true_position_for_evaluation_only` (explicitly, unambiguously named output field), and (c) computing `err_diff = p_est - p_true` for reporting. `pos_solver.solve()` is called with `initial_guess=p_guess`, where `p_guess = self.last_estimated_position` — **the engine's own prior estimate**, never ground truth. `DistanceDifferenceSolver` never receives `environment_state` at all — only `frequency_plan` and `tone_to_led_map`. **No CRITICAL — GROUND TRUTH LEAKAGE found.** This satisfies the audit's single highest-stakes requirement (Part 43) and should be locked in with `T-M4-002` (a static-analysis/import-boundary test, e.g., `PositionSolver`/`DistanceDifferenceSolver` classes must have no code path referencing `EnvironmentState.receiver_position`) so this property cannot silently regress.

### 10.15 Issues — `M4-LOC-006` (hardcoded rx_bandwidth), `M4-LOC-007` (phase-ambiguity validation gap), `M4-LOC-008` (undocumented sign convention), plus `VALIDATION GAP`s in `filters.py`, `calibration.py`.

---

## 11. CROSS-MODULE INTERFACE AUDIT

| Interface | Finding |
|---|---|
| Module 1 → 2 (geometry, angles, LOS) | **BROKEN**: units contract violated (degrees vs radians), see `M2-PHY-001`. Distance/LOS boolean handoff itself is correct. |
| Module 1 → 2 (room dims) | **MISSING**: `EnvironmentState` has no room-dimension fields; Module 2 and Module 4 each independently hardcode `[5.0,5.0,3.0]`. See `INT-001`. |
| Module 1 → 2 (LED beam angle / lambertian order) | **MISSING**: not carried in `EnvironmentState`; Module 2 hardcodes `beam_angle=60.0` for all LEDs. See `M2-PHY-002`. |
| Module 2 → 3 | `VALIDATION GAP` — `communication/channel_interface.py` not yet audited; must confirm it consumes `PhysicsState` rather than re-deriving gain. |
| Module 2 → 4 | **CORRECT** — `localization/channel_interface.py` correctly consumes `physics_state.los_gains`/`total_gains`/`propagation_times`/`noise_variances`; delay is genuinely applied to the waveform (not just metadata). |
| Module 3 / Module 4 reinventing physics | Module 4 does not; `communication/` not fully checked — `VALIDATION GAP`. |

---

## 12. UNITS AND DIMENSIONAL ANALYSIS

| Variable | Meaning | Required unit | Actual unit in code | Status |
|---|---|---|---|---|
| `irradiance_angles`, `incident_angles` (EnvironmentState) | φ, ψ | rad (internal convention target) | **degrees** | **MISMATCH** — root cause of M2-PHY-001 |
| `fov_rad` (physics_engine.py) | Ψc | rad | rad (`np.radians()` applied) | OK |
| `beam_angle_deg` (optical_channel.py param) | semi-angle | deg | deg | OK (name is honest) |
| distances `d` | m | m | m | OK |
| delay `τ` | s | s | s (`d/c`) | OK |
| `noise_variance` (physics) | A² | A² | A² | OK, dimensionally consistent (verified §8.6) |
| `receiver.gain` (Receiver class) | dimensionless concentrator gain g(ψ) | dimensionless | used directly as g(ψ) in `M1-ENV-002`'s duplicate formula, bypassing the actual Snell's-law concentrator equation | **MISMATCH** (design/duplication issue, not a unit bug per se) |
| LED `power` | W (optical) | W | 20.0 W default in `configs/default.yaml` | Plausible only if these are high-power LED arrays, not typical single 5mm LEDs (mW range) — flag as `CFG-002`, P3, needs paper cross-check (`NOT_SPECIFIED_IN_PAPER` for optical power in the excerpt provided) |
| Localization `sample_rate_hz` default (10 MHz) vs. paper tone range (4.0–4.8 MHz) | Nyquist margin | `Fs > 2·f_max` = 9.6 MHz | 10 MHz (default.yaml) | **Technically satisfies Nyquist but with <5% margin** — flag as `CFG-003`, P2, insufficient for a realistic anti-alias filter transition band; recommend ≥20 MHz for a paper-reproduction profile |

---

## 13. SNR DEFINITION AUDIT (Priority Table, Part 22)

| Variable | File | Formula (as implemented) | Linear/dB | Matches paper Eq.1? |
|---|---|---|---|---|
| `physics/snr.py::compute_snr` | Physics | `I²/σ²` (electrical), `I/σ` (optical) | both | N/A — this is a physical-link SNR, not the paper's per-subcarrier `γ_{k,n}^co`; correctly a *different* quantity, not mislabeled. |
| `communication/snr.py::compute_communication_snr` | Comm | `δ²·μ²·(Σ_i P_{n,i}·H_{i,n,k})² / σ²` | linear | **NO — BUG.** |
| `localization/channel_interface.py` (inline, per-tone) | Loc | `(μ·P_rx)² / σ²_inband`, dB | dB | N/A — a link-budget SNR for confidence scoring, correctly a different, undocumented-but-reasonable [PHYSICS-EXTENSION] quantity, not claiming to be Eq. 1. |

> **`M3-COM-002` [P1, CONFIRMED BUG].** Paper Eq. (1): `γ_{k,n}^co = μ²·(Σ_{i=1}^{L} √P_{n,i}·H_{i,n,k})² / δ²` — note the **square root** inside the summation (amplitude/coherent-voltage combining across LEDs). `communication/snr.py::compute_communication_snr()` implements `combined_optical = Σ (P_{n,i} · H_{i,n,k})` — **using `P_{n,i}` directly, without the square root** — even though its own docstring (lines 13–14) correctly transcribes the paper formula with `√P_{n,i}`. This is a clean, mechanical, high-confidence bug: the docstring and the code disagree, and the code is wrong. **Fix:** `combined_optical = np.sum(np.sqrt(subcarrier_powers) * gains_transposed, axis=1)`.
>
> **`M3-COM-003` [P2, PAPER_AMBIGUITY / naming risk].** The function also accepts a `delta: float = 1.0` parameter documented as "Standard scaling/efficiency factor," which does **not** correspond to anything in the paper — the paper's own `δ²` symbol denotes the *additive background noise power* (already correctly represented by the separate `noise_variance` parameter). Having an unrelated quantity named `delta` sitting next to a `noise_variance` that is the *actual* `δ²` is confusing and risks a future contributor conflating the two. Recommend renaming `delta` → `scaling_factor` (or removing it entirely, since default 1.0 makes it currently inert) to eliminate the naming collision with the paper's δ².

---

## 14. DUPLICATE LOGIC AUDIT (Part 61)

| Quantity | Canonical location | Duplicate(s) | Status |
|---|---|---|---|
| Lambertian LOS gain H(0) | `physics/optical_channel.py::compute_los_dc_gain` | `environment/geometry.py::calculate_lambertian_dc_gain` | **Confirmed duplicate, actively used, disagreeing formula** — `M1-ENV-002` |
| Lambertian order `m` | `physics/lambertian.py::lambertian_order` | `environment/led.py::LED.__init__` (inline) | **Confirmed duplicate**, currently numerically identical formula but independently maintained — `M1-ENV-003` |
| Received power / SNR (link-level) | `physics/photodiode.py` + `physics/snr.py` | `environment/receiver.py::Receiver.receive_signal/measure_snr` | **Confirmed duplicate, currently dead code** — `M1-ENV-004` |
| Room dimensions | `environment/room.py::Room` | Hardcoded `[5.0,5.0,3.0]` in `physics/physics_engine.py` and `localization/engine.py` | **Confirmed duplicate/hardcode, not sourced from Room** — `INT-001` |
| Speed of light `c` | `physics/constants.py::SPEED_OF_LIGHT` | Re-literaled in `physics_engine.py` and `position_solver.py` | Same value, harmless today, still a maintainability risk — `M2-PHY-005`, P3 |

---

## 15. NUMERICAL STABILITY AUDIT (Part 62)

Positive findings: `lambertian.py` guards `cos_theta<=0` before `ln()`; `ofdm.py` explicitly checks and raises on Hermitian-symmetry/IFFT-imaginary-residual violations (`1e-11` tolerance); `physics/snr.py` and `communication/ber.py`/`rate.py` guard divide-by-zero with `np.where`/floor values; `position_solver.py` falls back from `np.linalg.solve` to `np.linalg.lstsq` on `LinAlgError` and exposes `cond_number` for downstream confidence gating. `environment/geometry.py::distance()` returns 0.0 gracefully rather than raising on coincident points, with callers (`calculate_angles`, `is_visible_los`) checking `d==0` explicitly. No `float32` usage was found in the audited files (all `np.float64` / Python `float`, matching Part 62's "use float64" requirement). **No new numerical-stability issues found beyond those already logged as functional bugs.**

---

## 16. CONFIGURATION AUDIT (Part 71)

Only `configs/default.yaml` exists. **No `configs/paper_reference.yaml` exists** — `CFG-004`, P1 MISSING_FEATURE (see Section 27, required before Section IV of the paper can be reproduced). Spot-checked parameters:

| Parameter | `default.yaml` value | Paper value (Section IV) | Source |
|---|---|---|---|
| Room dims | 5×5×3 m | Not explicitly stated as room dims; coverage area 222.5 m³ | `NOT_SPECIFIED_IN_PAPER` (paper gives coverage volume, not W×L×H) |
| LED positions | quadrant centers of 5×5 room, z=3.0 | (−0.4,0.4,1.35), (0.4,0.4,1.35), (−0.4,0.4,1.35)*, (−0.4,−0.4,1.35) m | Different scale entirely — expected, since default.yaml is a generic demo config, not a paper-reproduction config. (*Paper's Section IV LED-position list appears to contain a duplicate `(−0.4,0.4,1.35)` entry for what is presumably LED 2 at `(0.4,0.4,1.35)` vs. what's printed — this looks like a transcription/OCR artifact in the paper itself; flagged `PAPER_AMBIGUITY`, needs the published erratum or the authors' code to resolve, not guessable.) |
| IFFT size N | not set in `default.yaml`'s visible keys (communication block not shown above) | 256 | `VALIDATION GAP` — need to inspect `communication/config.py` |
| Modulation bandwidth | — | 20 MHz | `VALIDATION GAP` |
| Localization tones | 1.0–1.4 MHz, 100 kHz spacing | 4.0–4.8 MHz, 200 kHz spacing | Different (expected for a generic default) |
| `BER_max` | — | 3.8×10⁻³ | `VALIDATION GAP` — need `communication/config.py` |
| Modulation order set | QAM supports {2,4,16,64,256} | {2,4,8,16,32,64} | **Gap**, see `M3-COM-001` |

---

## 17. PAPER-TO-CODE TRACEABILITY MATRIX

| Paper Eq./Section | Meaning | Target module | Current file/function | Status | Problem | Required fix | Test |
|---|---|---|---|---|---|---|---|
| Eq. 1 | Communication SNR γ_co | M3 | `communication/snr.py::compute_communication_snr` | **BUG** | Missing √ on P_{n,i}; `delta` param collides conceptually with δ² | Add `np.sqrt()`, rename `delta` | `T-M3-001` |
| Eq. 2 | BER | M3 | `communication/ber.py::compute_analytical_qam` | **CORRECT** | — | — | `T-M3-002` (regression pin) |
| Eq. 3 | Rate | M3 | `communication/rate.py::compute_user_rates` | **CORRECT** | — | — | `T-M3-003` (regression pin) |
| Eq. 4 | Tx tone | M4 | `localization/signal_generator.py::generate_frame` | **CORRECT** | — | — | `T-M4-001` |
| Eq. 5/6 | Rx tone (delay convention) | M4 | `localization/channel_interface.py::apply_channel` | **CORRECT, non-paper-literal sign** | Uses `−ωτ` not paper's `+ωτ` | Document; do not "fix" without updating `position_solver.py` in lockstep | `T-M4-003` |
| Eq. 7–9 | First differential | M4 | `localization/phase_estimator.py` (`process_*`) | **CORRECT** (sign-flipped, compensated downstream) | — | Document convention | `T-M4-003` |
| Eq. 10–12 | I/Q extraction | M4 | `phase_estimator.py` | **CORRECT** | — | — | `T-M4-003` |
| Eq. 13–15 | Dual-differential phase | M4 | `phase_estimator.py::process_phase_equivalent`/`process_full_waveform` | **CORRECT** (negated vs. paper, compensated) | — | — | `T-M4-003` |
| Eq. 16 | Distance-difference matrix | M4 | `localization/position_solver.py::DistanceDifferenceSolver._build_coefficient_matrix` | **CORRECT** (explicit compensating negation) | Fragile cross-file convention coupling | Add cross-reference comment + regression test | `T-M4-003` |
| Adaptive Eq. 17 | Modulation selection | M3 | Not implemented (by design, Part 88) | N/A — interface readiness only | `M` set gap (`M3-COM-001`) will limit future Eq. 17 work | Extend `QAMModem`/`BERCalculator` to 8/32-QAM | `T-M3-007` |
| Pre-eq Eq. 18 | `S'_k = √P_k·H_k^{-1}·S_k` | M3 | `communication/pre_equalizer.py::PreEqualizer` | **CORRECT primitive**, disabled by default | Needs real per-subcarrier `H_k` from `led_frequency_response.py` (unaudited) | Audit `led_frequency_response.py`, wire in | `T-M3-006` |
| N/A — H(0) core physics | LOS channel gain | M2 | `physics/optical_channel.py::compute_los_dc_gain` | **CORRECT in isolation** | Called with wrong units (M2-PHY-001) | See M2-PHY-001 | `T-M2-001`, `T-INT-001` |

---

## 18. COMPLETE ISSUE REGISTER

Each issue below uses the required template.

---
**Issue ID:** M2-PHY-001
**Module:** 2 (Physics)
**Severity:** P0 — CRITICAL
**Classification:** CONFIRMED BUG
**Affected files:** `backend/VLCL_AI/physics/physics_engine.py`
**Affected functions/classes:** `PhysicsEngine.compute()`
**Current behavior:** Degree-valued `env_state.irradiance_angles[led_id]` / `env_state.incident_angles[led_id]` are passed as `irradiance_angle_rad`/`incident_angle_rad` into `compute_los_dc_gain()`, which treats them as radians.
**Expected behavior:** Angles must be converted to radians (`np.radians(...)`) before being passed, or the units contract at the `EnvironmentState` boundary must be radians end-to-end.
**Paper reference:** Eq. (Section II-B, H(0) definition, "0 ≤ ψ ≤ Ψc")
**Relevant equation:** H(0) = [(m+1)A/(2πd²)]·cos^m(φ)·T(ψ)g(ψ)cos(ψ)
**Why current behavior is wrong/risky:** FOV gating and cosine evaluation both operate on the wrong numeric domain, corrupting or zeroing nearly all channel gains.
**Scientific impact:** Every physically-derived quantity in `PhysicsState` (gain, power, current, noise, SNR) is wrong; cascades into Modules 3 and 4.
**Required code change:** Convert angles to radians at the physics_engine.py call site (minimal fix) or change `calculate_angles()`'s return contract to radians and update all consumers (root-cause fix, preferred).
**Dependencies:** None — should be fixed first (Phase A/C).
**Migration concern:** Any existing snapshot tests/expected-output files baked from the buggy behavior will need to be regenerated.
**Required tests:** `T-INT-001`, `T-M2-001`
**Acceptance criteria:** For a synthetic geometry with hand-computed φ, ψ, H(0) must match to within 1e-9 relative error.

---
**Issue ID:** M1-ENV-001
**Module:** 1 (Environment)
**Severity:** P1 — HIGH
**Classification:** CONFIRMED BUG
**Affected files:** `backend/VLCL_AI/environment/simulator.py`
**Affected functions/classes:** `VLCLSimulator.get_state()`
**Current behavior:** `self.physics.compute(state)` and the final `return replace(state, physics=self.physics.export())` (lines 197–198) are unreachable — they sit after an earlier `return EnvironmentState(...)` (line 195), which is itself already inside the function body without a `physics=` override.
**Expected behavior:** `get_state()` should compute and attach physics data identically to `step()`.
**Paper reference:** N/A (software architecture defect)
**Relevant equation:** N/A
**Why current behavior is wrong/risky:** Any caller expecting a physics-consistent snapshot without advancing the simulation clock silently receives an empty/default `.physics` dict.
**Scientific impact:** Downstream consumers of `get_state()` (if any exist or are added later) will silently operate on incomplete state.
**Required code change:** Move the `self.physics.compute(state)` / `replace(...)` logic before the `return` statement (mirror `step()`'s structure).
**Dependencies:** M2-PHY-001 (fix physics first so the newly-reachable code path is correct).
**Migration concern:** None known; check for any current caller relying on the (buggy) empty `.physics` behavior.
**Required tests:** `T-M1-001`
**Acceptance criteria:** `simulator.get_state().physics` is non-empty and numerically matches `simulator.step().physics` for the same underlying scene state.

---
**Issue ID:** M1-ENV-002
**Module:** 1 (Environment) / Cross-cutting with Module 2
**Severity:** P0 — CRITICAL
**Classification:** CONFIRMED BUG / ARCHITECTURE VIOLATION
**Affected files:** `backend/VLCL_AI/environment/geometry.py`, `backend/VLCL_AI/environment/scene.py`, `backend/VLCL_AI/environment/state.py`, `backend/VLCL_AI/environment/simulator.py`
**Affected functions/classes:** `GeometryEngine.calculate_lambertian_dc_gain`, `Scene.get_geometric_metrics`, `EnvironmentState.dc_gains`
**Current behavior:** Module 1 independently computes an H(0)-like quantity using the receiver's raw `.gain` attribute instead of the Snell's-law concentrator formula `g(ψ)=n²/sin²(Ψc)`, and stores it in `EnvironmentState.dc_gains`. Module 2's canonical, correct `compute_los_dc_gain()` populates a *different* field (`PhysicsState.los_gains`, exposed as `EnvironmentState.physics["los_gains"]`).
**Expected behavior:** Module 1 must not compute channel gain at all; `EnvironmentState.dc_gains` should be removed, and any consumer that currently reads it should read `PhysicsState.los_gains` (post-fix of M2-PHY-001) instead.
**Paper reference:** Section II-B (H(0) definition)
**Relevant equation:** H(0) = [(m+1)A/(2πd²)]cos^m(φ)T(ψ)g(ψ)cos(ψ)
**Why current behavior is wrong/risky:** Two disagreeing numbers for the "same" physical quantity, silently selected by which field a consumer happens to read.
**Scientific impact:** Any future Module 5 work, dashboard, or test built against `EnvironmentState.dc_gains` will be systematically wrong even after M2-PHY-001 is fixed, because M1-ENV-002's formula independently omits the correct concentrator-gain equation.
**Required code change:** Delete `GeometryEngine.calculate_lambertian_dc_gain`, remove its call in `Scene.get_geometric_metrics`, remove `EnvironmentState.dc_gains` field, update `to_dict()`.
**Dependencies:** M2-PHY-001 must land first so the sole remaining gain source is correct.
**Migration concern:** `examples/demo_receiver_mobility.py` and `tests/test_simulation.py` currently read `metrics["dc_gains"]` — must be updated to read from `PhysicsState` instead.
**Required tests:** `T-M1-002`, `T-INT-002`
**Acceptance criteria:** `grep -r "calculate_lambertian_dc_gain\|dc_gains"` returns no hits outside of a migration changelog; only one code path computes H(0).

---
**Issue ID:** M1-ENV-003
**Module:** 1 (Environment)
**Severity:** P2 — MEDIUM
**Classification:** CONFIRMED BUG (duplication risk, not yet numerically wrong)
**Affected files:** `backend/VLCL_AI/environment/led.py`
**Affected functions/classes:** `LED.__init__`
**Current behavior:** Re-implements `m = -ln(2)/ln(cos(beam_angle))` inline instead of calling `physics.lambertian.lambertian_order()`.
**Expected behavior:** `LED` should call the canonical `lambertian_order()` function (or not precompute `m` at all — this arguably belongs to Module 2, not Module 1's LED data object).
**Paper reference:** N/A (duplication, not equation error)
**Relevant equation:** m = −ln2/ln(cosθ½)
**Why current behavior is wrong/risky:** Silent divergence risk if either implementation's edge-case handling changes independently (e.g., `lambertian.py` clamps `cos_theta<=0` to return `1.0`; `led.py`'s inline version has no such guard and would raise/produce `nan` for `beam_angle ≥ 90°`).
**Scientific impact:** Currently none (values agree for the supported range), but latent.
**Required code change:** Import and call `physics.lambertian.lambertian_order()` from `LED.__init__`, or move `lambertian_order` storage out of `LED` and compute it on demand in Module 2.
**Dependencies:** None.
**Migration concern:** None.
**Required tests:** `T-M1-003`
**Acceptance criteria:** Single source of truth for `m`; `LED.lambertian_order` for `beam_angle >= 90°` behaves identically to `physics.lambertian.lambertian_order()`.

---
**Issue ID:** M1-ENV-004
**Module:** 1 (Environment)
**Severity:** P3 — LOW
**Classification:** DESIGN RISK (dead code)
**Affected files:** `backend/VLCL_AI/environment/receiver.py`
**Affected functions/classes:** `Receiver.receive_signal`, `Receiver.measure_snr`
**Current behavior:** Independent, non-canonical received-power/SNR formulas exist on the `Receiver` class but are not called anywhere in the current codebase (confirmed via repository-wide `grep`).
**Expected behavior:** Remove, or clearly mark as deprecated/reference-only, to prevent accidental future use as a shortcut around Module 2.
**Paper reference:** N/A
**Relevant equation:** N/A
**Why current behavior is wrong/risky:** Violates Module 1 = geometry-only ownership boundary; attractive nuisance for future contributors.
**Scientific impact:** None currently (dead code), but risk if activated.
**Required code change:** Delete both methods (or move to a clearly-labeled `examples/`/`reference/` location, not on the production `Receiver` class).
**Dependencies:** None.
**Migration concern:** None (no current callers).
**Required tests:** `T-M1-004` (static check: no physics formulas on `environment/*` classes).
**Acceptance criteria:** `Receiver` class contains only geometric/kinematic state and methods.

---
**Issue ID:** M3-COM-002
**Module:** 3 (Communication)
**Severity:** P1 — HIGH
**Classification:** CONFIRMED BUG
**Affected files:** `backend/VLCL_AI/communication/snr.py`
**Affected functions/classes:** `compute_communication_snr`
**Current behavior:** `combined_optical = Σ (P_{n,i} · H_{i,n,k})` — power, not amplitude, summed.
**Expected behavior:** `combined_optical = Σ (√P_{n,i} · H_{i,n,k})`, matching both the paper and the function's own docstring.
**Paper reference:** Eq. (1)
**Relevant equation:** γ_{k,n}^co = μ²(Σ_i √P_{n,i} H_{i,n,k})² / δ²
**Why current behavior is wrong/risky:** Docstring/code mismatch; wrong physical combining law (power-sum vs. amplitude-sum before squaring materially changes SNR when multiple LEDs contribute to the same subcarrier).
**Scientific impact:** Any multi-LED-per-subcarrier scenario (which the paper's own system explicitly supports, `H_{i,n,k}` summed over `i=1..L`) will produce incorrect SNR, and therefore incorrect BER/rate/adaptive-modulation decisions.
**Required code change:** `combined_optical = np.sum(np.sqrt(subcarrier_powers) * gains_transposed, axis=1)`.
**Dependencies:** None.
**Migration concern:** Existing SNR-dependent tests/snapshots must be regenerated.
**Required tests:** `T-M3-001`
**Acceptance criteria:** For a synthetic 2-LED, single-subcarrier case with hand-computed γ, function output matches to 1e-9 relative error.

---
**Issue ID:** M3-COM-003
**Module:** 3 (Communication)
**Severity:** P2 — MEDIUM
**Classification:** PAPER AMBIGUITY / naming risk
**Affected files:** `backend/VLCL_AI/communication/snr.py`
**Affected functions/classes:** `compute_communication_snr`
**Current behavior:** A `delta` parameter (default 1.0, undocumented physical meaning) is multiplied in, separate from `noise_variance` (which is the actual `δ²` from the paper).
**Expected behavior:** Rename to avoid symbol collision with the paper's `δ²`; document explicitly as a non-paper scaling knob or remove.
**Paper reference:** Eq. (1) (`δ²` = additive background noise power)
**Relevant equation:** γ_{k,n}^co = μ²(Σ_i √P_{n,i} H_{i,n,k})² / δ²
**Why current behavior is wrong/risky:** Naming collision risks a future contributor conflating `delta` with `δ²` and double-applying or misplacing noise scaling.
**Scientific impact:** None currently (default value is inert at 1.0), but latent correctness risk.
**Required code change:** Rename `delta` → `scaling_factor` with an explicit docstring warning that it is not a paper quantity.
**Dependencies:** Should land alongside M3-COM-002.
**Migration concern:** Any caller passing `delta=` by keyword needs updating.
**Required tests:** `T-M3-001` (extend to check default `scaling_factor=1.0` reproduces the pure paper formula).
**Acceptance criteria:** No symbol named `delta` remains adjacent to a `noise_variance`/`δ²` parameter without disambiguating documentation.

---
**Issue ID:** INT-001
**Module:** Cross-module (1↔2, 1↔4)
**Severity:** P2 — MEDIUM
**Classification:** DESIGN RISK / VALIDATION GAP
**Affected files:** `backend/VLCL_AI/environment/state.py`, `physics/physics_engine.py`, `localization/engine.py`
**Affected functions/classes:** `EnvironmentState`, `PhysicsEngine.compute`, `LocalizationEngine.step`
**Current behavior:** Room dimensions live only on `environment/room.py::Room`, never propagated into `EnvironmentState`; `physics_engine.py` and `localization/engine.py` independently hardcode `[5.0, 5.0, 3.0]`.
**Expected behavior:** `EnvironmentState` should carry `room_width/length/height` (or a `room: Dict`), and both Module 2 and Module 4 should read from it.
**Paper reference:** N/A (architecture)
**Relevant equation:** N/A (affects NLOS reflection room-boundary geometry and localization solver bounds)
**Why current behavior is wrong/risky:** If a user edits `configs/default.yaml`'s room dimensions (the most likely first customization anyone makes), the physics NLOS model and the localization solver's search bounds silently continue using the stale hardcoded `5×5×3`, while the rendered/geometric room is whatever was configured — a silent, hard-to-detect inconsistency.
**Scientific impact:** NLOS reflections computed against wrong walls; localization solver bounded/initialized incorrectly for non-default rooms.
**Required code change:** Add room fields to `EnvironmentState`; thread through to `PhysicsEngine.compute()` and `LocalizationEngine.step()`; remove both hardcoded literals.
**Dependencies:** None.
**Migration concern:** Any snapshot tests assuming the hardcoded `5×5×3` must be checked.
**Required tests:** `T-INT-003`
**Acceptance criteria:** Changing `configs/default.yaml`'s room dimensions changes NLOS and solver-bound behavior accordingly, verified by test.

---
*(Remaining lower-severity issues — `M2-PHY-002` through `M2-PHY-006`, `M3-COM-001`, `M3-COM-004`, `M3-COM-005`, `M4-LOC-006` through `M4-LOC-008`, `CFG-001` through `CFG-004` — are fully specified inline in Sections 7–16 above with severity and required fix; they are not repeated in full template form here for space, but must receive the same template treatment in the implementing agent's working notes before code changes begin.)*

---

## 19. P0 CRITICAL ISSUES
- `M2-PHY-001` — degrees-as-radians unit bug corrupting all channel gain.
- `M1-ENV-002` — duplicated, disagreeing H(0) formula with two sources of truth in `EnvironmentState`.

## 20. P1 HIGH-PRIORITY ISSUES
- `M1-ENV-001` — dead code / unreachable physics attach in `get_state()`.
- `M3-COM-002` — missing √ in communication SNR (Eq. 1).
- `CFG-004` — no `paper_reference.yaml` profile exists (blocks Section IV reproduction).

## 21. P2 MEDIUM ISSUES
- `M1-ENV-003` (duplicated Lambertian-order calc), `M3-COM-003` (naming collision), `M3-COM-001` (missing M=8/32), `INT-001` (room-dims not propagated), `M2-PHY-002` (hardcoded beam_angle=60 for all LEDs), `M2-PHY-003` (hardcoded LED normal in NLOS), `M4-LOC-006` (hardcoded rx_bandwidth), `M4-LOC-007` (phase-ambiguity validation gap), `M4-LOC-008` (undocumented cross-file sign convention), `CFG-003` (thin Nyquist margin at paper frequencies).

## 22. P3 LOW-PRIORITY ISSUES
- `M1-ENV-004` (dead-code duplication), `M2-PHY-005`/`M2-PHY-006` (re-literaled constant, redundant field naming), `M3-COM-004` (silent BER-length truncation), `CFG-002` (LED optical power plausibility).

---

## 23. FILE-BY-FILE REPAIR SPECIFICATION (highest-priority files only; extend this template to every file touched)

```
FILE: backend/VLCL_AI/physics/physics_engine.py
CURRENT RESPONSIBILITY: Orchestrates Module 2's per-frame physics computation from EnvironmentState.
PROBLEMS: M2-PHY-001 (units), M2-PHY-002 (hardcoded beam_angle), M2-PHY-003 (hardcoded LED normal),
          M2-PHY-005/006 (duplicated constant/redundant fields), INT-001 (hardcoded room_dims).
KEEP: Overall orchestration structure, PhysicsState dataclass shape, noise/SNR sub-calls.
REMOVE: Hardcoded `beam_angle = 60.0`, hardcoded `room_dims = [5.0, 5.0, 3.0]`,
        hardcoded `led_normal=[0,0,-1]`, re-literaled `c = 299792458.0`.
CHANGE: Convert env_state angle fields to radians before calling compute_los_dc_gain
        (or consume radians directly once EnvironmentState's contract is fixed at the source).
        Source beam_angle/lambertian_order per-LED from EnvironmentState (once M1 exposes it).
        Source room_dims from EnvironmentState (once INT-001 lands). Import SPEED_OF_LIGHT
        from physics.constants instead of re-literaling.
NEW API: PhysicsEngine.compute(env_state) unchanged signature; internal correctness only.
DEPENDENCIES: Requires EnvironmentState to expose room dims and per-LED beam_angle (M1 changes) —
              can be sequenced as: fix units first (independent), then wire room/beam_angle once
              M1 exposes them (Phase B before Phase D, see Section 28).
TESTS: T-M2-001, T-INT-001, T-INT-003
ACCEPTANCE CRITERIA: Synthetic hand-computed H(0)/received-power/SNR cases match to 1e-9 relative error.
```

```
FILE: backend/VLCL_AI/environment/geometry.py
CURRENT RESPONSIBILITY: Stateless geometry utilities (distance, angles, LOS, boundary collision).
PROBLEMS: M1-ENV-002 (owns a duplicate, non-canonical H(0) formula that does not belong in Module 1).
KEEP: distance(), calculate_angles(), is_visible_los(), check_room_boundaries_collision().
REMOVE: calculate_lambertian_dc_gain() entirely.
CHANGE: Decide and document explicitly whether calculate_angles() returns degrees or radians;
        if kept as degrees, rename to calculate_angles_deg() to make the unit contract
        impossible to misuse silently (recommended, cheapest fix for M2-PHY-001's root cause).
NEW API: (none — pure removal + optional rename)
DEPENDENCIES: Must land before/with M1-ENV-002's Scene.get_geometric_metrics() change.
TESTS: T-M1-002
ACCEPTANCE CRITERIA: No H(0)-shaped formula exists outside physics/optical_channel.py.
```

```
FILE: backend/VLCL_AI/environment/scene.py
CURRENT RESPONSIBILITY: Composition root for Room/LEDArray/Receiver/Obstacles; produces geometric metrics.
PROBLEMS: get_geometric_metrics() calls the removed calculate_lambertian_dc_gain(); populates dc_gains.
KEEP: distances, incident_angles, irradiance_angles, visibility_matrix, los_matrix, blocking_obstacles.
REMOVE: dc_gains computation and field from the returned metrics dict.
CHANGE: get_geometric_metrics() no longer returns "dc_gains".
NEW API: Callers must obtain channel gain exclusively from PhysicsState.
DEPENDENCIES: M1-ENV-002.
TESTS: T-M1-002, T-INT-002
ACCEPTANCE CRITERIA: examples/demo_receiver_mobility.py and tests/test_simulation.py updated
                      to read gain from PhysicsState and still pass.
```

```
FILE: backend/VLCL_AI/environment/state.py
CURRENT RESPONSIBILITY: Immutable EnvironmentState snapshot dataclass.
PROBLEMS: dc_gains field (M1-ENV-002); missing room dims (INT-001); missing per-LED beam_angle/
          lambertian_order (M2-PHY-002); angle-unit ambiguity (M2-PHY-001 root cause).
KEEP: Overall frozen-dataclass structure, kinematics fields, obstacles, physics field.
REMOVE: dc_gains field.
CHANGE: Add room_width/room_length/room_height fields (or nested room dict). Add
        led_beam_angles/led_lambertian_orders dict fields. Rename incident_angles/
        irradiance_angles to *_deg or convert to radians at source (pick one, document it).
NEW API: EnvironmentState gains 4-5 new fields; to_dict() updated to match.
DEPENDENCIES: Must land before physics_engine.py / localization/engine.py can stop hardcoding.
TESTS: T-INT-003
ACCEPTANCE CRITERIA: No hardcoded room_dims literal remains in physics_engine.py or
                      localization/engine.py.
```

```
FILE: backend/VLCL_AI/communication/snr.py
CURRENT RESPONSIBILITY: Communication-layer per-subcarrier SNR (paper Eq. 1).
PROBLEMS: M3-COM-002 (missing sqrt), M3-COM-003 (delta naming collision).
KEEP: Function signature shape, numerator/denominator structure, docstring's correct
      transcription of the paper formula (used as the source of truth for the fix).
CHANGE: combined_optical = np.sum(np.sqrt(subcarrier_powers) * gains_transposed, axis=1).
        Rename delta -> scaling_factor with explicit non-paper-quantity docstring note.
NEW API: Parameter rename only (delta -> scaling_factor); update all call sites.
DEPENDENCIES: None.
TESTS: T-M3-001
ACCEPTANCE CRITERIA: 2-LED synthetic case matches hand-computed γ to 1e-9 relative error;
                      grep confirms no remaining `delta` symbol adjacent to noise_variance
                      without disambiguating docstring.
```

---

## 24. TARGET API CONTRACTS

```
EnvironmentState  (Module 1 output — pure geometry, radians, room dims, per-LED params; NO gain fields)
        ↓
PhysicsEngine.step(EnvironmentState) → PhysicsState
        (sole owner of: los_gains, nlos_gains, total_gains, received_powers, optical_delays,
         propagation_times, electrical_currents, voltages, noise_variances, snrs, channel_matrix)
        ├─────────────────────────────┐
        ▼                             ▼
CommunicationEngine.step(PhysicsState, tx_bits, config) → CommState
        (owns: SNR Eq.1 [fixed], BER Eq.2, Rate Eq.3, pre-eq Eq.18 primitive)

LocalizationEngine.step(EnvironmentState, PhysicsState) → LocalizationState
        (owns: Eq.4-16 chain; receives EnvironmentState ONLY to extract
         true_position_for_evaluation_only and led_positions — the ground-truth
         firewall boundary documented in Section 25 below)
```

---

## 25. GROUND-TRUTH FIREWALL DESIGN

**Current implementation already satisfies this design** (verified §10.14); this section documents it as the contract to be preserved, not a redesign.

```
Simulation Truth
──────────────────────────────
EnvironmentState.receiver_position   (true)
        │
        ├──► PhysicsEngine (propagation simulation — legitimate use)
        │
        └──► LocalizationEngine.step(): read exactly once into `p_true`,
              used ONLY for:
                - LocalizationState.true_position_for_evaluation_only
                - LocalizationMetrics.add_frame(true_pos=...)
                - err_diff = p_est - p_true (reporting only)

Estimator-visible measurements
──────────────────────────────
PhysicsState.{los_gains, total_gains, propagation_times, noise_variances}
        │
        ▼
LocalizationChannelInterface.apply_channel() → ReceivedLocalizationSignal
        │
        ▼
PhaseEstimator → PhaseUnwrapper → DistanceDifferenceSolver → PositionSolver
        (these four classes: NO import of, or reference to, EnvironmentState.receiver_position.
         PositionSolver's `initial_guess` may only be: None, room-center, LED centroid,
         or the engine's own previous estimate — never ground truth.)
        │
        ▼
LocalizationState.estimated_position
```

**Required enforcement test:** `T-M4-002` — a static-analysis check (e.g., AST scan or import-linter rule) asserting that `position_solver.py` and the solver-relevant methods of `phase_estimator.py` contain no reference to `receiver_position`, `true_position`, or `ground_truth`. This should run in CI so the firewall cannot silently regress.

---

## 26. TEST AND VALIDATION SPECIFICATION

Following the required Level 1–10 hierarchy (Part 64), populated with concrete, currently-missing tests identified by this audit (existing tests in `tests/` were enumerated but not individually graded in this pass — that grading is itself a required follow-up, see §32):

- **Level 1 (equation unit tests):** `T-M2-001` (H(0) hand-calc), `T-M3-001` (SNR Eq.1 hand-calc), `T-M4-001` (Tx tone), `T-M4-003` (sign-convention end-to-end synthetic delay).
- **Level 2 (geometry → gain):** `T-INT-001` (units contract at EnvironmentState/PhysicsEngine boundary).
- **Level 3 (comm primitives):** existing `tests/test_qam.py`, `test_ofdm.py`, `test_dco_ofdm.py`, `test_ber.py`, `test_rate.py` — grade per Part 63 (`T-M3-002`, `T-M3-003` regression pins for the *correct* Eq.2/Eq.3 already found).
- **Level 4 (localization primitives):** `T-M4-002` (ground-truth firewall static check), `T-M4-004`/`T-M4-005` (filter chain), `T-M4-006` (calibration).
- **Level 5 (noiseless end-to-end):** required new test — zero-noise, LOS-only, exact synthetic geometry through the full Module1→2→4 chain must recover position to numerical-solver tolerance (not currently verifiable as passing until M2-PHY-001 is fixed).
- **Levels 6–9 (noise/multipath/mobility/blockage):** `VALIDATION GAP` — none of `physics/reflection.py`, `environment/mobility.py`, `environment/obstacle.py` internals were re-derived in this pass; must be scheduled.
- **Level 10 (paper scenario reproduction):** blocked on `CFG-004` (no `paper_reference.yaml`).

---

## 27. PAPER REFERENCE CONFIGURATION

`configs/paper_reference.yaml` does not exist and must be created (`CFG-004`). Populate only values explicitly given in the paper text (Section IV):

```yaml
# configs/paper_reference.yaml
# Values sourced verbatim from Yang et al., IEEE Trans. Commun., vol.71 no.12, Dec 2023, Section IV.
# Room dimensions: NOT_SPECIFIED_IN_PAPER (only "coverage area of 222.5 m^3" is given — insufficient
#   to derive W x L x H uniquely; simulation assumption required and must be marked as such).
leds:
  # NOTE: paper lists 4 LED positions; as printed, entries 1 and 3 are identical
  # (-0.4, 0.4, 1.35) which is almost certainly a transcription/OCR duplication in the
  # source PDF (entry 3 is presumably (0.4, -0.4, 1.35) by symmetry with entry 4 at
  # (-0.4,-0.4,1.35)). PAPER_AMBIGUITY: flagged, not silently "corrected" — implementing
  # agent must either find the paper's own code/erratum or explicitly document the
  # inferred value with this comment preserved.
  - id: 1
    position: [-0.4, 0.4, 1.35]     # meters, from paper Section IV
  - id: 2
    position: [0.4, 0.4, 1.35]      # meters, from paper Section IV
  - id: 3
    position: [-0.4, 0.4, 1.35]     # AS PRINTED IN PAPER — PAPER_AMBIGUITY, see note above
  - id: 4
    position: [-0.4, -0.4, 1.35]    # meters, from paper Section IV

communication:
  ifft_size: 256                     # N, paper Section IV
  modulation_bandwidth_hz: 20.0e6    # paper Section IV
  modulation_orders: [2, 4, 8, 16, 32, 64]   # paper Section IV — requires M3-COM-001 fix
  ber_max: 3.8e-3                    # paper Section IV

localization:
  frequency_plan:
    count: 5
    start_frequency_hz: 4.0e6        # paper Section IV
    spacing_hz: 0.2e6                # paper Section IV
  sampling:
    sample_rate_hz: NOT_SPECIFIED_IN_PAPER   # paper gives only the analog experimental
      # setup (oscilloscope-captured); a full_waveform simulation needs Fs > 2*4.8MHz
      # with real filter margin — recommend >= 20e6 Hz as a documented simulation
      # assumption, not a paper value.
```

`configs/default.yaml` remains the generic demo config; `paper_reference.yaml` is additive, not a replacement.

---

## 28. DEPENDENCY-AWARE REPAIR ORDER

```
PHASE A — Shared constants + units
    M2-PHY-005 (import SPEED_OF_LIGHT everywhere instead of re-literaling)

PHASE B — Module 1 geometry & state contract
    M1-ENV-003 (delegate Lambertian order to physics.lambertian)
    INT-001 (add room dims + per-LED beam_angle/lambertian_order to EnvironmentState)
    Decide & fix the degrees/radians contract on calculate_angles() (root cause of M2-PHY-001)
    M1-ENV-002 (remove duplicate H(0) from geometry.py/scene.py/state.py)
    M1-ENV-004 (remove dead Receiver physics methods)
    M1-ENV-001 (fix unreachable get_state() code)

PHASE C — Module 2 LOS optical physics
    M2-PHY-001 (apply the units fix at the physics_engine.py call site — should already be
                mostly resolved once Phase B's contract decision lands, but verify explicitly)
    M2-PHY-002 (consume per-LED beam_angle from EnvironmentState instead of hardcoding 60.0)
    M2-PHY-003 (consume per-LED orientation for NLOS instead of hardcoding [0,0,-1])
    INT-001 completion (consume room dims from EnvironmentState instead of hardcoding)

PHASE D — Module 2 noise + frequency response + multipath
    T-M2-005 (audit physics/reflection.py bounce-order math — currently VALIDATION GAP)
    T-M3-006 (audit communication/led_frequency_response.py — currently VALIDATION GAP)

PHASE E — Module 3 QAM/OFDM primitives
    M3-COM-001 (add 8-QAM/32-QAM support)
    Grade existing tests/test_qam.py, test_ofdm.py per Part 63

PHASE F — Module 3 physical channel integration
    T-M3-004 (audit channel_equalizer.py — VALIDATION GAP)
    T-M3-005 (audit communication/channel_interface.py — VALIDATION GAP)

PHASE G — Module 3 SNR/BER/rate consistency
    M3-COM-002 (fix missing sqrt in Eq.1 SNR)
    M3-COM-003 (rename delta to avoid delta/δ² collision)
    M3-COM-004 (BER length-mismatch should warn, not silently trim)

PHASE H — Module 4 transmitted/received localization signals
    (No fixes required — Eq.4-6 chain confirmed correct; add T-M4-001, T-M4-003 as
     regression locks before touching anything nearby)

PHASE I — Module 4 DPD/IQ chain
    T-M4-004, T-M4-005 (audit filters.py — VALIDATION GAP)
    M4-LOC-007 (phase-ambiguity large-jump test)

PHASE J — Module 4 Equation 16
    M4-LOC-008 (add explicit cross-file sign-convention documentation + T-M4-003 regression test)

PHASE K — Module 4 position solver/calibration
    T-M4-006 (audit calibration.py — VALIDATION GAP)
    M4-LOC-006 (source rx_bandwidth from config instead of hardcoding 50 MHz)

PHASE L — Cross-module integration
    T-INT-001, T-INT-002, T-INT-003 (full-chain regression tests)

PHASE M — Frontend/API alignment
    CFG-001 (verify Three.js Y-up vs. backend Z-up handling — VALIDATION GAP, unaudited)

PHASE N — Regression and paper validation
    CFG-004 (create configs/paper_reference.yaml)
    Level 10 paper-scenario reproduction test
```

**Rationale for reordering vs. the template's default phase list:** Module 1's state-contract fix (units, room dims, per-LED params) is pulled earlier (Phase B, before Phase C's physics fix) because Module 2's P0 fix cannot be verified as "done" without first knowing what unit contract `EnvironmentState` is supposed to expose — fixing the call site in isolation without fixing/documenting the source contract risks the same bug recurring the next time someone touches `geometry.py`.

---

## 29. REGRESSION RISKS

| Change | Risk |
|---|---|
| Fixing M2-PHY-001 (units) | Every existing numeric expectation in `tests/test_physics.py`, `test_module2_integration.py`, and any snapshot/demo output changes substantially (gains that were near-zero will become nonzero and vice versa). **Expected and required** — old "passing" tests were passing against wrong physics. |
| Removing `EnvironmentState.dc_gains` (M1-ENV-002) | `examples/demo_receiver_mobility.py`, `tests/test_simulation.py` read this field directly — must migrate to `PhysicsState.los_gains`. |
| Fixing M3-COM-002 (√ in SNR) | Any BER/rate values computed downstream of `compute_communication_snr` shift; regenerate expected values in `tests/test_ber.py`/`test_rate.py` if they depend on this function (needs confirmation — `channel_interface.py` for communication was a `VALIDATION GAP` in this pass and must be checked for whether it even calls this function yet). |
| Touching Eq.16 sign convention (M4-LOC-008) | **Do not "fix" the sign to match the paper literally in only one file** — `channel_interface.py` and `position_solver.py` must change together or not at all; `T-M4-003` exists specifically to catch a partial, well-intentioned but incorrect fix. |
| Adding room dims to `EnvironmentState` (INT-001) | Changes the dataclass's field list — any code constructing `EnvironmentState(...)` positionally (none currently observed; all construction sites use keyword args) or via `dataclasses.replace()` needs updating. |

---

## 30. ACCEPTANCE CRITERIA (by module)

**Module 1:** All coordinates use one canonical, documented degrees-or-radians convention with no ambiguity at the `EnvironmentState` boundary. `EnvironmentState` carries room dimensions and per-LED beam_angle/lambertian_order. No channel-gain-shaped computation exists anywhere under `environment/`. `VLCLSimulator.get_state()` and `.step()` produce physics-consistent output.

**Module 2:** `compute_los_dc_gain` receives correctly-unit-converted angles and produces gains matching hand-calculated reference cases to 1e-9 relative error. Room dims and per-LED beam_angle are sourced from `EnvironmentState`, not hardcoded. Multipath/reflection math independently re-derived and tested (currently a gap).

**Module 3:** SNR Eq.1 includes the square root and matches hand-calculated 2-LED cases. BER Eq.2 and Rate Eq.3 regression-pinned (already correct). 8-QAM/32-QAM supported. `channel_interface.py`/`channel_equalizer.py` audited (currently gaps) and confirmed to consume `PhysicsState` without re-deriving physics or double-applying noise.

**Module 4:** Ground-truth firewall enforced by a CI static check (`T-M4-002`), not just manual review. Eq.16 sign convention documented and regression-locked (`T-M4-003`). Filters and calibration audited (currently gaps).

---

## 31. DEFINITION OF DONE

All P0 and P1 issues in this document resolved and covered by a passing, non-trivial test (Part 63's "GOOD" classification — not shape-only, not overly-tolerant). All `VALIDATION GAP` items in Section 32 either closed (audited and found correct/incorrect with evidence) or explicitly re-scoped with a tracked follow-up ID. `configs/paper_reference.yaml` exists and a Level 10 end-to-end test against it passes within a documented tolerance. The Requirement Traceability Matrix (Section 33) shows no P0/P1 requirement without an associated test ID.

---

## 32. OPEN QUESTIONS / PAPER AMBIGUITIES / VALIDATION GAPS

**Paper ambiguities (cannot be resolved from the excerpt alone):**
1. LED position list in Section IV appears to contain a duplicate entry — see `configs/paper_reference.yaml` note in Section 27.
2. The paper's Eq. (5)/(6) `+ωτ` delay convention vs. the physically-standard `−ωτ` convention: the paper's own hardware description (non-LO differential measurement) is agnostic to this choice as long as it's applied consistently, so this is plausibly just the paper authors' own sign convention rather than an error — flagged for documentation, not correction.
3. `NOT_SPECIFIED_IN_PAPER`: exact room width/length/height (only volume given), exact LED optical power in watts, exact photodiode/APD responsivity and area (paper mentions APD hardware but the excerpt provided does not give its datasheet numbers).

**Validation gaps requiring follow-up before Module 5 (files inspected structurally but not algebraically re-derived in this pass):**
- `environment/mobility.py`, `environment/obstacle.py` (full intersection math), `environment/visualization.py`
- `physics/reflection.py` (NLOS bounce-order correctness), `physics/raytracer.py`, `physics/channel_estimator.py`
- `communication/channel_interface.py`, `communication/channel_equalizer.py`, `communication/led_frequency_response.py`, `communication/evm.py`, `communication/synchronization.py`, `communication/adc.py`
- `localization/filters.py` (Butterworth design correctness, zero-phase/group-delay handling), `localization/calibration.py` (shifting-error mitigation substance), `localization/validation.py`
- Frontend (`frontend/src/`) coordinate-convention consistency vs. backend (Three.js Y-up vs. backend Z-up) — `CFG-001`
- Existing test suite (`tests/*.py`) was enumerated but not individually graded GOOD/WEAK/MISLEADING/MISSING per Part 63 — required before Definition of Done.

These gaps are listed explicitly, per the task's own Rule 2 and Part 91, rather than guessed at or silently assumed correct.

---

## 33. REQUIREMENT TRACEABILITY MATRIX

| Requirement ID | Paper Reference | File(s) | Implementation Task | Test ID | Status |
|---|---|---|---|---|---|
| M2-PHY-001 | H(0) definition, Sec. II-B | physics/physics_engine.py | Fix units at call site / source contract | T-M2-001, T-INT-001 | OPEN — P0 |
| M1-ENV-001 | N/A | environment/simulator.py | Fix unreachable code | T-M1-001 | OPEN — P1 |
| M1-ENV-002 | H(0) definition | environment/geometry.py, scene.py, state.py | Remove duplicate gain calc | T-M1-002, T-INT-002 | OPEN — P0 |
| M1-ENV-003 | m definition | environment/led.py | Delegate to physics.lambertian | T-M1-003 | OPEN — P2 |
| M1-ENV-004 | N/A | environment/receiver.py | Remove dead physics methods | T-M1-004 | OPEN — P3 |
| M3-COM-002 | Eq. 1 | communication/snr.py | Add sqrt | T-M3-001 | OPEN — P1 |
| M3-COM-003 | Eq. 1 (δ²) | communication/snr.py | Rename delta param | T-M3-001 | OPEN — P2 |
| M3-COM-001 | Sec. IV (M-set) | communication/qam.py, ber.py | Add M=8,32 | T-M3-007 | OPEN — P2 |
| M4-LOC-008 | Eq. 5/6, 16 | localization/channel_interface.py, position_solver.py | Document + regression-lock sign convention | T-M4-003 | OPEN — P2 (documentation; math already correct) |
| INT-001 | N/A | environment/state.py, physics_engine.py, localization/engine.py | Propagate room dims | T-INT-003 | OPEN — P2 |
| M4-LOC-014 (ground-truth firewall) | Sec. II-C (A-DPDOA) | localization/position_solver.py, engine.py | **Already satisfied** — add CI enforcement | T-M4-002 | VERIFIED, enforcement test OPEN |

*(Extend this matrix with all remaining P2/P3 issue IDs from Section 21–22 before implementation begins; abbreviated here for readability.)*

---
