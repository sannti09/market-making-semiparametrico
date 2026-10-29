# 18 · HJB with the exact interpolated curve; economic test

Generalises the HJB of `08_` to any distance curve. log λ̂(δ) is interpolated linearly between the nine estimated distances, and each segment's maximum is found in closed form (H′(p) = −Λ(δ*)e^(−γ(δ*−p))). Policies are precomputed as lookup tables in (σ², A_a, A_b), plus (m_a, m_b) for E3.

## Verifications (all passed, `salida/verificacion_v110.json`)

| | Check | Result |
|---|---|---|
| (a) | Exponential case vs the closed-form solver of `08_` | difference 1e-14 |
| (b) | Piecewise H vs brute force (200,001 points, 270 combinations) | max relative error 1.9e-8 |
| (c) | Monotonicity on real seconds | 0 violations of 220 |
| (d) | Table interpolation vs exact solution | small errors in δ* |

## Economic results in the test (4–20 Sep, gross of fees; `tablas_tesis/T6`, `T7`)

| Policy | E3 (bps per fill [95 % CI]) | Range across the 11 models | E3 minus model |
|---|---|---|---|
| Exact HJB | −1.32 [−1.42; −1.20] | −1.26 to −1.34 | every CI includes 0 |
| GLFT | −1.23 [−1.32; −1.11] | −1.22 to −1.26 | every CI includes 0 |
| Myopic | −1.34 [−1.48; −1.19] | −1.29 to −1.34 | — |

- **0 of 17 positive days for every model and policy.** With Binance maker fees (7.5–10 bps) the net loss is about −9 to −11 bps per fill.
- **The exact curve changes the policy but not the outcome.** It changes the quoted price in 86–99 % of decisions, but the loss per fill stays the same.
- **E3 trades less.** With the exact HJB it fills 2,451 orders/day, against 3,543–3,982 for AS and Hawkes with the same f(δ) shape (31–38 % fewer). That means less losing volume, not better fills.

## How to run

`codigo/verif_v110.py` builds the tables (`salida/tablas_v110.pkl`, regenerated, not stored) and runs the checks; then run `codigo/econ_v110.py`. The solver is `codigo/hjb_general.py`; `codigo/datos_v110.py` loads models and data.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
