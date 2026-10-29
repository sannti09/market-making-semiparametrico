# 06 · State modulation k(X) (development variant)

Tests whether the decay rate in distance should depend on the market state: k(X) = exp(c + b′z), with z = 10 s realised volatility, log trades in 5 s, own-side top-5 depth and top-5 imbalance.

## Result (`NOTA_KX.md`, 4 internal calibration days)

- Log-likelihood +4.1 % (ask) and +2.2 % (bid); the pre-set inclusion rule was met.
- AUC unchanged: k(X) shifts levels, not ranking.
- Effects are small (|b| ≤ 0.11 per standard deviation) and move GLFT quotes by about 0.6 bps between the 5th and 95th percentiles.

This variant led to the m(X) modulation of the final model (`05_`, `16_`). `modelo_kx.py` is the code; the protocol is sealed in `PROTOCOLO_KX.json`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
