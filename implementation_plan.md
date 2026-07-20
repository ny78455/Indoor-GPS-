# REVISED IMPLEMENTATION PLAN — Modules 1–4 Audit & Repair
### Yang et al., IEEE Trans. Commun. 71(12) Dec. 2023

---

## Confirmed Bugs (Priority Order)

| ID | Priority | File(s) | Bug |
|---|---|---|---|
| M2-PHY-001 | **P0** | `physics/physics_engine.py:133–142` | Degrees passed as radians to `compute_los_dc_gain` — corrupts ALL physics |
| M1-ENV-002 | **P0** | `environment/geometry.py`, `scene.py`, `state.py` | Duplicate non-canonical H(0) in Module 1; `dc_gains` must be removed |
| M1-ENV-ANGLE-001 | **P0** | `environment/geometry.py`, `scene.py`, `physics_engine.py` | Angular unit ambiguity; root cause of M2-PHY-001 — fix atomically |
| M1-ENV-001 | **P1** | `environment/simulator.py:197–198` | Dead code after `return` in `get_state()` — physics never populated |
| M3-COM-002 | **P1** | `communication/snr.py:31` | Missing `√P` in Eq.(1) coherent sum |
| CFG-004 | **P1** | *(missing)* | No `configs/paper_reference.yaml` |
| M1-ENV-003 | **P2** | `environment/led.py:28–32` | Lambertian order re-implemented in Module 1 (must be removed entirely, not delegated) |
| M2-PHY-002 | **P2** | `physics/physics_engine.py:131` | `beam_angle=60.0` hardcoded; must come from `EnvironmentState.led_beam_angles` |
| M2-PHY-003 | **P2** | `physics/physics_engine.py:150` | `led_normal=[0,0,-1]` hardcoded for NLOS |
| INT-001 | **P2** | `environment/state.py`, `physics_engine.py`, `localization/engine.py` | Room dims not in `EnvironmentState`; hardcoded in 3 places |
| M3-COM-003 | **P2** | `communication/snr.py:10` | `delta` param name collides with paper's `δ²` noise symbol |
| M4-LOC-008 | **P2** | `localization/channel_interface.py`, `position_solver.py` | Sign convention undocumented; math is correct but fragile |
| M2-PHY-005 | **P3** | `physics_engine.py:170`, `position_solver.py:33` | Speed of light re-literaled instead of imported |
| M1-ENV-004 | **P3** | `environment/receiver.py:65–81` | Dead physics methods (`receive_signal`, `measure_snr`) |
| M3-COM-004 | **P3** | `communication/ber.py` | Silent truncation on BER length mismatch; must raise or warn with strict mode |

---

## Ownership Boundary (Non-Negotiable)

```
EnvironmentState  (Module 1: pure geometry)
  led_positions          ✅
  led_orientations       ✅
  led_beam_angles        ✅  ← primitive; Module 2 derives m from this
  room_dims              ✅
  distances              ✅
  incident_angles_rad    ✅  ← radians (after M1-ENV-ANGLE-001)
  irradiance_angles_rad  ✅  ← radians
  los_matrix             ✅
  dc_gains               ❌  REMOVED (M1-ENV-002)
  led_lambertian_orders  ❌  NOT ADDED (derived in Module 2 only)
        ↓
PhysicsEngine.compute(EnvironmentState)  (Module 2: sole gain/power/SNR owner)
  H(0) via compute_los_dc_gain()         ✅
  lambertian_order derived from beam_angle ✅
  los_gains, nlos_gains, total_gains     ✅
  received_powers, noise, snrs           ✅
        ├──────────────────────────┐
        ▼                          ▼
CommunicationEngine            LocalizationEngine
  Eq.(1),(2),(3)                 Eq.(4)–(16)
  consumes PhysicsState          consumes PhysicsState
  never re-derives H(0)          never reads receiver_position
                                 except into true_position_for_evaluation_only
```

---

## Angular Unit Contract (applies everywhere after Phase B)

```
INTERNAL COMPUTATION  →  radians (float64)
CONFIGURATION / UI    →  may use degrees
DISPLAY               →  may convert rad→deg for output
```

Conversion occurs **exactly once** at the environment boundary.

---

## Revised Execution Phases

---

### PHASE A — Scientific constants + paper_reference.yaml skeleton

