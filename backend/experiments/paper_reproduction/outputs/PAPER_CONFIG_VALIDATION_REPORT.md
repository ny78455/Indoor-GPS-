# Paper Configuration Validation Report

Mode: `PAPER_INFERRED`  
Configuration hash: `fe04be6e090c751b6d413def06d12bf41dcc9737706c0aa7c39c5f96b7b943e6`  
Status: **PASS**

| Severity | Code | Configuration path | Finding |
|---|---|---|---|
| WARNING | REP-CFG-004 | `room.width_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `room.length_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `room.height_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `room.reflections` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[0].orientation` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[0].optical_power_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[0].semi_angle_deg` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[1].position_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[1].orientation` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[1].optical_power_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[1].semi_angle_deg` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[2].orientation` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[2].optical_power_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[2].semi_angle_deg` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[3].position_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[3].orientation` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `leds[3].optical_power_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `leds[3].semi_angle_deg` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `receiver.height_m` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `receiver.area_m2` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `receiver.responsivity_a_per_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `receiver.fov_deg` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `receiver.orientation` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-004 | `communication.cyclic_prefix_ratio` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `localization.sample_rate_hz` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `power.total_budget_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `power.per_led_max_w` | Using documented SIMULATION_ASSUMPTION. |
| WARNING | REP-CFG-004 | `power.localization_reserve_w` | Using documented PAPER_INFERRED. |
| WARNING | REP-CFG-023 | `communication.modulation_orders` | Analytical BER oracle has no square-QAM implementation for [8, 32]. |

## Interpretation

`PAPER_EXACT` rejects critical inferred, assumed, ambiguous, or unknown values. Other modes retain those values only when their provenance remains explicit.
