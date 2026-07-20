# IMPLEMENTATION HANDOFF
Companion to `MODULES_1_TO_4_AUDIT_AND_REPAIR_SPEC.md`. This document is the executable checklist; the spec document is the evidence and rationale. Do not skip re-reading the relevant spec section before implementing an item.

---

## 1. REPAIR PHASES IN EXACT ORDER

### PHASE A — Shared constants + units
- `M2-PHY-005`

### PHASE B — Module 1 geometry & state contract
- `M1-ENV-003`, `INT-001` (add fields), degrees/radians contract decision (root cause of `M2-PHY-001`), `M1-ENV-002`, `M1-ENV-004`, `M1-ENV-001`

### PHASE C — Module 2 LOS optical physics
- `M2-PHY-001`, `M2-PHY-002`, `M2-PHY-003`, `INT-001` (completion)

### PHASE D — Module 2 noise + frequency response + multipath
- `T-M2-005` (audit `physics/reflection.py`), `T-M3-006` (audit `communication/led_frequency_response.py`)

### PHASE E — Module 3 QAM/OFDM primitives
- `M3-COM-001`, grade existing OFDM/QAM tests

### PHASE F — Module 3 physical channel integration
- `T-M3-004` (audit `channel_equalizer.py`), `T-M3-005` (audit `communication/channel_interface.py`)

### PHASE G — Module 3 SNR/BER/rate consistency
- `M3-COM-002`, `M3-COM-003`, `M3-COM-004`

### PHASE H — Module 4 transmitted/received localization signals
- No code fix required (Eq. 4–6 chain verified correct). Add `T-M4-001`, `T-M4-003` as regression locks first.

### PHASE I — Module 4 DPD/IQ chain
- `T-M4-004`, `T-M4-005` (audit `filters.py`), `M4-LOC-007`

### PHASE J — Module 4 Equation 16
- `M4-LOC-008` (documentation + `T-M4-003`)

### PHASE K — Module 4 position solver/calibration
- `T-M4-006` (audit `calibration.py`), `M4-LOC-006`

### PHASE L — Cross-module integration
- `T-INT-001`, `T-INT-002`, `T-INT-003`

### PHASE M — Frontend/API alignment
- `CFG-001` (Three.js Y-up vs. backend Z-up — audit, currently unverified)

### PHASE N — Regression and paper validation
- `CFG-004` (`configs/paper_reference.yaml`), Level 10 test

---

## 2. REQUIREMENT IDs IN EACH PHASE (summary table)

| Phase | Requirement IDs |
|---|---|
| A | M2-PHY-005 |
| B | M1-ENV-001, M1-ENV-002, M1-ENV-003, M1-ENV-004, INT-001 (partial) |
| C | M2-PHY-001, M2-PHY-002, M2-PHY-003, INT-001 (complete) |
| D | (validation-gap audits, no ID yet assigned — assign on discovery) |
| E | M3-COM-001 |
| F | (validation-gap audits) |
| G | M3-COM-002, M3-COM-003, M3-COM-004 |
| H | (regression locks only) |
| I | M4-LOC-007, (validation-gap audits) |
| J | M4-LOC-008 |
| K | M4-LOC-006, (validation-gap audit) |
| L | INT-001 (cross-module verification) |
| M | CFG-001 |
| N | CFG-004 |

---

## 3. FILES MODIFIED IN EACH PHASE

- **A:** `physics/physics_engine.py`, `localization/position_solver.py` (remove re-literaled `c`)
- **B:** `environment/led.py`, `environment/state.py`, `environment/geometry.py`, `environment/scene.py`, `environment/receiver.py`, `environment/simulator.py`
- **C:** `physics/physics_engine.py`
- **D:** `physics/reflection.py`, `communication/led_frequency_response.py` (audit only unless bugs found)
- **E:** `communication/qam.py`, `communication/ber.py`
- **F:** `communication/channel_equalizer.py`, `communication/channel_interface.py` (audit only unless bugs found)
- **G:** `communication/snr.py`
- **H:** none (test additions only: `tests/test_localization_engine.py` or new file)
- **I:** `localization/filters.py` (audit), `localization/phase_estimator.py` / `localization/engine.py` (if `M4-LOC-007` requires a code change)
- **J:** `localization/channel_interface.py`, `localization/position_solver.py` (comments only — no logic change)
- **K:** `localization/calibration.py` (audit), `localization/channel_interface.py` (`M4-LOC-006`)
- **L:** integration test files only
- **M:** `frontend/src/*` (audit; changes only if a mismatch is found)
- **N:** `configs/paper_reference.yaml` (new file)

---

## 4. TESTS THAT MUST PASS BEFORE PROCEEDING TO THE NEXT PHASE

