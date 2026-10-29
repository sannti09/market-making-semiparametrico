# v49: HJB numérica con intensidades semiparamétricas (OE4), frente a GLFT (2026-10-27)

**Protocolo:** `PROTOCOLO_HJB.json` (pre-registrado, sha256 en `PROTOCOLO_HJB.sha256`). Código: `hjb_numerico.py` (solver, tabla), `test_hjb.py`, `corrida_hjb.py`. Salidas: `salida/RESULTADO_HJB.json`, `corrida_hjb.log`, `test_hjb.log`.

## 1. Derivación (apéndice)

**Modelo.** Mid brownian `dS = σ dW` (σ en bps/√s, en unidades de precio constante a efectos de la derivación). El agente cotiza una compra a `S − δ_b` y una venta a `S + δ_a`. Las ejecuciones llegan como procesos de Poisson de intensidad `Λ_b(δ_b) = A_b e^{−k_b δ_b}` y `Λ_a(δ_a) = A_a e^{−k_a δ_a}` (k puede diferir por lado). Efectivo `X`, inventario `q ∈ {−Q,…,Q}` (sin compra en `q = Q`, sin venta en `q = −Q`). Utilidad CARA con liquidación a mid en `T`:

`V(t,x,q,S) = sup E[ −exp(−γ(X_T + q_T S_T)) ]`.

**HJB.** Una compra ejecutada lleva `(x,q) → (x − S + δ_b, q+1)`; una venta, `(x,q) → (x + S + δ_a, q−1)`:

`0 = ∂_t V + ½σ² ∂_SS V + 1_{q<Q} sup_{δ_b} Λ_b(δ_b)[V(t,x−S+δ_b,q+1,S) − V] + 1_{q>−Q} sup_{δ_a} Λ_a(δ_a)[V(t,x+S+δ_a,q−1,S) − V]`, `V(T) = −exp(−γ(x+qS))`.

**Ansatz** `V = −exp(−γ(x + qS + θ(t,q)))`, con `θ(T,q) = 0`. Derivadas (`V < 0`): `∂_t V = −γ ∂_tθ · V`, `∂_SS V = γ²q² V`. Saltos: `V(x−S+δ_b,q+1)/V = exp(−γ(δ_b + θ(t,q+1) − θ(t,q)))` y `V(x+S+δ_a,q−1)/V = exp(−γ(δ_a + θ(t,q−1) − θ(t,q)))` (el término `qS` se cancela porque `S` no cambia en el salto). Se divide por `V < 0`, de modo que cada `sup` pasa a `inf`:

`0 = −γ∂_tθ + ½γ²σ²q² + 1_{q<Q} inf_{δ_b} Λ_b(δ_b)[e^{−γ(δ_b − p_b)} − 1] + 1_{q>−Q} inf_{δ_a} Λ_a(δ_a)[e^{−γ(δ_a − p_a)} − 1]`,

con `p_b(q) = θ(q) − θ(q+1)` y `p_a(q) = θ(q) − θ(q−1)`. Dividiendo por `−γ`:

**`0 = ∂_tθ − ½γσ²q² + 1_{q<Q} H_b(θ(t,q) − θ(t,q+1)) + 1_{q>−Q} H_a(θ(t,q) − θ(t,q−1))`**, `H_i(p) = sup_δ Λ_i(δ)(1 − e^{−γ(δ−p)})/γ`.

**Maximización.** Sea `f(δ) = e^{−kδ} − e^{γp}e^{−(k+γ)δ}`. `f'(δ) = 0 ⇔ e^{γδ} = (1 + γ/k) e^{γp}`, es decir

**`δ_i* = p + (1/γ) ln(1 + γ/k_i)`** (única, y máximo porque `f → 0⁺` en ∞ y `f(p) = e^{−kp}γ/(·)>0` se cumple en el punto crítico). En el óptimo `e^{−γ(δ*−p)} = k/(k+γ)`, `1 − e^{−γ(δ*−p)} = γ/(k+γ)` y `Λ(δ*) = A e^{−kp}(1+γ/k)^{−k/γ}`, luego

**`H_i(p) = A_i (1+γ/k_i)^{−k_i/γ} e^{−k_i p} / (k_i + γ)`.** (Límite `γ→0`: `A e^{−kp}/(e k)`, el caso Avellaneda-Stoikov sin aversión.)

**Sistema en τ = T − t.** `∂_τθ(q) = −½γσ²q² + 1_{q<Q} H_b(θ(q)−θ(q+1)) + 1_{q>−Q} H_a(θ(q)−θ(q−1))`, `θ(τ=0,q) = 0`. Es un sistema de `2Q+1` EDO no lineales, cooperativo (las derivadas cruzadas `k_i H_i` son ≥ 0) y con filas de jacobiano de suma cero.

