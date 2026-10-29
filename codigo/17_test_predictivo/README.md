# 17 · Predictive test, 4–20 Sep (main predictive result)

Evaluates the models of `16_` with the protocol of `09_`. This is the period already opened in `12_`, so it is declared as previously consulted, not blind.

## Result: all four pre-registered criteria are met

| Criterion | Result |
|---|---|
| C1 hierarchy | ✓ CI > 0 against all five benchmarks, both sides |
| C2 consistency vs E2m+S | ✓ 17/17 days, both sides |
| C3 AUC ≥ 0.80 | ✓ 0.813 ask, 0.813 bid |
| C4 rebound ≤ 0.15 | ✓ +0.115 after seller sweeps, −0.140 after buyer sweeps |

E3 log-likelihood per bin minus each model's [95 % CI], days E3 wins, model AUC:

| Model | Ask | Bid |
|---|---|---|
| E3-fkX (44 cov.) | +0.002 [−0.004; +0.008], 10/17, 0.813 | +0.015 [+0.003; +0.029], 13/17, 0.812 |
| E3 base | +0.053 [+0.034; +0.073], 16/17, 0.812 | +0.087 [+0.047; +0.134], 17/17, 0.809 |
| GLM 49 cov. (E1+X49) | +0.110 [+0.077; +0.145], 16/17, 0.801 | +0.140 [+0.089; +0.193], 16/17, 0.798 |
| Hawkes 2 scales + signals (E2m+S) | +0.345 [+0.251; +0.454], 17/17, 0.768 | +0.353 [+0.263; +0.457], 17/17, 0.758 |
| Hawkes 2 scales + h-f (E2m+h-f) | +0.523 [+0.377; +0.692], 17/17, 0.753 | +0.505 [+0.355; +0.681], 17/17, 0.743 |
| AS + 7 signals (E1+S) | +0.742 [+0.508; +1.010], 17/17, 0.714 | +0.764 [+0.526; +1.036], 17/17, 0.715 |
| AS base (E1) | +1.316 [+0.880; +1.810], 17/17, 0.500 | +1.340 [+0.835; +1.953], 17/17, 0.500 |

- E3 clearly beats every classical benchmark.
- Against its own 44-covariate variant the gain is small, and not significant on the ask side.

Full table in `tablas_tesis/T5_test.md`; comparison with the original fit in `NOTA_V109.md`. Run: `codigo/test_v109.py`, then `codigo/tabla_test_v109.py`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
