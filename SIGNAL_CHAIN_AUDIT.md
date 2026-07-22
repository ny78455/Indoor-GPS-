# Signal-Chain Exactly-Once Audit

| Transformation | Owning module | Audit evidence | Status |
|---|---|---|---|
| Distance and angles | `environment.GeometryEngine` | geometry returns metres/radians; tests use manual vectors | pass |
| Lambertian DC gain | `physics.optical_channel` | explicitly excluded from Module 1 | pass |
| LED frequency response | `communication.led_frequency_response` | Module 7 attenuation test | pass |
| Pre-equalization H⁻¹ and √P | `communication.PreEqualizer.apply_eq18` | Module 9 Eq. 18 oracle | pass |
| Optical propagation delay | `localization.channel_interface` | paired sign convention documented in `DistanceDifferenceSolver` | pass |
| Noise | physics/channel interfaces | seed streams separated by `RandomSeedManager` | review per experiment |
| FFT/IFFT, DC bias, clipping | communication DCO-OFDM chain | existing Module 3 tests | existing regression |

This audit is a traceability review, not a claim that every physical hardware effect is known from the paper.