**Caso lineal (Guéant 2017).** Si `k_a = k_b = k`, `w(q) = e^{kθ(q)}` cumple `∂_τ w = M w` con `M = diag(−½kγσ²q²) + k C (A_b·sub + A_a·sup)`, `C = (1+γ/k)^{−k/γ}/(k+γ)`: tridiagonal, solución `w(τ) = exp(Mτ)·1`. En el régimen de τ grande domina el autovector principal `w∞` y `θ(τ,q) ≈ cτ + ln w∞(q)/k`.

**Política estacionaria.** Para `τ → ∞`, `θ(τ,q) = cτ + θ∞(q)` (la deriva `c` es la tasa ergódica de utilidad). La política depende solo de las diferencias de `θ∞`:
`δ_b*(q) = (1/γ)ln(1+γ/k_b) + θ∞(q) − θ∞(q+1)`, `δ_a*(q) = (1/γ)ln(1+γ/k_a) + θ∞(q) − θ∞(q−1)`.
La aproximación GLFT de v41 es el desarrollo cuadrático para `γ` pequeño y `Q` grande: `p_b(q) ≈ (q+½)ω_b`, `p_a(q) ≈ −(q−½)ω_a`, `ω_i = √(σ²γ/(2k_iA_i) (1+γ/k_i)^{1+k_i/γ})`.

**Observaciones.** (i) `δ*` puede ser negativo (cruzar); el simulador lo limita a cotización pasiva (igual que v41). (ii) Invariancia: `θ∞` no cambia al escalar `(σ², A_a, A_b)` por `s > 0` (solo `c`); la política depende de `(σ²/A_a, A_b/A_a, k_a, k_b, γ)`. Esto reduce la tabla a 2 dimensiones (4 con `k(X)`).

## 2. Esquema numérico
- Estacionario: Euler implícito linealizado `(I − Δτ J)Δθ = Δτ F(θ)` con `Δτ` creciente (×1,7 por paso) hasta que `F(θ)` es constante entre estados (dispersión relativa < 1e-9); `I − Δτ J` es M-matriz (diagonal dominante, fuera de diagonal ≥ 0), por lo que es estable para cualquier paso. Después, Newton ergódico sobre `F(θ) = c·1` con `θ(0) = 0`. ~20 iteraciones, ~0,4 ms por solución con `Q = 10`.
- Temporal (solo para tests): RK4 con paso adaptativo `Δτ ≤ cfl/‖J‖_∞`.
- Tabla de búsqueda: rejilla en `(u = ln σ²/A_a, v = ln A_b/A_a)` [y `ln k_a, ln k_b`] con interpolación multilineal de `p_b(q), p_a(q)`. Rejillas: 2D `u ∈ [−7,4]` (74 nodos), `v ∈ [−5,5]` (41); 4D `u` 37, `v` 21, `k ∈ [0,3; 1,6]` 9 nodos por lado. Fuera de rejilla se recorta y se reporta la fracción.

## 3. Tests (`test_hjb.py`, unittest, 6/6 OK; `test_hjb.log`)
| Test | Verificación | Resultado |
|---|---|---|
| H cerrada | `H_i(p)` frente a supremo numérico (rejilla fina de δ) y argmax = `p + (1/γ)ln(1+γ/k)` | coincide (6 cifras; argmax a 1e-3) |
| (a) Guéant | k y A simétricos: RK4 en τ ∈ {1, 20, 150} frente a `exp(Mτ)·1`; estacionario frente al autovector principal; τ = 3000 converge al estacionario; caso A_a ≠ A_b con igual k | error < 1e-7 (temporal), < 1e-5 (estacionario, rango central) |
| (b) GLFT | γ ∈ {0,003; 0,01}, Q = 40, q ∈ [−4,4]: error máximo 0,007 y 0,018 bps (≈ 5–6 % de ω = 0,16 y 0,29 bps) | < 10 % de ω y decreciente con γ |
| (c) monotonía | `δ_b*(q)` creciente y `δ_a*(q)` decreciente (3 conjuntos de parámetros, k, A, σ distintos por lado) | cumple |
| (d) q = 0 | simétrico: `δ_a*(0) = δ_b*(0) = base + corrección` con corrección ∈ (0,1) bps; con σ → 0 la corrección es la de borde `(1/k)ln(1/cos(π/(2(Q+1))))` | exacto a 1e-6 |
| tabla | tabla 2D frente a la solución exacta en 60 puntos aleatorios | error < 0,05 bps |

