# 02 · Response counts

Builds the response variable of every model: for each 1-second bin and each distance δ ∈ {0.5, 1, 2, 3, 5, 7.5, 10, 15, 20} bps, the number of aggressor events whose price reaches m_t(1 ± 10⁻⁴ δ) on the ask (buyers) or bid (sellers) side.

All models are compared on exactly these counts with a composite Poisson log-likelihood over the nine distances.

- `01_codigo/cargador_v58.py`: event extraction and counting.
- `NOTA_V58.md`: a development-phase evaluation that used this code. It is kept for traceability; it is not part of the final protocol.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
