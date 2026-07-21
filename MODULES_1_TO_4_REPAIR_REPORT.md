# MODULES 1–4 REPAIR REPORT

**Project:** Indoor-GPS VLC/L System  
**Specification:** `MODULES_1_TO_4_AUDIT_AND_REPAIR_SPEC.md`  
**Reference Paper:** Yang et al., *An Advanced Integrated Visible Light Communication and Localization System*, IEEE Trans. Commun., Dec. 2023.  
**Completed:** 2026-07-21  
**Test Result:** **83 / 83 PASS** (zero regressions)

---

## Executive Summary

All P0–P3 requirements in the audit spec have been resolved across Phases A–I. The implementation now:

- Maintains a clean **Module 1 → 2 → 3/4** architectural boundary (no reverse dependencies)
- Uses a **single canonical angular unit** (radians) throughout internal computation
- Derives **Lambertian order `m`** only in Module 2 from Module 1's primitive `beam_angle`
- Implements **Paper Eq.(1) correctly** with `√P` weighting in the SNR numerator
- Documents and enforces the **sign convention invariant** between `channel_interface.py` and `position_solver.py`
- Provides **50 new regression tests** across 2 test files covering all fixed requirements

---

## Requirement Status

| Req ID | Priority | Status | Summary |
|---|---|---|---|
| M1-ENV-ANGLE-001 | P0 | ✅ DONE | `calculate_angles()` returns radians; all consumers updated atomically |
| M1-ENV-002 | P0 | ✅ DONE | `dc_gains` removed from `EnvironmentState`; `PhysicsState.los_gains` is sole owner |
| M1-ENV-001 | P1 | ✅ DONE | Unreachable physics code removed from `simulator.get_state()`; `PhysicsEngine` removed from Module 1 |
| M1-ENV-003 | P2 | ✅ DONE | Lambertian order computation removed from `LED.__init__`; only `beam_angle` stored |
| M1-ENV-004 | P3 | ✅ DONE | Dead methods `receive_signal()`, `measure_snr()` removed from `Receiver` |
| INT-001 | P2 | ✅ DONE | `room_dims`, `led_orientations`, `led_beam_angles` added to `EnvironmentState`; sourced in all callers |
| M2-PHY-001 | P0 | ✅ DONE | Angles arrive in radians (fixed at source via M1-ENV-ANGLE-001); `compute_los_dc_gain()` receives correct input |
| M2-PHY-002 | P2 | ✅ DONE | `beam_angle` sourced from `env_state.led_beam_angles[led_id]` |
| M2-PHY-003 | P2 | ✅ DONE | `led_normal` sourced from `env_state.led_orientations[led_id]` |
| M2-PHY-005 | P3 | ✅ DONE | `SPEED_OF_LIGHT` imported from `physics/constants.py`; no literals |
| M3-COM-002 | P1 | ✅ DONE | `snr.py`: `Σ √P·H` implemented (was `Σ P·H`); Paper Eq.(1) now correct |
| M3-COM-003 | P2 | ✅ DONE | `delta` parameter renamed to `eta_scaling` in `snr.py` |
| M3-COM-004 | P3 | ✅ DONE | `strict=True` raises `VLCLCommunicationError` on BER length mismatch |
| M4-LOC-006 | P2 | ✅ DONE | `rx_bandwidth` made configurable in `LocalizationChannelInterface` |
| M4-LOC-008 | P2 | ✅ DONE | Cross-file sign convention documented in both `channel_interface.py` and `position_solver.py` |
| M4-LOC-014 | P2 | ✅ VERIFIED | `PositionSolver` contains no `EnvironmentState` import or reference |
| CFG-004 | P1 | ✅ DONE | `configs/paper_reference.yaml` created with full Section IV provenance |
| Phase D (reflection.py) | AUDIT | ✅ PASS | NLOS Lambertian model correct; no changes needed |
| Phase D (led_freq_response.py) | AUDIT | ✅ PASS | First-order LP H(f)=1/(1+jf/fc) correct |
| Phase E (BER modulation audit) | AUDIT | ✅ PASS | M-set is {2,4,16,64} square QAM; 8/32-QAM not present |
| Phase F (comm channel_interface) | AUDIT | ✅ FIX | Fixed deterministic noise seed (42→None); `noise_seed` parameter added |
| Phase I (filters.py) | AUDIT | ✅ PASS | Butterworth BPF correct; zero-phase `sosfiltfilt` used |
| Phase I (M4-LOC-007) | ✅ DONE | `PhaseUnwrapper` large-jump test (T-M4-007) verified |

---

## Files Changed

### Module 1 — Environment

