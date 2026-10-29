# 11 · Final models

Fits the 11 models on **all training data, 29 Jun–3 Sep**, with exactly the specifications validated in `10_`. It uses the same fitting function as the walk-forward. No date after 3 Sep is read.

**Models:**
- E3: E3-fkX+B (the thesis model), E3-fkX, E3 base.
- Avellaneda–Stoikov: E1, E1+h-f, E1+S, E1+X49.
- Hawkes: E2+h-f, E2+S, E2m+h-f, E2m+S.

The models are saved as a pickle with SHA-256 and timestamp in `modelos/`. Run: `codigo/entrenar_v103.py` (log in `entrenar_v103.log`).

The models actually used in the thesis are these with the corrected E3 curve: `16_curva_e3_corregida/modelos/modelos_finales_v108.pkl`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
