# 20 · Where the loss comes from: adverse selection

Decomposes each fill's 10-second markout into two parts:

**markout = distance captured (vs the decision mid) + subsequent mid movement**

The fills are the same as the simulator's in `18_` and `19_` (53 days); fills and PnL match exactly.

| Period | Model, policy | Fills/day | Captured | Move 1 s | Move 10 s | Markout 10 s | % > 0 |
|---|---|---|---|---|---|---|---|
| test | E3, myopic | 4,222 | +0.92 | −1.78 | −2.15 | −1.24 | 23 % |
| test | E3, HJB | 2,451 | +1.08 | −2.08 | −2.36 | −1.28 | 27 % |
| test | Hawkes 2 sc. + S, HJB | 3,543 | +1.01 | −1.96 | −2.28 | −1.27 | 26 % |
| test | AS base, HJB | 2,218 | +1.46 | −2.43 | −2.75 | −1.29 | 29 % |
| test | AS base, myopic (δ = 2) | 1,173 | +2.00 | −3.04 | −3.31 | −1.31 | 32 % |
| simulation | E3, HJB | 2,375 | +1.04 | −1.93 | −2.28 | −1.24 | 27 % |
| simulation | AS base, HJB | 2,115 | +1.46 | −2.30 | −2.64 | −1.18 | 29 % |
| simulation | AS base, myopic (δ = 2) | 975 | +2.00 | −2.92 | −3.21 | −1.21 | 32 % |

## The pattern is the same in both periods and every combination

- Quoting farther captures more (+0.9 to +2.0 bps), but the price then moves more against the position (−2.1 to −3.3 bps).
- The markout always ends at −1.16 to −1.31 bps.
- 80–90 % of the 10-second movement happens within the first second.
- Across deciles of E3's predicted intensity, the captured distance rises (0.42 → 2.24 bps), but the markout stays flat.

Better prediction of *when* orders arrive does not tell *which* fills will be toxic.

Run: `codigo/sa_v112.py`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
