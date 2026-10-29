# 16 · Corrected E3 curve (the models used in the thesis)

`codigo/modelo_f_v2.py` corrects the gradient (adds the derivative of the clip) and checks convergence (`success = True`, maxiter 2000). The original code in `05_` is left untouched.

`codigo/actualizar_curva_v108.py` takes the final models from `11_` and refits **only the curve step** of E3 and E3-fkX, with g and h fixed, on 29 Jun–3 Sep.

## Result

- All four fits converge in 70–102 iterations.
- f(20 bps) moves from −8.65 to −8.87 (ask) and from −10.31 to −10.62 (bid). For δ ≤ 5 bps nothing changes materially.
- The likelihood gain on training data is ~6e-6 per second: a numerical correction, not a new model.

Output: `modelos/modelos_finales_v108.pkl`, with its manifest `MANIFIESTO_v108.json` (SHA-256). **Every result in `17_`–`20_` uses this file.**

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