**Requirements:** `M2-PHY-005`, `CFG-004` (skeleton)

**Files:**
- `physics/physics_engine.py`: import `SPEED_OF_LIGHT` from `constants.py`, remove literal
- `localization/position_solver.py`: import `SPEED_OF_LIGHT` from `constants.py`, remove literal
- `configs/paper_reference.yaml` *(new)*: create with all Section IV parameters and provenance comments; not yet used for full experiments (that is Phase N)

**paper_reference.yaml must include:**
```yaml
# SOURCE: Yang et al., IEEE Trans. Commun. 71(12), Dec. 2023
# All values from Section IV unless noted NOT_IN_PAPER
room:
  # NOT_IN_PAPER: paper gives coverage volume ~22.5 m³, not explicit W×L×H
  width: 5.0
  length: 5.0
  height: 3.0

leds:
  # NOTE: paper LED-position list in Section IV appears to contain a
  # duplicate entry for LED 2 — (−0.4,0.4,1.35) listed twice.
  # Using (0.4,0.4,1.35) for LED 2 as most likely intended.
  # PAPER_AMBIGUITY: needs erratum or authors' code to resolve definitively.
  - id: 1; position: [-0.4,  0.4, 1.35]
  - id: 2; position: [ 0.4,  0.4, 1.35]  # assumed
  - id: 3; position: [-0.4, -0.4, 1.35]
  - id: 4; position: [-0.4, -0.4, 1.35]  # as printed

communication:
  ifft_size: 256          # Section IV
  modulation_bandwidth: 20.0e6   # Section IV
  ber_max: 3.8e-3         # Section IV

localization:
  tone_count: 5
  start_frequency: 4.0e6  # Section IV
  spacing: 0.2e6           # Section IV
  # NOT_IN_PAPER: sample_rate; recommend ≥20 MHz for simulation margin
```

**Tests:** none yet; creates the reference fixture for Phase N.

**Exit gate:** `SPEED_OF_LIGHT` appears in `constants.py` only; `grep -r "299792458" backend/VLCL_AI` returns zero hits outside `constants.py`. `paper_reference.yaml` exists with provenance comments.

---

### PHASE B — Module 1 ownership cleanup + atomic angle migration

**Requirements:** `M1-ENV-ANGLE-001`, `M1-ENV-002`, `M1-ENV-003`, `M1-ENV-004`, `M1-ENV-001`, `INT-001` (partial)

**Key rule from user corrections:**
> Do NOT import Module 2 (physics) into Module 1. Remove Lambertian computation from `led.py` entirely — do not delegate to `physics.lambertian`. Module 1 stores only the primitive `beam_angle`; Module 2 derives `m` from it.

#### B.1 — M1-ENV-ANGLE-001 (atomic, all-or-nothing)

Change `geometry.py::calculate_angles()` to return **(φ_rad, ψ_rad)** instead of degrees.

Must update simultaneously in **one commit**:

| File | Change |
|---|---|
| `environment/geometry.py` | Return `(np.arccos(cos_phi), np.arccos(cos_psi))` — no `np.degrees()` |
| `environment/scene.py` | FOV check changes from `abs(psi) <= self.receiver.fov` to `abs(psi) <= np.radians(self.receiver.fov)` |
| `environment/state.py` | Rename fields: `incident_angles` → `incident_angles_rad`, `irradiance_angles` → `irradiance_angles_rad`; update docstring |
| `physics/physics_engine.py` | Remove any surviving `np.radians(inc_ang)` call — angles now arrive in radians |
| All tests | Update expected values to radians |

**Analytically obvious test cases for T-M1-ANGLE:**
```
LED directly above receiver → φ=0.0 rad, ψ=0.0 rad
45° geometry             → φ=π/4, ψ=π/4 (±tol 1e-9)
Exactly at FOV boundary  → must be accepted (ψ == FOV_rad)
Just outside FOV         → must be rejected (ψ = FOV_rad + ε)
```

#### B.2 — M1-ENV-002 (remove duplicate H(0))