## 4. Datos y modelos
Ajuste 2026-06-29…07-12 (14 días), calibración interna 07-13…07-16 (4 días); ningún otro bloque se tocó. E1, E3 y E3-kX reajustados en ajuste (E3: `k` coincide con la especificación congelada a < 1e-4; k = 0,620 ask / 0,747 bid, igual en E1, E2 y E3); E2 con la especificación congelada (Λ predictivo de 1 s con historia anterior a la fila de decisión, `A = Λ e^{a}`). σ constante (E1) = 0,465 bps/√s; los demás usan σ_t causal (EWMA, semivida 60 s). `E1s` es un control (E1 con σ_t).
El simulador es el de v41, reescrito con la política por bin; la corrida verifica que con la política GLFT reproduce `V41.simular` exactamente (PnL y ejecuciones) en un día de ajuste. Fracción de bins recortados a la rejilla de la tabla ≤ 0,06 %. Error de la tabla frente a la solución exacta (150 bins reales por celda): 2D ≤ 0,003 bps (|q| ≤ 5 y todo q); 4D (E3-kX) ≤ 0,006 / 0,017 / 0,039 bps para γ = 0,01 / 0,1 / 1. Tiempo de la corrida: 385 s (tablas 4D: 33–63 s por γ; ~0,4 ms por solución).

**Enmienda 1 al protocolo** (documentada en `PROTOCOLO_HJB.json`; el original está en `PROTOCOLO_HJB_original_sha_e1db8904.json`): la primera corrida (abortada por un error de código con k vectorial, antes de evaluar calibración) mostró en el chequeo de interpolación de E3 errores p99 de 0,4–0,8 bps por recorte de la rejilla (ln(A_b/A_a) de E3 llega a ±4). Se ampliaron los ejes de la tabla (u: [−7,4], v: [−5,5]) antes de cualquier evaluación en calibración. No cambia modelos, γ, simulador ni regla de selección. Se vieron resultados de ajuste de E1/E1s/E2 antes de la enmienda, pero esos modelos no cambian con ella.

## 5. Resultados
**γ seleccionado en ajuste** (máximo PnL/día con ≥ 100 ejecuciones/día): 0,01 en todos los casos salvo E1s-HJB (1,0). En ajuste, ninguna de las 30 configuraciones tiene PnL positivo (PnL/día entre −3 188 y −7 407).

**Calibración interna** (4 días, ejecución "atraviesa", sin comisión; una sola evaluación por celda; PnL en bps·unidad por día):

| Modelo | Política | γ | PnL/día | Días + | Ejec./día | PnL por ejecución | \|q\| medio |
|---|---|---|---|---|---|---|---|
| E1 | GLFT | 0,01 | −3 333 | 0/4 | 2 634 | −1,27 | 2,5 |
| E1 | HJB | 0,01 | −3 250 | 0/4 | 2 612 | −1,24 | 2,3 |
| E1s | GLFT | 0,01 | −3 372 | 0/4 | 2 606 | −1,29 | 2,7 |
| E1s | HJB | 1,0 | −3 644 | 0/4 | 2 731 | −1,33 | 0,4 |
| E2 | GLFT | 0,01 | −3 377 | 0/4 | 2 612 | −1,29 | 2,7 |
| E2 | HJB | 0,01 | −3 340 | 0/4 | 2 565 | −1,30 | 2,5 |
| E3 | GLFT | 0,01 | −3 360 | 0/4 | 2 706 | −1,24 | 2,5 |
| E3 | HJB | 0,01 | **−2 467** | 0/4 | 2 051 | −1,20 | 2,3 |
| E3-kX | GLFT | 0,01 | −4 678 | 0/4 | 3 632 | −1,29 | 2,6 |
| E3-kX | HJB | 0,01 | **−2 644** | 0/4 | 2 156 | −1,23 | 2,4 |

**Distancias óptimas en q = 0** (calibración; γ = 0,01; percentiles 5/50/95 en bps, ask y bid; diferencia absoluta media frente a E1 con la misma política):

| Modelo | GLFT δ_a* | HJB δ_a* | Δ vs E1 (GLFT / HJB, ask) |
|---|---|---|---|
| E1 | 1,64 (constante) | 1,62 (constante) | 0 / 0 |
| E1s, E2 | 1,61 / 1,63 / 1,68 | 1,61 / 1,62 / 1,67 | 0,02 / 0,02 |
| E3 | 1,62 / 1,66 / 1,71 | **−0,15 / 1,61 / 3,38** | 0,03 / **0,95** |
| E3-kX | 1,09 / 1,35 / 1,85 | **0,09 / 1,29 / 3,07** | 0,30 / **0,81** |

