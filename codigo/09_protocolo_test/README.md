# 09 · Test protocol (pre-registered)

`PREREGISTRO_TEST_V101.md` was written and sealed (SHA-256) **before any test data were loaded**. It fixes the models, the metrics and four pass/fail criteria for the test period, 4–20 Sep 2026:

| | Criterion |
|---|---|
| C1 | Hierarchy: E3 beats E1+h-f, E1+S, E1+X49, E2m+h-f and E2m+S with a 95 % CI of Δ log-likelihood per bin > 0, on both sides |
| C2 | Consistency: E3 beats E2m+S on at least 14 of 17 days, on both sides |
| C3 | Discrimination: AUC at δ = 2 bps ≥ 0.80, on both sides |
| C4 | Rebound: \|gap\| after seller and buyer sweeps ≤ 0.15 |

- **Metrics:** log-likelihood per bin over the nine distances; 95 % CIs by day bootstrap (2,000 resamples, seed 20261029); AUC at δ = 2 bps.
- `ENMIENDA_V101B.md` is an amendment written before the test was opened.
- `codigo/test_v101.py` holds the shared functions (GLM, signals, evaluation) that later folders import.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