- Remove `calculate_lambertian_dc_gain()` from `geometry.py` entirely
- Remove `dc_gains` computation from `scene.py::get_geometric_metrics()`
- Remove `dc_gains` field from `EnvironmentState`
- Remove `dc_gains=metrics["dc_gains"]` from `simulator.py::step()` and `get_state()`
- **Migrate all consumers in this same phase:**
  - `examples/demo_receiver_mobility.py`: replace `state.dc_gains` with `physics_state.los_gains`
  - `tests/test_simulation.py`: same migration
  - Frontend API (`server.ts`): if `dc_gains` is serialized in any response, remove or replace with `PhysicsState` field

#### B.3 — M1-ENV-003 (remove lambertian calculation from LED class)

- Remove lines 28–32 from `environment/led.py` (the inline `m = -ln(2)/ln(cos(θ))`)
- `LED` stores only `beam_angle: float` (the primitive)
- No import of `physics.lambertian` into Module 1 (that direction is forbidden)
- `lambertian_order()` in `physics/lambertian.py` remains the single canonical implementation

#### B.4 — INT-001 (partial: add fields to EnvironmentState)

Add to `EnvironmentState`:
```python
room_dims: List[float]           # [width, length, height] in metres
led_orientations: Dict[int, List[float]]   # LED normal vectors (already in LED obj)
led_beam_angles: Dict[int, float]          # semi-angle at half power (degrees — config primitive)
```

**Do NOT add `led_lambertian_orders`** — that is a derived optical quantity owned by Module 2.

Update `simulator.py::step()` and `get_state()` to populate these fields from `self.scene`.

#### B.5 — M1-ENV-004 (remove dead physics from Receiver)

Remove from `environment/receiver.py`:
- `receive_signal()` (lines 65–74)
- `measure_snr()` (lines 76–81)

#### B.6 — M1-ENV-001 (fix get_state() dead code)

The dead code in `get_state()` (lines 197–198) performs Module 2 computation (`self.physics.compute(state)`). Per user correction:

> Do NOT move that code before the `return`. That would recreate Module 1/2 coupling.

**Fix:** simply delete lines 197–198. `get_state()` returns pure geometry/environment state only. Callers that need physics must explicitly call `PhysicsEngine.compute(env_state)` themselves.

**Tests required before Phase C:**
- `T-M1-001`: `get_state()` returns an `EnvironmentState` with no `dc_gains` field and no `physics` field populated by Module 1
- `T-M1-002`: `grep -r "calculate_lambertian_dc_gain\|dc_gains" backend/VLCL_AI` → zero hits
- `T-M1-003`: `LED.__init__` stores `beam_angle` but does not compute `lambertian_order`
- `T-M1-004`: `Receiver` class has no `receive_signal` or `measure_snr` methods
- `T-M1-ANGLE`: Four analytically-obvious angle cases pass to 1e-9 tolerance

**Phase B exit gate:** All five tests pass. `grep` confirms no `dc_gains` or `calculate_lambertian_dc_gain` anywhere in the repo.

---

### PHASE C — Module 2 LOS optical physics

**Requirements:** `M2-PHY-001`, `M2-PHY-002`, `M2-PHY-003`, `INT-001` (complete)

#### C.1 — M2-PHY-001 verification

After Phase B, `incident_angles_rad` and `irradiance_angles_rad` in `EnvironmentState` are already in radians. Verify the `compute_los_dc_gain` call site in `physics_engine.py` passes them directly with no unit conversion (since they now arrive correctly). If any surviving `np.radians()` wrapper exists at the call site, remove it (double-conversion would re-introduce the bug in the opposite direction).

#### C.2 — M2-PHY-002

Replace `beam_angle = 60.0` (hardcoded) with:
```python
beam_angle = env_state.led_beam_angles.get(led_id, 60.0)
```
Module 2 derives `m` internally: `m = lambertian_order(beam_angle)`.

#### C.3 — M2-PHY-003

Replace `led_normal=np.array([0.0, 0.0, -1.0])` with:
```python
led_normal = np.array(env_state.led_orientations.get(led_id, [0.0, 0.0, -1.0]))
```

**Tilted-LED regression test (T-M2-TILT):**
```
LED A: normal=[0,0,-1], position=[2.5, 2.5, 3.0]
LED B: 30° tilt, same position, same receiver
Result: gain_A ≠ gain_B, difference is predictable from Lambertian cos^m(φ)
```

#### C.4 — INT-001 completion

Replace hardcoded `room_dims = [5.0, 5.0, 3.0]` in `physics_engine.py` and `localization/engine.py` with `env_state.room_dims`.

