# Full System Traceability

| Paper requirement | Equation/section | Module | Source | Validation | Status |
|---|---|---|---|---|---|
| Coherent communication SNR | Eq. 1 | 3 | `communication/snr.py` | `test_eq01_03.py` | validated |
| QAM BER | Eq. 2 | 3 | `communication/ber.py` | `test_eq01_03.py` | validated for supported square QAM |
| Allocated rate | Eq. 3 | 3/6 | `communication/rate.py` | `test_eq01_03.py` | validated |
| A-DPDOA waveform/DSP | Eq. 4–16 | 4 | `localization/*` | `test_eq04_16.py` | deterministic oracle validated |
| Adaptive M-QAM | Eq. 17 | 6 | `adaptive/modulation_controller.py` | `test_eq17.py` | validated |
| Weighted pre-equalization | Eq. 18 | 7 | `communication/pre_equalizer.py` | `test_eq18.py` | validated |
| Joint resource loop | Sec. III | 8 | `adaptive/joint_optimizer.py` | existing `test_module8_joint.py` | existing regression |

Figure-level numerical reproduction remains pending paper numerical data and a complete paper-exact configuration.
