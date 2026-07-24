# Paper Configuration Validation Report

Mode: `PAPER_EXACT`  
Configuration hash: `66f31fbacd5e12b1d35894e52c3ecd6364b182a1e991b482eaaac075ade403b0`  
Status: **INCOMPLETE / FAIL**

| Severity | Code | Configuration path | Finding |
|---|---|---|---|
| ERROR | REP-CFG-001 | `room.width_m` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `room.length_m` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `room.height_m` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `receiver.height_m` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `receiver.area_m2` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `receiver.responsivity_a_per_w` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-001 | `receiver.fov_deg` | Required value is absent; exact reproduction is not supportable. |
| ERROR | REP-CFG-003 | `room.width_m` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `room.length_m` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `room.height_m` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `room.reflections` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[0].orientation` | PAPER_INFERRED is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[0].optical_power_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[0].semi_angle_deg` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[1].position_m` | PAPER_AMBIGUITY is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[1].orientation` | PAPER_INFERRED is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[1].optical_power_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[1].semi_angle_deg` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[2].orientation` | PAPER_INFERRED is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[2].optical_power_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[2].semi_angle_deg` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[3].position_m` | PAPER_AMBIGUITY is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[3].orientation` | PAPER_INFERRED is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[3].optical_power_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `leds[3].semi_angle_deg` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `receiver.height_m` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `receiver.area_m2` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `receiver.responsivity_a_per_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `receiver.fov_deg` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `receiver.orientation` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `communication.cyclic_prefix_ratio` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `localization.sample_rate_hz` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `power.total_budget_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `power.per_led_max_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-003 | `power.localization_reserve_w` | UNKNOWN is not allowed in PAPER_EXACT. |
| ERROR | REP-CFG-012 | `leds[1].position_m` | LED position must be a three-element coordinate in metres. |
| ERROR | REP-CFG-012 | `leds[3].position_m` | LED position must be a three-element coordinate in metres. |
| WARNING | REP-CFG-023 | `communication.modulation_orders` | Analytical BER oracle has no square-QAM implementation for [8, 32]. |

## Interpretation

`PAPER_EXACT` rejects critical inferred, assumed, ambiguous, or unknown values. Other modes retain those values only when their provenance remains explicit.