- **After Phase B:** `T-M1-001`, `T-M1-002`, `T-M1-003`, `T-M1-004` pass. `grep -r "calculate_lambertian_dc_gain\|dc_gains" backend/VLCL_AI` returns no hits.
- **After Phase C:** `T-M2-001`, `T-INT-001` pass — synthetic hand-computed H(0)/power/SNR cases match to 1e-9 relative error.
- **After Phase E/G:** `T-M3-001` (SNR), `T-M3-002`, `T-M3-003` (BER/Rate regression pins) pass.
- **After Phase H/J:** `T-M4-001`, `T-M4-002` (ground-truth firewall static check), `T-M4-003` (sign-convention synthetic end-to-end) pass.
- **After Phase L:** a full noiseless Level-5 end-to-end test (Module 1→2→3 and Module 1→2→4) passes: near-zero BER, near-exact position recovery from synthetic exact geometry.
- **Before Phase N is considered complete:** Level 10 paper-scenario test runs against `configs/paper_reference.yaml` and reports results within a documented tolerance (not necessarily bit-exact to the paper's experimental hardware results, since those include real-world effects not modeled here — but internally consistent and order-of-magnitude correct).

---

## 5. STOP CONDITIONS

Stop and escalate back to spec/review (do not proceed to the next phase) if any of the following occur:
- A fix to `M2-PHY-001` does not converge `T-M2-001` to the stated tolerance after the units correction — indicates a second, undiscovered bug in `optical_channel.py` or `lambertian.py` that this audit did not find.
- Any change to `localization/channel_interface.py` or `localization/position_solver.py` (Phase J) changes the sign of recovered distance differences in `T-M4-003` — this means the compensating negation described in `M4-LOC-008` was broken; revert and re-derive both files together, not separately.
- `T-M4-002` (ground-truth firewall static check) ever fails, at any phase, for any reason — this is a hard stop regardless of what phase is in progress. No P0/P1 fix elsewhere justifies reintroducing ground-truth leakage.
- Any `VALIDATION GAP` file (Section 32 of the spec) is found, upon audit, to contain a P0-severity issue — pause the current phase, add the new issue to the register with a fresh ID, and re-sequence the repair order if the new issue has dependencies on work not yet done.
- Paper reproduction (`configs/paper_reference.yaml`, Phase N) cannot converge to a plausible localization/BER result even after all P0/P1 fixes — this indicates either a remaining undiscovered bug or a `PAPER_AMBIGUITY` (e.g., the LED-position duplication noted in Section 27 of the spec) that must be resolved with an explicit, documented simulation assumption before continuing, not silently worked around.

---

## 6. FINAL ACCEPTANCE GATE FOR MODULE 5

Module 5 (integrated VLCL spectrum) may begin only when **all** of the following hold:

1. Both P0 issues (`M2-PHY-001`, `M1-ENV-002`) are closed and covered by passing tests.
2. All P1 issues (`M1-ENV-001`, `M3-COM-002`, `CFG-004`) are closed and covered by passing tests.
3. `T-M4-002` (ground-truth firewall) is running in CI and passing.
4. `T-M4-003` (Eq. 16 sign-convention regression) is running in CI and passing.
5. Every item in Section 32 of the spec ("Validation Gaps") has been either (a) audited and closed with evidence, or (b) explicitly re-filed as a tracked P2/P3 issue with a documented reason it is safe to defer past Module 5.
6. `configs/paper_reference.yaml` exists and the Level 10 reproduction test passes within documented tolerance.
7. `EnvironmentState` exposes room dimensions and per-LED beam_angle/lambertian_order, and no file outside `physics/` computes a channel-gain-shaped quantity (verified by `grep`/static check, not just by report).
8. The Requirement Traceability Matrix (spec Section 33) shows zero P0/P1 rows in `OPEN` status.

### OVERALL VERDICT (as of this audit): **NOT READY FOR MODULE 5**

Blocking requirements, in priority order:
1. `M2-PHY-001` (P0 — units bug corrupts all physics)
2. `M1-ENV-002` (P0 — duplicated, disagreeing H(0) source of truth)
3. `M1-ENV-001` (P1 — broken `get_state()` snapshot path)
4. `M3-COM-002` (P1 — communication SNR Eq. 1 missing square root)
5. `CFG-004` (P1 — no paper-reproduction configuration exists, blocking Level 10 validation)
6. Full closure of the Section 32 validation-gap list (currently ~15 files/areas not yet algebraically audited)

### Readiness scores (self-assessed from this audit's depth of coverage; VALIDATION GAP areas scored conservatively)

```
MODULE 1 — Environment
  Architecture correctness: 6/10   (duplicated gain ownership violation)
  Mathematical correctness: 6/10   (geometry math itself correct; units contract broken)
  Paper fidelity:            7/10   (coordinate system, LOS, mobility structurally sound)
  Test coverage:              5/10   (tests exist but not individually graded — gap)
  Ready for Module 5: NO

MODULE 2 — Physics
  Architecture correctness: 7/10   (clean separation, but Module-1 duplication leaks in)
  Mathematical correctness: 3/10   (P0 units bug corrupts the central H(0) computation)
  Paper fidelity:            7/10   (formulas themselves are paper-correct in isolation)
  Test coverage:              5/10   (existing tests likely passing against the bug, not despite it — must be re-verified post-fix)
  Ready for Module 5: NO

MODULE 3 — Communication
  Architecture correctness: 7/10
  Mathematical correctness: 6/10   (BER/Rate correct; SNR Eq.1 has a confirmed bug)
  Paper fidelity:            6/10   (missing M=8/32; otherwise faithful)
  Test coverage:              5/10   (several files not yet audited)
  Ready for Module 5: NO

MODULE 4 — Localization
  Architecture correctness: 8/10   (ground-truth firewall verified clean — the hardest part)
  Mathematical correctness: 8/10   (Eq.4-16 chain re-derived and confirmed correct, with a
                                     documented, self-consistent sign-convention translation)
  Paper fidelity:            7/10   (topology detail — LED1 carries f1&f5 — correctly modeled)
  Test coverage:              4/10   (filters.py, calibration.py unaudited; no CI enforcement
                                     of the firewall yet)
  Ready for Module 5: NO (blocked by upstream Module 2 dependency, not by Module 4's own logic)
```

**OVERALL VERDICT: NOT READY FOR MODULE 5.** Module 4's own localization mathematics is the strongest part of the codebase (ground-truth firewall clean, Eq. 4–16 chain correct), but it is currently consuming physically-wrong channel gains from Module 2 (`M2-PHY-001`), which makes its real-world output unreliable regardless of its internal correctness. Fix Phases A–C first; re-run this scorecard after Phase C before proceeding further.
