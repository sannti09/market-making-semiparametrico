# 14 · HJB and GLFT with a local exponential approximation (superseded by 18)

Applies the HJB of `08_` (γ = 0.01, Q = 10) to the 11 models, approximating each second's intensity curve by a local exponential.

## Result

- **All combinations lose about the same per fill:** −1.23 to −1.34 bps, with 0 of 17 positive days in all 22 combinations (11 models × HJB/GLFT).
- **E3 does change the policy:**
  - it quotes closer at q = 0 and withdraws when order flow is unbalanced;
  - it trades less: 1,729 fills/day vs 2,218 for AS;
  - it loses less per day: −176 vs −219 USDT, but not per fill.

`18_` replaces the exponential approximation with the exact interpolated curve.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
