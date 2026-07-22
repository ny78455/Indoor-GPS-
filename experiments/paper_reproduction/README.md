# Paper Reproduction Experiments

Run from `backend`:

```powershell
python -m VLCL_AI.reproduction.run --config VLCL_AI/configs/paper_exact.yaml --experiment all --seed 42
```

Each run saves its configuration validation report, equation results, Markdown report, and reproducibility manifest below `outputs/`. A non-zero exit status for `PAPER_EXACT` means the paper lacks a critical value; it is an honest incompleteness report, not a failed engineering default.

For a documented, non-exact engineering run use `VLCL_AI/configs/paper_inferred.yaml`. Its assumptions are intentionally embedded with provenance and should never be presented as paper-stated values.
