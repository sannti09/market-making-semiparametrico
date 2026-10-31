# 21 · Execution with an approximate queue (robustness of the economic evaluation)

The thesis evaluates PnL with a **strict-cross rule**: a passive order fills only if an aggressor trades strictly beyond its price. This folder re-runs the economic evaluation of the test (4–20 Sep) and the simulation (21 Sep–26 Oct) under two more execution rules. Models (v108) and policies (v110) stay frozen; only the execution rule changes. The protocol was sealed before running (`PLAN_V115.md`). This is a robustness analysis, not a confirmatory one: both periods had already been evaluated with the strict-cross rule.

## What the data allow

The canonical layer shows 20 levels per side every 100 ms. They reach only ~0.4–0.5 bps from the mid, while the policies quote at 0.85–2 bps (median). The real queue position therefore cannot be reconstructed. The rules below are sensitivity scenarios; they have not been shown to bound the real PnL:

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
| E3 base | R0 | −1.34 [−1.50; −1.15] | −1.30 [−1.43; −1.17] |
| E3 base | R2 | −1.34 [−1.51; −1.16] | −1.30 [−1.42; −1.16] |
| E3 base | R1 | +0.35 [+0.24; +0.47] | +0.44 [+0.37; +0.51] |
| AS and Hawkes (7 variants) | any | −1.22 to −1.29 | −1.20 to −1.26 |

- AS, Hawkes, GLFT and the myopic rule: the three rules differ by ≤ 0.07 bps.
- HJB with E3 (and the 49-covariate GLM): under R1 the number of fills triples and the gross result turns slightly positive. Under R1 the best economic variant is E3 base, not the thesis E3 (thesis − base: −0.24 bps in the test and −0.28 in the simulation, CI excludes 0), and the thesis E3 beats every AS and Hawkes variant by about +1.35 bps per fill (CI excludes 0). Under R0 and R2 none of these differences appears.
- With the maker fees evaluated in the thesis (7.5 and 10 bps per fill), no policy is profitable under any of the three rules.

## Limitations

- R1 is an optimistic scenario, not an estimate of real queue priority. It does not show that more speed would make E3 profitable.
- R2 matching R0 shows the result does not change under its assumptions (displayed or imputed depth, no cancellations ahead). It does not show that the real queue produces that result.
- The mechanism behind R1's extra fills has not been verified at fill level here.
- The pre-registered reading "the economic conclusion holds" is false even under R0, because the fixed-δ 5 bps policy has very few fills and a wide interval. Restricted to the 11 models (a reading added after seeing the results), it holds under R0 and R2, not under R1.

Details: [`NOTA_V115.md`](NOTA_V115.md) (Spanish). An exploratory fill-level analysis, designed after seeing these results, is in [`NOTA_FILLS_V115.md`](NOTA_FILLS_V115.md). Under R1 with E3, most fills are classified as touch-only (no trade beyond the price before the fill, at 1 ms resolution). Almost all of them are at the best price, they capture about half a tick against the mid, and their average 10 s markout is favourable (+0.55 to +0.62 bps), unlike the fills classified as crossing (≈ −1.27). This group is not the same as the fills R1 adds over R0, since fills are not matched across runs, and the analysis does not show how many of them a real order would get. Run: `codigo/cola_v115.py test`, then `codigo/cola_v115.py sim`. It needs `19_simulacion/salida/por_dia_econ_v111.json` for the control.

---
Protocols (`PLAN_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
