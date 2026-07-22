# Module 9 Component Validation Matrix

| Module | Validation target | Evidence | Current conclusion |
|---|---|---|---|
| 1 Environment | coordinates, distances, angles, scene bounds | existing geometry tests; paper config validator | implementation testable; paper geometry incomplete |
| 2 Channel | H(0), received power, noise, SNR | existing physics/channel tests; Eq. 1 oracle | equation checked; paper hardware inputs incomplete |
| 3 Communication | QAM, DCO-OFDM, BER, rate | existing communication tests; Eq. 1–3 oracles | deterministic equations checked |
| 4 Localization | tones, differential DSP, I/Q, distance differences | existing localization tests; Eq. 4–16 oracles | deterministic chain checked |
| 5 Spectrum | tone reservation, guards, Hermitian layout | existing integrated tests | requires paper spectrum details for figure comparison |
| 6 Adaptation | threshold selection, allocation/QoS | existing adaptive tests; Eq. 17 boundary oracle | deterministic threshold checked |
| 7 Power/pre-EQ | H(f), reserve, water filling, Eq. 18 | existing Module 7 suite; Eq. 18 oracle | deterministic equation checked |
| 8 Joint optimization | iteration/constraints/convergence | existing Module 8 suite | paper numerical trace unavailable |

This matrix distinguishes executable component regressions from numerical comparison against the reference paper. The latter is not complete until missing parameters and paper reference data are supplied.
