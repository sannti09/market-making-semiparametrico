# 04 · Sweep covariates

Adds five covariates that describe the most recent sweep (a burst of aggressive orders that walks the book): signed price range, volume and time since the last sweep; maximum spread over the last second; mid change over the last second. With them, E3 goes from 44 to 49 covariates (E3-fkX → E3-fkX+B).

## Why

Without them, E3 underestimated the flow that comes back after a sweep (the "rebound").

## Results (development phase, `NOTA_V94.md`)

| | E3-fkX (44) | E3-fkX+B (49) |
|---|---|---|
| Rebound gap after seller sweeps | 0.332 | **0.248** |
| Rebound gap after buyer sweeps | 0.060 | **0.011** |
| Δ log-likelihood per bin [95 % CI] | — | ask +0.011 [+0.003; +0.023], bid +0.020 [+0.007; +0.036] |

- The covariates improve the **level** of the intensity after sweeps, not its ranking (AUC unchanged).
- With a longer fit the seller-side gap fell further, to +0.091 (`03_`).
- Permutation importance: order flow dominates; the sweep group adds about as much as volatility.

## Contents

- `codigo/feats_v94.py`: the covariates and a no-leakage test.
- `eventos_barridos/codigo/eventos_v92.py`: detects the sweep events. Its output is regenerated, not stored.
- `eventos_barridos/NOTA_V92.md`: an exploratory taker strategy that followed sweeps. **Negative:** 0 of 72 configurations passed.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