**Tests required before Phase D:**
- `T-M2-001`: Synthetic hand-computed H(0) case — LED directly above receiver at distance d, φ=0, ψ=0: H(0) = (m+1)·A/(2π·d²)·g(ψ) matches to 1e-9 relative error
- `T-M2-002`: FOV gate — angle just outside FOV returns H(0)=0.0 exactly
- `T-M2-003`: Two-LED received power sums correctly
- `T-M2-TILT`: Tilted vs vertical LED produces different gains
- `T-INT-001`: `EnvironmentState` angle fields are in radians; `PhysicsEngine.compute()` consumes them without any `np.radians()` wrapping

**Phase C exit gate:** `T-M2-001` passes to 1e-9. No `beam_angle = 60.0` or `[0.0, 0.0, -1.0]` literals remain in `physics_engine.py`.

---

### PHASE D — Module 2 extended physics audit

**Requirements:** Audit `physics/reflection.py`, `communication/led_frequency_response.py`

**STOP GATE — required before Phase E:**

For each audited component, produce a classification:

| Component | Classification | Evidence |
|---|---|---|
| `physics/reflection.py` | PASS / FIX_REQUIRED / NOT_PAPER_REQUIRED / BLOCKED_BY_AMBIGUITY | Derivation notes |
| `communication/led_frequency_response.py` | same | same |

**If any component is classified `FIX_REQUIRED` with severity P0 or P1:** STOP. Create a new repair task with a fresh ID. Do not proceed to Phase E until that repair is complete.

If both components pass or are classified `NOT_PAPER_REQUIRED`, proceed.

---

### PHASE E — Modulation-order fidelity audit (NOT automatic implementation)

**Requirements:** `M3-COM-001` (audit gate, not auto-code)

**This is an audit gate, not an automatic coding task.** Per user correction:

> Do not implement 8/32-QAM unless the paper explicitly requires non-square QAM. The BER formula's √M terms assume square constellations; applying it to cross-8-QAM or cross-32-QAM would introduce a new scientific inconsistency.

**Audit steps:**

1. Extract modulation orders from: paper text, simulation parameters, figures, experimental setup table
2. Determine whether only square M-QAM is used (M ∈ {4, 16, 64, 256}) or whether 8/32 are explicitly required
3. If **only square QAM**: support exactly {4, 16, 64} (+ BPSK if needed). Remove 256-QAM if it adds implementation surface without paper backing. Do not add 8 or 32.
4. If **8/32-QAM explicitly required**: implement constellation-specific mapping AND use constellation-appropriate BER models. Never evaluate square-QAM analytical BER for a non-square constellation.

**Outcome of audit goes into IMPLEMENTATION_STATUS.md with evidence before any code is written.**

**STOP GATE:** If 8/32-QAM is found to be required, stop, create `M3-COM-001-FIX` task with correct BER model derivation, and get review before implementing.

---

### PHASE F — Module 3 physical-channel integration audit

**Requirements:** Audit `communication/channel_interface.py`, `communication/channel_equalizer.py`

**STOP GATE — required before Phase G:**

For each file, verify and classify:

| Question | Pass Criterion |
|---|---|
| Does `channel_interface.py` consume `PhysicsState` without re-deriving H(0)? | Must not call any gain formula; must read from `physics_state` fields only |
| Is channel applied exactly once (no double-convolution)? | Trace signal from TX to RX; noise must not be added twice |
| Does `channel_equalizer.py` implement ZF and MMSE correctly? | Audit inverse formula; confirm no divide-by-zero on deep fades |

If `FIX_REQUIRED` with P0/P1: STOP before Phase G.

---

### PHASE G — Module 3 SNR / BER / rate

**Requirements:** `M3-COM-002`, `M3-COM-003`, `M3-COM-004`

#### G.1 — M3-COM-002: Fix Eq.(1) SNR

**Prerequisite before writing code:**

Trace `subcarrier_powers` from allocation through to `compute_communication_snr()`:
- What does the value represent? True electrical power P, or amplitude √P?
- Are units verified? (P in Watts, not dBm)
- Does pre-equalization upstream already apply √P?

Only after tracing apply the fix:
```python
# Paper Eq.(1): γ = δ²μ²(Σ_i √P_{n,i} · H_{i,n,k})² / σ²
combined_optical = np.sum(np.sqrt(subcarrier_powers) * gains_transposed, axis=1)
```

