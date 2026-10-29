# NOTA v105 — PnL de market making en el test 4–20 sep (29 oct; informativo, P2 pausada)
- Regla AS miope δ* = argmax λ̂(δ)·δ, igual para todos los modelos. Modelos congelados v103. Ejecución estricta. Tabla: tablas_tesis/T6_pnl_test.md.
- **Todos pierden ≈ −1,3 bps por ejecución antes de comisiones; 0/17 días positivos con δ ≤ 1.** Coincide con v81–v89 (−1,2 a −1,3 en entrenamiento): ahora queda confirmado en el test.
- **Limitación de la regla:** con la regla miope solo importa la *forma* de λ̂ en δ, no su nivel.
  - Los modelos con forma fija (AS y Hawkes con f(δ), GLM) eligen siempre δ = 1, así que son la misma estrategia.
  - Los de −kδ (E1, E3 base) eligen siempre δ = 2, equivalente a δ fijo 2.
  - Solo E3-fkX(+B) cambia δ según el estado: −1,34 [−1,47; −1,19], frente a −1,29 de δ = 1 fijo. No es mejor.
- Con comisión maker de Binance (7,5–10 bps) todas pierden ≈ −9 a −11 bps por ejecución.
- **Lectura:** predecir mejor la intensidad de cruces (P1) no convierte el market making pasivo en rentable en BTCUSDT; la pérdida es selección adversa (markout −1,2 a −1,4 bps a 10–60 s), igual para todos los modelos.
