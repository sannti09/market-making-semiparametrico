# 21 · Execution with an approximate queue (robustness of the economic evaluation)

The thesis evaluates PnL with a **strict-cross rule**: a passive order fills only if an aggressor trades strictly beyond its price. This folder re-runs the economic evaluation of the test (4–20 Sep) and the simulation (21 Sep–26 Oct) under two more execution rules. Models (v108) and policies (v110) stay frozen; only the execution rule changes. The protocol was sealed before running (`PLAN_V115.md`). This is a robustness analysis, not a confirmatory one: both periods had already been evaluated with the strict-cross rule.

## What the data allow

The canonical layer shows 20 levels per side every 100 ms. They reach only ~0.4–0.5 bps from the mid, while the policies quote at 0.85–2 bps (median). The real queue position therefore cannot be reconstructed, only bounded:

| Rule | Fill condition |
|---|---|
| R0, strict cross (thesis) | an aggressor trades strictly beyond the order's price |
| R2, approximate FIFO with imputed depth | as R0, or the aggressor volume at exactly the order's price within the second exceeds the queue ahead + the order. Queue ahead = displayed size at that price, or the median of the 20 visible levels when the price is beyond them; the queue only advances with trades, and priority is lost every second |
| R1, optimistic execution at the touch | an aggressor trades at the order's price or beyond (no queue ahead) |

Control: R0 reproduces v110 (17 days) and v111 (36 days) exactly.

## Results (gross PnL per fill, bps [95 % CI over days])

| HJB policy | Rule | Test | Simulation |
|---|---|---|---|
| E3 thesis | R0 | −1.32 [−1.42; −1.21] | −1.26 [−1.33; −1.18] |
| E3 thesis | R2 | −1.32 [−1.42; −1.21] | −1.25 [−1.33; −1.18] |
| E3 thesis | R1 | +0.11 [−0.00; +0.24] | +0.15 [+0.08; +0.24] |
| AS and Hawkes (7 variants) | any | −1.22 to −1.29 | −1.20 to −1.26 |

- AS, Hawkes, GLFT and the myopic rule: the three rules differ by ≤ 0.07 bps.
- HJB with E3 (and the 49-covariate GLM): under R1 the number of fills triples and the gross result turns slightly positive.
- With the maker fees evaluated in the thesis (7.5 and 10 bps per fill), no policy is profitable under any of the three rules.

## Limitations

- R1 is an optimistic scenario, not an estimate of real queue priority. It does not show that more speed would make E3 profitable.
- R2 matching R0 shows the result does not change under its assumptions (displayed or imputed depth, no cancellations ahead). It does not show that the real queue produces that result.
- The mechanism behind R1's extra fills has not been verified at fill level here.
- The pre-registered reading "the economic conclusion holds" is false even under R0, because the fixed-δ 5 bps policy has very few fills and a wide interval. Restricted to the 11 models (a reading added after seeing the results), it holds under R0 and R2, not under R1.

Details: [`NOTA_V115.md`](NOTA_V115.md) (Spanish). Run: `codigo/cola_v115.py test`, then `codigo/cola_v115.py sim`. It needs `19_simulacion/salida/por_dia_econ_v111.json` for the control.

---
Protocols (`PLAN_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