**Golden test cases (T-M3-001):**

One LED:
```
γ = μ² · P · H² / σ²
```

Two LEDs:
```
γ = μ² · (√P₁·H₁ + √P₂·H₂)² / σ²
```

These must match the formula analytically to 1e-9 relative error.

#### G.2 — M3-COM-003: Rename parameter

Rename `delta` parameter in `communication/snr.py` to a name reflecting physical semantics:
- If it represents the paper's `δ²` noise denominator → name it `noise_power` or `noise_variance`
- If it is a dimensionless normalization constant → name it `normalization_factor`
- Do NOT rename to `scaling_factor` (still ambiguous)

Trace the actual physical meaning before renaming.

#### G.3 — M3-COM-004: Strict BER validation mode

Replace silent truncation with two modes:

```python
def compute_empirical(self, tx_bits, rx_bits, strict: bool = True):
    if len(tx_bits) != len(rx_bits):
        if strict:
            raise VLCLCommunicationError(
                f"BER bit-length mismatch: TX={len(tx_bits)}, RX={len(rx_bits)}. "
                "Indicates synchronization, framing, CP, or QAM grouping error."
            )
        else:
            warnings.warn(f"BER bit-length mismatch: TX={len(tx_bits)}, RX={len(rx_bits)}. "
                          "Trimming to shorter length.", VLCLWarning)
            min_len = min(len(tx_bits), len(rx_bits))
            tx_bits, rx_bits = tx_bits[:min_len], rx_bits[:min_len]
```

Default for tests and paper experiments: `strict=True`.

**Tests required before Phase H:**
- `T-M3-001`: Eq.(1) one-LED and two-LED golden cases pass to 1e-9
- `T-M3-002`: BER regression pin (already correct — pin current values post-SNR fix)
- `T-M3-003`: Rate regression pin (already correct)
- `T-M3-004`: BER mismatch raises `VLCLCommunicationError` in strict mode

---

### PHASE H — Module 4 basic signal regression locks

**Requirements:** `T-M4-001` through `T-M4-008`

Per user correction, "no code fix required" is insufficient. A full synthetic Eq.(4)–(16) validation chain is required before Phase I.

**Synthetic validation chain (all using known analytical inputs):**

| Test ID | Input | Expected Output | Validates |
|---|---|---|---|
| T-M4-001 | Known propagation delays τ → generate signals | Received phasors have phase `−ωτ` | Eq.(4)–(5)/(6) delay convention |
| T-M4-002 | `s₁ × s₂` (multiply two tones) | Difference-frequency component at `Δf` | Eq.(7)–(9) |
| T-M4-003 | BPF applied to product | `D_i` phase matches expected `ω_{i+1}τ_{i+1} − ω_i τ_i` (with sign) | Eq.(9) output |
| T-M4-004 | `D₁ × D₂*` dual differential | Phase = `−(ω₁τ₁ + ω₃τ₃ − 2ω₂τ₂)` | Eq.(13)–(15) |
| T-M4-005 | IQ extraction → atan2 | Phase angle matches expected to 1e-6 rad | Eq.(10)–(12) |
| T-M4-006 | Eq.(16) synthetic known phases | Exact distance differences recovered to 1e-9 m | Eq.(16) matrix |
| T-M4-007 | Known distance differences → nonlinear solver | Receiver position recovered to 1e-6 m (noiseless) | PositionSolver |
| T-M4-008 | Static import check | `PositionSolver` and `DistanceDifferenceSolver` have zero code paths referencing `EnvironmentState.receiver_position` | Ground-truth firewall |

**T-M4-008 implementation:**
```python
import ast, inspect
src = inspect.getsource(PositionSolver)
tree = ast.parse(src)
assert "receiver_position" not in ast.dump(tree), "Ground-truth leakage detected in PositionSolver"
```

**Sign-convention invariant test (part of T-M4-004):**

Define the canonical convention explicitly in a docstring:
```
Convention: received signal phase = −ω·τ  (physical delay)
Paper Eq.(5)/(6) uses +ω·τ — a notation difference, not a physics difference.
position_solver.py compensates with A = −A·(2π/c).
Net effect: A_code · Δd = θ_measured ↔ A_paper · Δd = θ_paper. Correct.
If you change the sign in channel_interface.py, you MUST change it in position_solver.py simultaneously.
This test will fail if only one side is changed.
```

