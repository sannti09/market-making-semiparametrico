# 03 · Data loader with date guard

`codigo/cargador_v98.py` reads only the canonical folder (`00_`) and raises `PermissionError` for any date outside the range a script is allowed to see. This is how the test (4–20 Sep) and the simulation (21 Sep–26 Oct) stayed closed while models were being developed.

## Result recorded here (development phase, not blind)

With 33 fitting days (29 Jun–31 Jul) and evaluation on 1 Aug–3 Sep, this is where the final E3 specification was chosen:

- **Chosen model: E3-fkX+B (49 covariates).** Adding a long-trend covariate did not help significantly.
- With the longer fit, the gradient-boosting part learns the post-sweep rebound: the gap after seller sweeps falls to **+0.091** and after buyer sweeps to **−0.036**.

Plans `PLAN_V98.md`, `PLAN_V99.md` (sealed with SHA-256); results in `NOTA_V98.md` and `salida/`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
