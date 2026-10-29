# 10 · Walk-forward validation

Five weekly expanding windows: each fit starts on 29 Jun and ends on 31 Jul, 7, 14, 21 or 28 Aug; each evaluation is the following week. That gives **34 out-of-sample days (1 Aug–3 Sep)**; the test stayed closed. All 11 models are refitted in every window.

## Results (`tablas_tesis/T1–T4`)

- **E3 beats the other 10 models in all 5 windows and on both sides.**
- The smallest margin is against its own variant without sweep covariates (E3-fkX): ask +0.024 [+0.005; +0.050], bid +0.008 [+0.002; +0.015].
- AUC at δ = 2 bps: 0.834 (ask) and 0.825 (bid).

E3 log-likelihood per bin minus each model's [95 % CI]:

| Model | Ask | Bid |
|---|---|---|
| GLM, 49 covariates (E1+X49) | +0.158 [+0.111; +0.223] | +0.166 [+0.102; +0.254] |
| Hawkes 2 scales + signals (E2m+S) | +0.365 [+0.275; +0.470] | +0.408 [+0.286; +0.554] |
| AS + 7 signals (E1+S) | +0.857 [+0.609; +1.152] | +0.893 [+0.582; +1.261] |
| AS base (E1) | +1.743 [+1.122; +2.483] | +1.684 [+1.061; +2.440] |

- **Stable ranking:** E3 > E3-fkX > E3 base > GLM 49 > Hawkes 2 scales + S > Hawkes 2 scales + h-f > Hawkes 1 scale / AS + S > Hawkes 1 scale / AS + h-f > AS base.
- **Overfitting check:** not flagged. The out/in-sample ratio against the GLM fell below 0.5 in 2 of 5 windows; the rule needed 3. Those two windows contain the turbulent 15–28 Aug week in-sample.

## How to run

`codigo/wf_v102.py`, then `codigo/tablas_v102.py` (writes `tablas_tesis/` as md, csv, tex and figures).

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