The test must verify: if `channel_interface.py` sign is flipped, `T-M4-006` fails. (Implemented as a parameterized test with a deliberately-wrong sign.)

---

### PHASE I — A-DPDOA DSP chain audit

**Requirements:** Audit `localization/filters.py`, `M4-LOC-007`

Audit `filters.py` Butterworth design:
- Verify order, cutoff frequency, zero-phase option group-delay handling
- Classify: PASS / FIX_REQUIRED

**M4-LOC-007** (phase ambiguity large-jump test):
- Simulate a receiver position change that causes a phase jump > 2π between frames
- Verify `PhaseUnwrapper` correctly resolves it (or documents that it cannot and marks LOW_CONFIDENCE)

---

### PHASE J — Equation 16 sign convention: documentation + invariant test

**Requirements:** `M4-LOC-008`

Add to both files an explicit comment block:

In `localization/channel_interface.py`:
```python
# SIGN CONVENTION (cross-ref: position_solver.py::_build_coefficient_matrix)
# This file applies delay as: received_phase = −ω·τ  (standard physics: s(t−τ) ↔ e^{-jωτ})
# Paper Eq.(5)/(6) writes phase as +ω·τ — a notation difference, not a physics error.
# position_solver.py compensates with an explicit negation of the A matrix.
# Both files must use the SAME convention. Changing only one will break localization.
# Protected by regression test T-M4-004.
```

In `localization/position_solver.py`:
```python
# SIGN CONVENTION (cross-ref: channel_interface.py::apply_channel)
# θ_measured = −θ_paper  (because channel_interface uses −ωτ convention)
# A_code = −A_paper·(2π/c)  (this negation here)
# Net: A_code·Δd = θ_measured  ↔  A_paper·Δd = θ_paper  ✓ CORRECT
# Do NOT "fix" this sign to match the paper literally without changing channel_interface.py.
# Protected by regression test T-M4-004 / T-M4-006.
```

---

### PHASE K — Module 4 position solver + calibration

**Requirements:** Audit `localization/calibration.py`, `M4-LOC-006`

**Calibration audit:** Verify `LocalizationCalibrator`/`ShiftingErrorMitigator` implements actual per-LED/per-tone bias calibration (not a generic smoothing filter). Must confirm it reads `calibration.phase_bias_rad`/`delay_bias_s` from config.

**M4-LOC-006:** Source `rx_bandwidth` from config in `localization/channel_interface.py` instead of hardcoded `50.0e6`.

---

### PHASE L — Cross-module integration tests

**Requirements:** `T-INT-001`, `T-INT-002`, `T-INT-003`

| Test ID | Pipeline | Pass Criterion |
|---|---|---|
| T-INT-001 | Module 1 boundary | `EnvironmentState` angle fields are in radians; no `dc_gains` field present |
| T-INT-002 | Module 1→2→3 | Noiseless AWGN channel: BER ≈ 0 at high SNR; BER curve monotonically improves with SNR |
| T-INT-003 | Module 1→2→4 | Noiseless: receiver position recovered to <0.01 m from known synthetic geometry |

---

### PHASE M — Frontend/API coordinate alignment

**Requirements:** `CFG-001`

Audit `frontend/src/components/ThreeCanvas.tsx` and `backend/server.ts` API serialization:
- Backend uses Z-up (Z = height); Three.js uses Y-up
- Verify `ThreeCanvas.tsx` coordinate swap: Python `[x, y, z]` → Three.js `[x, z, y]`
- If mismatch found: create `CFG-001-FIX` task

---

### PHASE N — Paper-reference experiments + full regression

**Requirements:** `CFG-004` (complete), Level 10 reproduction test

Use `configs/paper_reference.yaml` (created in Phase A) for all experiments.

**Final acceptance gate — ALL must be true:**

