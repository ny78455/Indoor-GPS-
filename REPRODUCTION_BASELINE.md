# Reproduction Baseline

Modules 1–8 are frozen for Module 9 validation. The runner writes the exact commit, Python/dependency inventory, platform, configuration hash, seed policy, timestamp, and experiment outputs to `REPRODUCIBILITY_MANIFEST.json` for every run.

Known unresolved scientific inputs: paper room dimensions; absolute LED power and semi-angle; receiver area/responsivity/FOV; sampling/filter settings; and an apparent duplicate/ambiguous LED coordinate. These are reproduction blockers in `PAPER_EXACT`, not default values.

Any production change after this baseline must be recorded as `REPRODUCTION_BLOCKING_FIX` with its issue, scientific rationale, changed files, tests, and before/after evidence.