| File | Changes |
|---|---|
| [`environment/geometry.py`](backend/VLCL_AI/environment/geometry.py) | Returns radians; removed `calculate_lambertian_dc_gain()` |
| [`environment/scene.py`](backend/VLCL_AI/environment/scene.py) | Removed H(0) step; FOV comparison in radians; added `led_orientations`, `led_beam_angles` to metrics dict |
| [`environment/state.py`](backend/VLCL_AI/environment/state.py) | Renamed angle fields; removed `dc_gains`; added `room_dims`, `led_orientations`, `led_beam_angles` |
| [`environment/simulator.py`](backend/VLCL_AI/environment/simulator.py) | Removed dead physics code; removed `PhysicsEngine` instantiation; added INT-001 fields |
| [`environment/led.py`](backend/VLCL_AI/environment/led.py) | Removed inline lambertian_order calculation |
| [`environment/receiver.py`](backend/VLCL_AI/environment/receiver.py) | Removed `receive_signal()`, `measure_snr()` |

### Module 2 — Physics

| File | Changes |
|---|---|
| [`physics/physics_engine.py`](backend/VLCL_AI/physics/physics_engine.py) | Angles consumed in radians; `beam_angle` and `led_normal` sourced from `env_state`; `room_dims` from `env_state` |
| [`physics/reflection.py`](backend/VLCL_AI/physics/reflection.py) | Phase D PASS annotation added |
| [`physics/constants.py`](backend/VLCL_AI/physics/constants.py) | Pre-existing; `SPEED_OF_LIGHT` canonical source |

### Module 3 — Communication

| File | Changes |
|---|---|
| [`communication/snr.py`](backend/VLCL_AI/communication/snr.py) | `sqrt(P)` fix (M3-COM-002); `eta_scaling` rename (M3-COM-003) |
| [`communication/ber.py`](backend/VLCL_AI/communication/ber.py) | `strict=True` parameter added (M3-COM-004) |
| [`communication/channel_interface.py`](backend/VLCL_AI/communication/channel_interface.py) | `noise_seed=None` fix (Phase F) |

### Module 4 — Localization

| File | Changes |
|---|---|
| [`localization/channel_interface.py`](backend/VLCL_AI/localization/channel_interface.py) | `rx_bandwidth` configurable (M4-LOC-006); sign convention doc (M4-LOC-008) |
| [`localization/position_solver.py`](backend/VLCL_AI/localization/position_solver.py) | Sign convention doc (M4-LOC-008); `SPEED_OF_LIGHT` import (M2-PHY-005) |
| [`localization/engine.py`](backend/VLCL_AI/localization/engine.py) | `room_bounds` sourced from `env_state.room_dims` (INT-001) |

### Config

| File | Changes |
|---|---|
| [`configs/paper_reference.yaml`](backend/VLCL_AI/configs/paper_reference.yaml) | NEW — Section IV simulation parameters with provenance |

### Tests

| File | Tests | Coverage |
|---|---|---|
| [`tests/test_phase_b_c_audit.py`](backend/VLCL_AI/tests/test_phase_b_c_audit.py) | 16 | Phases B+C: angles, ownership, H(0) physics, INT-001 |
| [`tests/test_phase_g_h_i_audit.py`](backend/VLCL_AI/tests/test_phase_g_h_i_audit.py) | 34 | Phases G+H+I: SNR, BER, sign convention, firewall, unwrapper |

---

## Open Deviations and Known Ambiguities

> [!WARNING]
> The following items are documented as scientific ambiguities, not implementation bugs.

| ID | Description | Action Required |
|---|---|---|
| PAPER_AMBIGUITY-001 | LED 2 position: Paper Sec.IV appears to list LED 1 and LED 3 at the same position. Used `[0.4, 0.4, 1.35]` for LED 2 as a symmetric-layout correction. | Resolve with authors' dataset or published erratum. |
| PAPER_AMBIGUITY-002 | LED transmit power: Paper does not specify absolute optical power for hardware used in Sec.IV experiments. Using `1.0 W` as a documented assumption. | Replace when hardware spec is available. |
| PAPER_AMBIGUITY-003 | APD model parameters not given in paper excerpt. Using typical Si APD values. | Replace with paper's actual APD datasheet values. |
| OPEN-M3-COM-001 | 8/32-QAM in BER M-set: square-QAM BER formula does not apply to non-square constellations. Currently blocked. | Requires constellation-specific erfc derivation before enabling. |

---

## Test Summary

```
============================= 83 passed in 1.09s ==============================

Breakdown:
  test_ber.py                          2 pass
  test_communication_chain.py          1 pass
  test_dco_ofdm.py                     2 pass
  test_equalization.py                 2 pass
  test_frequency_response.py           1 pass
  test_localization_engine.py          7 pass
  test_module2_integration.py          1 pass
  test_ofdm.py                         2 pass
  test_phase_b_c_audit.py             16 pass   ← new (Phases B+C)
  test_phase_g_h_i_audit.py           34 pass   ← new (Phases D/E/F/G/H/I)
  test_physics.py                      5 pass
  test_qam.py                          3 pass
  test_rate.py                         1 pass
  test_simulation.py                   5 pass
  test_subcarriers.py                  1 pass
```

Zero regressions in pre-existing tests.
