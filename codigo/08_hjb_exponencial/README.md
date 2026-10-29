# 08 · HJB solver with exponential intensity

Numerical solution of the Guéant market-making problem (CARA utility, inventory |q| ≤ Q) when each side's intensity is Λ(δ) = A·e^(−kδ).

- **Equation:** ∂_τ θ = −½γσ²q² + H_b + H_a, with the Hamiltonian in closed form, H(p) = A(1 + γ/k)^(−k/γ) e^(−kp) / (k + γ).
- **Optimal quote:** δ* = p + (1/γ) ln(1 + γ/k).
- Full derivation in `NOTA_HJB.md`.

| File | Purpose |
|---|---|
| `hjb_numerico.py` | Solver and lookup tables |
| `test_hjb.py`, `test_hjb.log` | 6 tests, all passing: closed-form H vs numerical sup; the linear Guéant case; GLFT close at the centre of the inventory range; monotone quotes in q; zero inventory; table interpolation |
| `PROTOCOLO_HJB.json` | Sealed protocol (γ, Q, grids) |

The thesis uses γ = 0.01 and Q = 10. Folder `18_` generalises the solver to the exact (piecewise) distance curve.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
