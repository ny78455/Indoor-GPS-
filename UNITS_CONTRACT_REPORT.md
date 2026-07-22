# Units Contract Report

| Quantity | Canonical unit | Enforcement point |
|---|---|---|
| Distance | m | `GeometryEngine.distance` / environment configs |
| Time | s | localization signal and propagation APIs |
| Frequency/bandwidth | Hz | `LocalizationFrequencyPlan`, communication configs |
| Angles | rad internally | `GeometryEngine.calculate_angles` |
| Electrical/optical power | W, explicitly named | power allocation/config fields |
| Responsivity | A/W | receiver/photodiode configuration |
| Noise variance | A² where used in Eq. 1 | `compute_communication_snr` |
| Rate | bit/s | `RateCalculator` |
| Localization error | m | localization metrics |

Configuration validators reject invalid physical ranges and Nyquist violations. Paper-exact unknown units are retained as unknown rather than converted by assumption.