Con γ = 0,1 y 1 el patrón es el mismo (E3 HJB: Δ vs E1 ≈ 0,95 y 1,0 bps; GLFT: 0,08 y 0,33 bps). El detalle (bid, perfiles por q, todos los γ) está en `salida/RESULTADO_HJB.json` (`distancias`).

## 6. Interpretación para OE4 / P3
- **El solver numérico es correcto y reproduce la solución de Guéant**; para γ pequeño y Q grande GLFT es una buena aproximación en el centro del inventario. Con E1 (A, k constantes) HJB y GLFT difieren poco (δ en q = 0 a 0,02–0,03 bps; PnL −3 250 vs −3 333): la aproximación cerrada no pierde casi nada en el caso estacionario.
- **Con intensidades dependientes del estado, HJB y GLFT dejan de ser equivalentes.** En GLFT, A solo escala la pendiente de inventario (ω ∝ A^{−1/2}) y la distancia base no depende de A (hallazgo estructural de v41), por eso E3 y E2 casi no mueven las cotizaciones (Δ vs E1 ≈ 0,02–0,03 bps; E2 ≈ E1s). En la HJB numérica la razón A_b/A_a entra en las ecuaciones de θ de forma no lineal: cuando el modelo predice mucho más flujo comprador que vendedor, el inventario estacionario tiende a un lado y la política corrige con un sesgo en q = 0. Con E3 esto desplaza los cotizaciones ≈ 1 bps respecto a E1 (percentiles 5–95 de δ_a* en q = 0: −0,15…3,4 bps) y con E3-kX ≈ 0,8 bps. **Es la primera vez en el proyecto que P1 (E3/E3-kX) cambia de forma material la política óptima**, y lo hace por la vía de la razón de intensidades, no del nivel.
- **E2** (Hawkes, razón A_b/A_a entre e^{−0,3} y e^{0,3}) no distingue su política de la de E1 con σ_t (0,02 bps); su aporte predictivo es de nivel total, que la HJB no usa.
- **Rendimiento:** HJB con E3 y E3-kX mejora el PnL/día en calibración frente a su GLFT (−2 467 vs −3 360; −2 644 vs −4 678) y frente a E1 (−3 250 a −3 333), pero la ganancia viene de **menos ejecuciones** (2 051–2 156 vs 2 600–3 600/día) con el mismo PnL por ejecución (−1,2 bps): la política retira cotizaciones en los momentos de flujo desfavorable pero no elimina la selección adversa. **Ninguna configuración es rentable (0/4 días positivos en todas)**, igual que en v38–v41. Con 4 días y sin comisión no hay base para afirmar que HJB-E3 sea mejor que E1 en sentido estadístico; es un resultado descriptivo.
- Para OE4: la política óptima data-driven existe y se obtiene numéricamente con costo despreciable (tabla de búsqueda; ≈ 0,4 ms por solución); su efecto sobre la cotización es material con E3/E3-kX y nulo con E2, mientras que el efecto sobre la rentabilidad es nulo en signo y solo reduce volumen perdedor.

## 7. Cautelas
- **Cruce ≠ ejecución:** regla "atraviesa", sin cola; las distancias δ < 0 de la HJB (≈ 5 % de los bins con E3) se fuerzan a cotización pasiva, por lo que la política efectiva es truncada.
- **Latencia** de 100 ms más ~90 ms de retraso propio del LOB; la selección adversa de ≈ −1,2 bps por ejecución es del orden de la latencia, no de la política.
- **Liquidación al mid de cierre** y límite |q| ≤ 10; horizonte infinito (política estacionaria) frente a un día finito.
- **Coeficientes congelados:** el problema real tiene A, k, σ estocásticos; resolver con los valores del instante y suponerlos permanentes sobreestima la persistencia del desbalance de flujo (la razón A_b/A_a de E3 es transitoria, ventana de ~1 s), lo que explica sesgos extremos en q = 0. No es la solución de la HJB con estado; es una aproximación de orden cero (la corrección sería incluir X como variable de estado con dinámica estimada).
- E3 y E3-kX se evalúan con A estimado en ajuste (14 días, en muestra) y calibración fuera de muestra, 4 días; E3-kX viene de un backfit que no convergió del todo (v47). Selección de γ siempre en el extremo inferior de la rejilla (0,01), lo que sugiere que la rejilla no encuentra un óptimo interior: el PnL de ajuste decrece casi siempre con γ (menos aversión = cotizar más lejos y menos ejecuciones).
- 30 configuraciones en ajuste, todas reportadas; 10 evaluaciones en calibración.
