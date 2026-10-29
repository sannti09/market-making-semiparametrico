# 01 · E3 core: data layer, conventions and base model

Shared building blocks used by every later folder.

| Path | Purpose |
|---|---|
| `01_pipeline/datos_capa_100ms.py` | Reads the 100 ms layer and builds 1-second bins; `indice_en_rejilla` returns −1 when a horizon falls outside covered data |
| `01_pipeline/convenciones.py` | Methodological conventions and which data each signal depends on (trades only vs trades + order book) |
| `01_pipeline/metricas.py` | Metrics, including AUC with mid-rank ties |
| `01_pipeline/modelo_e3_semiparametrico.py` | Base E3: log λ = g(X) + h(t) − kδ, with g a Poisson gradient-boosting model and h an hourly effect |
| `02_configuracion/PARTICION_ANTEPROYECTO.json` | The data partition fixed in the thesis proposal |

The final thesis model (E3-fkX+B) extends this base with a free monotone distance curve (`05_`), a state modulation m(X) (`05_`, `06_`) and sweep covariates (`04_`).

`NOTA_V37.md`, `AUC_P1_V37.md` and `RESUMEN_V37_*.md` are development-phase notes (corrections to horizons, the AUC tie rule and wording); their numbers belong to the exploratory phase, not to the final results.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
