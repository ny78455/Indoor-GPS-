# Paper Reproduction Specification

This repository validates Yang et al., *An Advanced Integrated Visible Light Communication and Localization System*, IEEE Transactions on Communications 71(12), 2023. The canonical machine-readable record is [paper_exact.yaml](backend/VLCL_AI/configs/paper_exact.yaml).

| Parameter | Symbol | Paper value | Units | Paper location | Confidence | Simulator mapping | Status |
|---|---:|---:|---|---|---|---|---|
| LEDs | L | 4 | — | Sec. II-A/IV | PAPER_EXPLICIT | `environment.LEDArray` | mapped |
| FFT size | N | 256 | — | Sec. IV | PAPER_EXPLICIT | `communication.SubcarrierGrid` | mapped |
| Modulation bandwidth | B | 20 | MHz | Sec. IV | PAPER_EXPLICIT | `communication` config | mapped |
| BER limit | BER_max | 3.8e-3 | — | Sec. IV | PAPER_EXPLICIT | `BERCalculator` | mapped |
| Localization tones | f1…f5 | 4.0…4.8, Δ=0.2 | MHz | Sec. IV | PAPER_EXPLICIT | `LocalizationFrequencyPlan` | mapped |
| Tone topology | — | f1/f5 use LED 1 | — | Sec. II-A | PAPER_EXPLICIT | `tone_to_led_map` | mapped |
| LED coordinates | — | listed in canonical config | m | Sec. IV | PAPER_EXPLICIT / PAPER_AMBIGUITY | `environment.LED` | partial |
| Room dimensions | — | not stated | m | — | UNKNOWN | `environment.Room` | blocking exact mode |
| Optical power / semi-angle | — | not stated | W / deg | — | UNKNOWN | `physics` | blocking exact mode |
| Receiver area, responsivity, FOV | A, μ, Ψc | not stated | m², A/W, deg | — | UNKNOWN | `Receiver`, `Photodiode` | blocking exact mode |
| ADC sampling/filter settings | G, fs | not stated | samples, Hz | — | UNKNOWN | `localization` | blocking exact mode |

Modes are strictly separated: `PAPER_EXACT` accepts only explicit or rigorously derived values and therefore reports the listed gaps; [`paper_inferred.yaml`](backend/VLCL_AI/configs/paper_inferred.yaml) preserves the documented inferred configuration; `DIGITAL_TWIN_EXTENDED` may model realistic phenomena but must label them extensions. Simulation results cannot establish physical-hardware equivalence without measurements or original experimental data.
