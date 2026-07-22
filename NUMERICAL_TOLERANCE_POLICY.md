# Numerical Tolerance Policy

| Result type | Acceptance rule |
|---|---|
| Integer allocation / IDs | exact equality |
| Deterministic scalar equations | absolute error ≤ 1e-9 unless units require a documented scale |
| Geometry/channel floating point | `rtol=1e-9`, `atol=1e-12` |
| Monte Carlo BER | compare binomial confidence intervals; report bits/errors, never interpret zero observed errors as zero true BER |
| Digitized paper points | use uncertainty recorded with the digitized dataset; do not use MAPE near zero |

Curve comparisons report MAE, RMSE, maximum absolute deviation, correlation and R² when meaningful. Raw values are retained alongside aggregate metrics.
