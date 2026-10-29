# v106: PnL con la política HJB (y GLFT) en el test 4–20 sep, con las intensidades de los 11 modelos congelados v103 (29 oct; escrito antes de correr; Santiago eligió "Correr GLFT/HJB en el test")

**Para qué:** OE4–OE5 prometen evaluar la política óptima derivada de la HJB con cada intensidad, frente a AS y Hawkes. v105 usó la regla miope; aquí se usa la HJB.

**Datos y modelos:** carpeta canónica; test 4–20 sep; modelos v103 sin reajuste; predicciones idénticas a v104/v105. La corrida libre sigue cerrada.

**Intensidad exponencial local.** La HJB de v49 está resuelta para Λ_i(δ) = A_i e^{−k_i δ}. En cada segundo y en cada lado se ajusta log λ̂(δ) ≈ log A − kδ por mínimos cuadrados sobre δ ∈ {0,5; 1; 2; 3; 5} bps.
- Es exacto para E1 y E3 (−kδ).
- Para los modelos con f(δ), k es fijo por modelo (2D).
- Para E3-fkX(+B), k cambia con X (tabla 4D).
- Es una aproximación declarada para las formas f(δ).
- Los ejes de la tabla 4D se fijan con un día de entrenamiento (3 sep), no con el test.

**Volatilidad:** σ_t causal, igual para todos los modelos. Es la EWMA del cuadrado de los retornos de 1 s del mid en bps, con semivida de 60 s y retornos hasta el inicio del bin, con piso de 1e-3.

**Política:**
- HJB estacionaria con coeficientes congelados (solver y tablas de v49, verificados con 6 tests), γ = 0,01 y Q = 10.
- γ es el que v49 eligió en entrenamiento para casi todos los modelos; no se ajusta nada en el test.
- Para comparar se incluye también GLFT (la aproximación cerrada) con los mismos A_t, k y σ_t.

**Simulador (el de v105):**
- Decisión al inicio de cada bin de 1 s con el inventario q de ese momento: δ_a(q) y δ_b(q).
- Cotización redondeada al tick y pasiva frente al BBO de la decisión.
- Una orden de 0,01 BTC por lado; no se cotiza el lado que llevaría |q| por encima de 10.
- Hay ejecución si llega un agresor estrictamente más allá del precio dentro del segundo; como mucho una por lado y por segundo.
- PnL = efectivo + q × último mid del día.

**Métricas:** las de v105.
- PnL por ejecución (bps), PnL/día (USDT), días > 0, ejecuciones/día, |q| medio, markouts a 10 y 60 s.
- IC95 bootstrap por días (2 000 réplicas, semilla 20261029), y diferencia pareada E3 tesis − cada modelo.

**Lectura esperada (v49, calibración):** todas negativas, ≈ −1,2 bps por ejecución; con E3, la HJB reduce el número de ejecuciones. Informativo, sin criterio de éxito.
