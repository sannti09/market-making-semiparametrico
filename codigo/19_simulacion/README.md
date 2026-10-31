# 19 · Simulation, 21 Sep–26 Oct (36 days, frozen models and policies)

Part of this period (21 Sep–6 Oct) was used in the exploratory phase, in predictive and economic evaluations of earlier versions of the model; those results were not used to select or tune the final specifications. No model was evaluated on 7–26 Oct before this run. Models (`16_`) and policies (`18_`) are frozen and were run once in this folder; `21_` later re-ran the economic evaluation with other execution rules. As a control, the script first reproduces 4 Sep of `17_` and `18_` exactly.

## Simulator rules

- Decisions are taken at the start of each second, with no order latency.
- An order fills only when the price is strictly crossed, at most one fill per side per second.
- Orders are 0.01 BTC each, with inventory |q| ≤ 10.
- PnL is marked to the last mid.

## Prediction

- AUC of E3: **0.848 ask / 0.842 bid** (0.813 in the test).

E3's advantage per second [95 % CI], days won:

| Against | Ask | Bid |
|---|---|---|
| AS base | +1.16 [0.95; 1.42], 36/36 | +1.29 [1.02; 1.58], 36/36 |
| Hawkes 2 scales + S | +0.35 [0.30; 0.41], 36/36 | +0.38 [0.32; 0.44], 36/36 |
| GLM 49 cov. | +0.11 [0.07; 0.15], 32/36 | +0.13 [0.08; 0.18], 35/36 |
| E3-fkX | −0.003 [−0.010; 0.005], 16/36 | +0.008 [0.003; 0.014], 28/36 |

- Criteria C1–C3 hold.
- **C4 does not hold:** the rebound gap after buyer sweeps is +0.222 (limit 0.15).

## Economics (E3)

| Policy | Fills/day | USDT/day | bps per fill | Positive days |
|---|---|---|---|---|
| HJB | 2,375 | −249 | −1.26 [−1.34; −1.18] | 0/36 |
| Myopic | 4,406 | −449 | −1.22 | 0/36 |
| GLFT | 3,065 | −309 | −1.21 | 0/36 |

- With the HJB and GLFT policies, no difference between E3 and any other model is significant.
- **With the myopic rule E3 loses more:** −0.079 bps per fill [−0.128; −0.028] against the models that always quote at 1 bp.

**Summary:** E3 remains the best predictor out of sample, but no model is profitable and none wins clearly on PnL.

Run: `codigo/sim_v111.py` (log in `salida/sim_v111.log`).

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
