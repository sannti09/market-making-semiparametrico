# 15 · Gradient and convergence check of the E3 curve

Training data only. It checks the optimisation step that fits f(δ) and m(X) in E3.

## Findings (`NOTA_V107.md`)

- **The analytic gradient matches finite differences** (max relative error 1e-4). Its only defect was ignoring the ±5 clip in m(X).
- **The clip is active:** in about 30 of 5.8 million seconds, with max |b′z| of 6.8–8.6.
- **Convergence:** the original step stopped after 1–3 iterations. With the corrected gradient it converges in 70–102 iterations.
- **Effect:**
  - f changes only in the tail: up to −0.33 in log at 20 bps, ≤ 0.005 for δ ≤ 5 bps;
  - b changes ≤ 0.001;
  - the likelihood gain is negligible (~6e-6 per second).

This led to the corrected curve in `16_`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
