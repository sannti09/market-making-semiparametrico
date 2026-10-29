# 13 · Myopic market-making PnL with the original fit (superseded by 18)

Applies the same myopic rule to every model, δ* = argmax λ̂(δ)·δ, in the test period. Results in `tablas_tesis/T6_pnl_test.md`.

## Result

- **Every model loses about −1.3 bps per fill before fees, with 0 of 17 positive days** for δ ≤ 1 bps.
- Under this rule only the *shape* of λ̂ in δ matters, not its level:
  - models with a fixed shape all quote at δ = 1;
  - models with −kδ all quote at δ = 2;
  - only E3 moves δ with the state, and it does not do better (−1.34 vs −1.29 bps).
- With Binance maker fees (7.5–10 bps) every model loses −9 to −11 bps per fill.

The thesis reports the same table recomputed with the corrected curve in `18_`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