```
P0 unresolved           = 0
P1 unresolved           = 0

Paper Eq.(1) validated  ✅  (T-M3-001)
Paper Eq.(2) validated  ✅  (T-M3-002 — already correct; regression-pinned)
Paper Eq.(3) validated  ✅  (T-M3-003 — already correct; regression-pinned)
Paper Eq.(4)–(16) chain ✅  (T-M4-001 through T-M4-008)

No ground-truth leakage ✅  (T-M4-008 static check)
No degree/radian ambiguity ✅  (T-M1-ANGLE, T-INT-001)
No duplicate H(0)       ✅  (grep: zero hits on calculate_lambertian_dc_gain)
No Module 1 physics     ✅  (grep: zero hits on gain computation outside physics/)
Module 2 applied once   ✅  (T-INT-002 channel-trace)
No dB/linear confusion  ✅  (SNR field naming audit)

Module 3 noiseless BER  ≈ 0  at reference geometry
Module 4 synthetic position recovery < 0.01 m (noiseless)

paper_reference.yaml complete with provenance comments
All validation gaps from spec Section 32 either closed or explicitly re-filed P2/P3

Full regression suite passes
```

**MODULES_1_TO_4_STATUS** updated to `VALIDATED` only when all gates pass.

---

## Requirement Traceability Matrix (Complete)

| Req ID | Priority | Paper Ref | Files | Test IDs | Status |
|---|---|---|---|---|---|
| M2-PHY-001 | P0 | H(0), Sec. II-B | `physics_engine.py` | T-M2-001, T-INT-001 | OPEN |
| M1-ENV-ANGLE-001 | P0 | H(0) units | `geometry.py`, `scene.py`, `physics_engine.py` | T-M1-ANGLE, T-INT-001 | OPEN |
| M1-ENV-002 | P0 | H(0) duplicate | `geometry.py`, `scene.py`, `state.py` | T-M1-002 (grep) | OPEN |
| M1-ENV-001 | P1 | N/A | `simulator.py` | T-M1-001 | OPEN |
| M3-COM-002 | P1 | Eq.(1) | `communication/snr.py` | T-M3-001 | OPEN |
| CFG-004 | P1 | Sec. IV | `configs/paper_reference.yaml` | Phase N Level-10 | OPEN |
| M1-ENV-003 | P2 | m definition | `environment/led.py` | T-M1-003 | OPEN |
| M2-PHY-002 | P2 | H(0) | `physics_engine.py` | T-M2-001 | OPEN |
| M2-PHY-003 | P2 | H(0) NLOS | `physics_engine.py` | T-M2-TILT | OPEN |
| INT-001 | P2 | N/A | `state.py`, `physics_engine.py`, `localization/engine.py` | T-INT-003 | OPEN |
| M3-COM-003 | P2 | Eq.(1) δ² | `communication/snr.py` | T-M3-001 | OPEN |
| M3-COM-001 | P2 | Sec. IV M-set | `qam.py`, `ber.py` | Phase E audit gate | OPEN (audit) |
| M4-LOC-008 | P2 | Eq.(5)/(6),(16) | `channel_interface.py`, `position_solver.py` | T-M4-004, T-M4-006 | OPEN |
| M2-PHY-005 | P3 | N/A | `physics_engine.py`, `position_solver.py` | grep check | OPEN |
| M1-ENV-004 | P3 | N/A | `environment/receiver.py` | T-M1-004 | OPEN |
| M3-COM-004 | P3 | N/A | `communication/ber.py` | T-M3-004 | OPEN |
| M4-LOC-006 | P2 | N/A | `localization/channel_interface.py` | T-M4-001 | OPEN |
| M4-LOC-007 | P2 | Phase unwrap | `localization/phase_estimator.py` | T-M4-007 | OPEN |
| M4-LOC-014 | VERIFIED | Sec. II-C | `position_solver.py`, `engine.py` | T-M4-008 | VERIFIED — CI lock needed |

---

## Stop Conditions (Hard Rules)

1. If fixing M2-PHY-001 does not converge `T-M2-001` to 1e-9 after the units fix → second undiscovered bug; stop and re-audit.
2. If any Phase D/F audit component is `FIX_REQUIRED` P0/P1 → stop current phase; repair first.
3. If T-M4-008 (ground-truth firewall) ever fails at any phase → hard stop; no other P0/P1 fix justifies reintroducing leakage.
4. If Phase E audit finds 8/32-QAM is required → stop; derive constellation-appropriate BER model; do not silently apply square-QAM formula to non-square constellation.
5. If sign in either `channel_interface.py` or `position_solver.py` is changed without changing the other → T-M4-004 must catch this; if it doesn't, the test itself is broken.
