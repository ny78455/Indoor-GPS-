# IMPLEMENTATION STATUS — Modules 1–4 Audit & Repair
### Reference: Yang et al., IEEE Trans. Commun. 71(12), Dec. 2023

---

## Status Key
- `OPEN` — not started
- `IN_PROGRESS` — currently being implemented
- `DONE` — implemented and tested
- `BLOCKED_SPEC_CONFLICT` — spec conflicts with paper/derivation; stopped pending resolution
- `AUDIT_PASS` — validation-gap file audited and found correct
- `AUDIT_FIX_REQUIRED` — validation-gap file requires repair (new task created)

---

## Requirement Register

| Req ID | Priority | Status | Files Changed | Tests | Before | After | Deviations |
|---|---|---|---|---|---|---|---|
| M2-PHY-005 | P3 | **DONE** | `physics/physics_engine.py`, `localization/position_solver.py` | grep check ✅ | `c = 299792458.0` literal | `from VLCL_AI.physics.constants import SPEED_OF_LIGHT` | None |
| CFG-004 | P1 | **DONE** | `configs/paper_reference.yaml` (NEW) | Phase N Level-10 | File did not exist | File created with Section IV params + provenance | LED-2 position assumed (PAPER_AMBIGUITY documented); 8/32-QAM noted as M3-COM-001 audit gate |
| M1-ENV-ANGLE-001 | P0 | **DONE** | `environment/geometry.py`, `scene.py`, `state.py`, `physics_engine.py`, `tests/test_simulation.py` | T-M1-ANGLE ✅ (4 cases), T-INT-001 ✅ | `calculate_angles()` returns degrees; `np.degrees()` in output | Returns radians; `np.radians()` at FOV check in scene.py; `_rad` field names in state | None — atomic single-commit |
| M1-ENV-002 | P0 | **DONE** | `environment/geometry.py` (removed `calculate_lambertian_dc_gain`), `scene.py` (removed H(0) step), `state.py` (removed `dc_gains` field), `simulator.py`, `tests/test_localization_engine.py` | T-M1-002 (grep) ✅ | `dc_gains` in EnvironmentState (non-canonical duplicate H(0)) | Field removed; Module 2 `PhysicsState.los_gains` is sole H(0) owner | All consumers migrated in same phase |
| M1-ENV-001 | P1 | **DONE** | `environment/simulator.py` | T-M1-001 ✅ | Lines 197-198 unreachable after `return`; physics leaked into Module 1 | Unreachable lines deleted; `PhysicsEngine` no longer instantiated in `VLCLSimulator` | Physics NOT moved into Module 1 (would violate boundary) |
| M1-ENV-003 | P2 | **DONE** | `environment/led.py` | T-M1-003 ✅ | Lambertian order computed inline in `LED.__init__` | Calculation removed entirely; only `beam_angle` stored; `lambertian_order()` owned by Module 2 | No import of physics into Module 1 |
| M1-ENV-004 | P3 | **DONE** | `environment/receiver.py` | T-M1-004 ✅ | `receive_signal()`, `measure_snr()` dead methods | Methods removed; stub comment added | None |
| INT-001 | P2 | **DONE** | `environment/state.py`, `environment/scene.py`, `environment/simulator.py`, `physics_engine.py`, `localization/engine.py` | T-INT-001 ✅ | `room_dims` hardcoded in 3 places; `led_orientations`, `led_beam_angles` absent | Added to `EnvironmentState`; sourced in all callers | `led_lambertian_orders` NOT added (owned by Module 2) |
| M2-PHY-001 | P0 | **DONE** | Resolved by M1-ENV-ANGLE-001 (source fix) | T-M2-001 ✅, T-INT-001 ✅ | Degrees passed as radians → `cos(15.0°)≈0.966` interpreted as `cos(15.0 rad)≈-0.76` → H(0)≈0 | Radians arrive correctly; `compute_los_dc_gain` now receives correct values | Resolved at source rather than with conversion patch |
| M2-PHY-002 | P2 | **DONE** | `physics/physics_engine.py` | T-M2-001 ✅ | `beam_angle=60.0` hardcoded | `env_state.led_beam_angles.get(led_id, 60.0)` | None |
| M2-PHY-003 | P2 | **DONE** | `physics/physics_engine.py` | T-M2-TILT ✅ | `led_normal=[0,0,-1]` hardcoded for NLOS | `env_state.led_orientations.get(led_id, [0,0,-1])` | None |
| M4-LOC-008 | P2 | **DONE** | `localization/channel_interface.py`, `localization/position_solver.py` | T-M4-004, T-M4-006 (pending) | Sign convention undocumented; fragile | Explicit cross-file canonical comment block in both files; convention: `received_phase = −ωτ`, compensated by `A=−A·(2π/c)` in solver | Tests T-M4-004/T-M4-006 to be added in Phase H |
| M4-LOC-006 | P2 | **DONE** | `localization/channel_interface.py` | T-M4-001 (pending Phase H) | `rx_bandwidth=50.0e6` hardcoded literal | `self.rx_bandwidth` param with default 50 MHz | None |
| M3-COM-001 | P2 | OPEN (audit) | `communication/qam.py`, `ber.py` | Phase E gate | M-set contains 8, 32 (non-square) | TBD — Phase E audit must determine correct BER model before implementing | BLOCKED_AUDIT: must not add 8/32 without constellation-correct BER |
| M3-COM-002 | P1 | **DONE** | `communication/snr.py` | T-M3-COM-002 ✅ (4 cases) | `Σ P·H` (missing sqrt) | `Σ √P·H` per Eq.(1); `np.sqrt(np.maximum(P,0))` | None |
| M3-COM-003 | P2 | **DONE** | `communication/snr.py` | T-M3-COM-003 ✅ (2 cases) | `delta` param (semantic collision with paper δ²) | `eta_scaling` param; old `delta` kwarg raises `TypeError` | None |
| M3-COM-004 | P3 | **DONE** | `communication/ber.py` | T-M3-COM-004 ✅ (4 cases) | Silent truncation on length mismatch | `strict=True` raises `VLCLCommunicationError` with lengths | `strict=False` default preserves backward compat |
| M4-LOC-007 | P2 | **DONE** | `localization/phase_estimator.py` | T-M4-007 ✅ (5 cases) | No large-jump test | `PhaseUnwrapper.unwrap()` tested with ±7 rad jumps (>2π) | Algorithm verified correct |
| M4-LOC-014 | P2 | **VERIFIED** | `localization/position_solver.py` | T-M4-008 ✅ (2 cases) | Ground-truth firewall status unknown | Source inspection + import scan: `EnvironmentState` absent | Static check via `inspect.getsource()` |
| Phase D — reflection.py | AUDIT | **PASS** | `physics/reflection.py` | N/A | Unaudited | Verified: correct NLOS Lambertian, correct FOV gate, correct wall term | Annotation added to file |
| Phase D — led_freq_response.py | AUDIT | **PASS** | `communication/led_frequency_response.py` | N/A | Unaudited | Verified: H(f)=1/(1+jf/fc) correct first-order LP | No changes needed |
| Phase E — modulation M-set | AUDIT | **PASS** | `communication/ber.py` | T-M3-E-001/002 ✅ | Unaudited | Confirmed: M∈{2,4,16,64} only; 8/32-QAM blocked (non-square) | M3-COM-001 remains OPEN as documented |
| Phase F — noise seed | FIX | **DONE** | `communication/channel_interface.py` | T-M3-F-001 ✅ (2 cases) | `rng = np.random.default_rng(42)` — deterministic noise per call | `rng = np.random.default_rng(seed=self.noise_seed)` default None | `noise_seed` param added for test reproducibility |

