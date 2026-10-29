# 05 · Monotone distance curve f(δ)

Replaces the exponential distance term −kδ with a free monotone curve f(δ) estimated on the nine distances (closed form f_j = log N_j / N_1 with a θ-parametrisation), multiplied by a state modulation m(X) = exp(clip(b′z, ±5)).

## Results (training data only, `NOTA_V90.md`)

- **The exponential is badly miscalibrated in the tail.** At 20 bps, −kδ underestimates crossings by a factor e^5.6 (ask) and e^8.1 (bid).
- **The free curve fixes it.** Log-likelihood per bin +0.031 (ask) and +0.032 (bid), better on 45 of 45 evaluation days.
- **AUC does not change** (0.822 → 0.822): this is calibration of levels across distances, not better ranking in time.
- Curve and state modulation together (E3-fkX) beat each one alone.

`codigo/modelo_f.py` is the original fit. The corrected version used in the thesis is in `16_`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
