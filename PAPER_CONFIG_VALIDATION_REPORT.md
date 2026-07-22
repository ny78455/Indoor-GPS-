# Paper Configuration Validation Report

Run `python -m VLCL_AI.reproduction.run --config VLCL_AI/configs/paper_exact.yaml --experiment config` from `backend` to generate the timestamped report and manifest.

Expected `PAPER_EXACT` outcome: **INCOMPLETE / FAIL**, because critical room, optical, receiver, sampling and power values are explicitly `UNKNOWN` or `PAPER_AMBIGUITY`. This is the intended scientific-integrity gate; use `PAPER_INFERRED` only with a separately documented inferred configuration.