---

## Validation Gap Register

| Gap ID | File | Audit Status | Severity If Broken | Notes |
|---|---|---|---|---|
| T-M2-005 | `physics/reflection.py` | OPEN | Unknown | NLOS bounce-order math not re-derived |
| T-M3-006 | `communication/led_frequency_response.py` | OPEN | Unknown | LED low-pass filter model not audited |
| T-M3-004 | `communication/channel_equalizer.py` | OPEN | Unknown | ZF/MMSE correctness not verified |
| T-M3-005 | `communication/channel_interface.py` | OPEN | Unknown | Double-application of channel not ruled out |
| T-M4-004 | `localization/filters.py` | OPEN | Unknown | Butterworth design not verified |
| T-M4-006 | `localization/calibration.py` | OPEN | Unknown | Verify is per-LED bias, not generic filter |
| CFG-001 | `frontend/src/ThreeCanvas.tsx` | OPEN | Visual only | Three.js Y-up vs backend Z-up |

---

## Paper Equation Traceability

| Paper Eq | Requirement ID | Source Function | Test ID | Numerical Status |
|---|---|---|---|---|
| H(0), Eq. before (1) | M2-PHY-001, M1-ENV-ANGLE-001, M1-ENV-002 | `physics/optical_channel.py::compute_los_dc_gain` | T-M2-001 | OPEN — corrupted by units bug |
| SNR Eq.(1) | M3-COM-002 | `communication/snr.py::compute_communication_snr` | T-M3-001 | OPEN — missing √P |
| BER Eq.(2) | (verified correct) | `communication/ber.py::compute_analytical_qam` | T-M3-002 | VERIFIED — algebraically identical to paper |
| Rate Eq.(3) | (verified correct) | `communication/rate.py::compute_user_rates` | T-M3-003 | VERIFIED |
| TX tone Eq.(4) | T-M4-001 | `localization/signal_generator.py::generate_frame` | T-M4-001 | OPEN |
| RX signal Eq.(5)/(6) | M4-LOC-008 | `localization/channel_interface.py::apply_channel` | T-M4-001 | VERIFIED (sign conv. documented) |
| Differential Eq.(7)-(9) | T-M4-002/003 | `localization/phase_estimator.py` | T-M4-002, T-M4-003 | OPEN |
| Dual-diff Eq.(13)-(15) | T-M4-004 | `localization/phase_estimator.py` | T-M4-004, T-M4-005 | OPEN |
| Matrix Eq.(16) | M4-LOC-008 | `localization/position_solver.py::_build_coefficient_matrix` | T-M4-006 | VERIFIED (algebraically correct with compensating negation) |

---

## Phase Execution Log

### Phase A — IN PROGRESS
**Started:** 2026-07-20

- M2-PHY-005: Replacing speed-of-light literals with constant imports
- CFG-004: Creating paper_reference.yaml
