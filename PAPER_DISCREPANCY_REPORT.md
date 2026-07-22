# Paper Discrepancy Report

| ID | Classification | Severity | Observation | Scientific impact | Recommended investigation |
|---|---|---|---|---|---|
| REP-001 | PAPER_AMBIGUITY | P0 | Section-IV LED coordinate listing is reported by the existing reference config as containing an apparent duplicate. | Prevents unambiguous geometry reproduction. | Obtain erratum, author clarification, or original experiment data. |
| REP-002 | PARAMETER_MISMATCH | P0 | Room dimensions/receiver trajectory are not available in the canonical exact config. | Prevents spatial/channel/heatmap comparison. | Obtain paper supplement or author configuration. |
| REP-003 | PAPER_AMBIGUITY | P0 | LED power/semi-angle and receiver area/responsivity/FOV are missing. | Prevents absolute SNR, BER, rate and localization-error comparison. | Obtain hardware/datasheet parameters. |
| REP-004 | PAPER_AMBIGUITY | P1 | Sampling, capture length and filter settings are missing. | Limits waveform-level A-DPDOA reproduction. | Obtain DSP implementation parameters. |

No production parameter has been tuned to clear these discrepancies. `PAPER_INFERRED` results must remain separate from untouched `PAPER_EXACT` results.
