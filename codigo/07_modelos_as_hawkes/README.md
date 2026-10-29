# 07 · Benchmark models: Avellaneda–Stoikov and Hawkes

The competitors of E3, fitted on the same bins, counts and days:

| Name | Model |
|---|---|
| E1 | Avellaneda–Stoikov: constant intensity A·e^(−kδ) |
| E1+h-f | AS + hourly effect + free distance curve f(δ) |
| E1+S | AS + hour + f(δ) + 7 signals (linear) |
| E1+X49 | Poisson GLM with the same 49 covariates as E3 (linear) |
| E2+h-f, E2+S | Hawkes, one exponential kernel, + hour + f(δ) / + signals |
| E2m+h-f, E2m+S | Hawkes, two kernels (β = 1 and 300 s⁻¹), + hour + f(δ) / + signals |

## Result (development comparison, evaluation 1 Aug–3 Sep, `NOTA_COMPARACION_E1_E2_E3.md`)

Share of E3's log-likelihood improvement over E1 that each model recovers (ask / bid):

| Model | Share | AUC δ = 2 |
|---|---|---|
| E1+h-f | 7.8 % / 7.2 % | 0.62 / 0.62 |
| E2+h-f | 9.6 % / 9.2 % | 0.63 / 0.63 |
| E1+S | 52.3 % / 48.2 % | 0.73 / 0.72 |
| E2m+h-f | 62.0 % / 59.2 % | 0.76 / 0.75 |
| E2m+S | 80.5 % / 75.8 % | 0.78 / 0.77 |
| E1+X49 | 92.8 % / 89.7 % | 0.82 / 0.81 |

- The two-scale Hawkes changes the picture: it recovers about 60 % of E3's gain, against under 10 % for the one-scale kernel.
- E3 still beats every variant on every day.

`exportar_paquete.py` exports the event files the Hawkes fit needs (`paquete/dias/`, regenerated, not stored).

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
