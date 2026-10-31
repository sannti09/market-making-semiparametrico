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

- `wf_v102.py` writes to `salida/`:
  - `por_dia_v102.json`: metrics per day and model (included in the repository);
  - `eventos_v102.npy`: post-sweep events with each model's prediction (≈ 12 MB, not included).
- `tablas_v102.py` needs both. Without `eventos_v102.npy` it stops, and that file is only produced by running `wf_v102.py`.
- **Resuming:** after each window the script saves `fold{k}.json` and `fold{k}_ev.npy` (all the events of that window). On a re-run, windows with both files are not refitted, and `eventos_v102.npy` is rebuilt from them.
  - Before 30 Oct 2026, `fold{k}_ev.npy` kept only the window's last day. A resumed run would have produced an incomplete `eventos_v102.npy` and changed T4.
  - The published run was not resumed (see `salida/wf_v102.log`): its `eventos_v102.npy` has all 53,764 events, and T1–T4 are unaffected.
- `codigo/test_reanudacion_v102.py` checks the resume path without data or fitting. It verifies that a run interrupted after window 2, and a run with every window saved, reproduce the complete files. Optional argument: an existing `eventos_v102.npy`, to use its real rows.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
