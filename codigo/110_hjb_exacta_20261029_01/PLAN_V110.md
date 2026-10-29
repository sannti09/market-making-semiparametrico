# v110: HJB exacta con la curva real de cada modelo (29 oct; escrito antes de correr nada)

**Estado del test.** El test 4–20 sep ya fue consultado antes: v104 (predictivo, modelos v103), v105 (regla miope), v106 (HJB con exponencial local) y, con los modelos v108, nada económico todavía. v110 REEMPLAZA la versión aproximada de v106 (misma pregunta, HJB sin aproximar la curva) y NO es ciego. No se ajusta nada con el test: γ, Q, rejillas y criterios se fijan aquí; los ejes de m se fijan con el 3 sep (entrenamiento).

## Modelo
- Intensidad por segundo y lado: Λ_i(δ) = A_i · exp(g_i(δ)), con A_i = Λ_i(0,5 bps) (normalización: g_i(0,5) = 0) y g_i la curva log λ̂(δ_j) − log λ̂(0,5) en los 9 nodos δ_j = {0,5; 1; 2; 3; 5; 7,5; 10; 15; 20} bps, interpolada linealmente a trozos en log. Fuera de [0,5; 20] se extiende con la pendiente del primer y del último tramo.
- En cada tramo s: Λ = A·exp(c_s − k_s δ). Si algún k_s ≤ 0 (extrapolación o forma) se aborta y se reporta (no se trata en silencio); se cuenta además cuántos segundos de m quedan recortados al rango.
- Hamiltoniano exacto H_i(p) = sup_δ Λ_i(δ)(1 − e^{−γ(δ−p)})/γ. En cada tramo el máximo sin restricción es δ_s = p + (1/γ) ln(1+γ/k_s), recortado al tramo (tramo izquierdo hasta −100 bps, derecho hasta 2000 bps); H = máximo sobre los 8 tramos (incluye los extremos), δ*(p) = argmax; H'(p) = −Λ(δ*) e^{−γ(δ*−p)} (envolvente).
- Sistema estacionario igual que v49 (Euler implícito linealizado + Newton ergódico) con este H: ∂_τθ(q) = −½γσ²q² + 1_{q<Q} H_b(θ(q)−θ(q+1)) + 1_{q>−Q} H_a(θ(q)−θ(q−1)); política por diferencias de θ∞: δ_b*(q)=δ*_b(θ(q)−θ(q+1)), δ_a*(q)=δ*_a(θ(q)−θ(q−1)). γ = 0,01, Q = 10; unidades de v49 (δ en bps, t en s, A por s, σ en bps/√s). Invariancia: (σ², A_a, A_b) → s·(σ², A_a, A_b) no cambia θ∞.

## Tablas (el solucionador está en codigo/hjb_general.py; v49 se importa sin editar)
Las tablas guardan p_b(q), p_a(q) (diferencias de θ∞); δ* se evalúa después, exacto, con la forma del segundo.
- Modelos con forma fija (m ≡ 1; todos salvo E3-fkX+B y E3-fkX; incluye E1 y E3, que son exponenciales exactas y sirven de control frente a v106): tabla 2D en u = ln σ²/A_a, v = ln A_b/A_a, con A = Λ(0,5). Rejilla u ∈ [−7,5; 4,5] con 81 nodos, v ∈ [−5; 5] con 41 nodos. La forma g_a, g_b se toma de la mediana del 3 sep y se verifica que es constante entre segundos (desviación máx.). Una tabla por par de formas distintas.
- E3-fkX+B y E3-fkX: forma g = m·f(δ), f = curva del modelo (f(0,5)=0), m(X) por segundo y lado. Tabla 4D (u, v, m_a, m_b): u ∈ [−7,5; 4,5] con 41 nodos, v ∈ [−5; 5] con 21, m_a y m_b lineales con 9 nodos cada uno, rango = percentiles 0,1–99,9 de m del 3 sep ampliados ×0,9 / ×1,1 (como v106 con k). Fuera de rejilla se recorta y se reporta la fracción.
- Interpolación multilineal (la de Tabla de v49).

## Simulador y políticas (idéntico a v106/v105; funciones copiadas, no importadas)
Decisión al inicio de cada bin de 1 s con el q actual; cotización redondeada al tick y pasiva frente al BBO; ejecución si llega un agresor estrictamente más allá del precio; como mucho una por lado y segundo; |q| ≤ 10; 0,01 BTC; PnL = efectivo + q·último mid; markouts 10 y 60 s; IC95 bootstrap por días (2000 réplicas, semilla 20261029), diferencia pareada E3-fkX+B − cada modelo. σ_t: EWMA causal de v106 (semivida 60 s, piso 1e-3).
Políticas: (1) miope δ* = argmax λ̂(δ)·δ en la rejilla (como v105); (2) HJB exacta (nueva); (3) GLFT con exponencial local (como v106). Como control adicional informativo, HJB aproximada (v106: exp_local + tablas de v49) con los modelos v108, para separar el efecto de v108 del de la exactitud. Referencias δ fijo 0,5/2/5 con la regla miope para T6.
Modelos: modelos_finales_v108.pkl, con sha256 verificado contra MANIFIESTO_v108.json. Las predicciones salen de W.lls como en v106.

## Verificaciones (solo entrenamiento: 3 sep vía T.dia_aj; script verif_v110.py → salida/verificacion_v110.json)
(a) Con forma exponencial exacta la solución general reproduce estacionario() de v49: máx |Δ diferencias de θ| < 1e-8.
(b) H por tramos vs fuerza bruta (rejilla fina de 200 001 puntos en [p−5, p+100] más los nodos de la curva), error relativo < 1e-6, varias p y formas reales (todos los modelos y lados; E3-fkX(+B) con m mínimo, medio y máximo).
(c) Monotonía: δ_b*(q) creciente y δ_a*(q) decreciente en q para 20 segundos reales de cada modelo.
(d) Error de interpolación de cada tabla frente a la solución exacta en 150 segundos reales por modelo (3 sep): p99 < 0,05 bps en |q| ≤ 5.
Complementos informativos: constancia de la forma normalizada (m ≡ 1) y reproducción de m·f en E3-fkX(+B); positividad de k_s.
**Criterio de parada:** si alguna de las cuatro falla, se detiene, se guarda el informe y se reporta; no se corre el test. Si pasan, se corre econ_v110.py una sola vez.

## Supuestos declarados
Misma σ_t para todos los modelos; γ = 0,01 sin ajustar en el test; HJB estacionaria con coeficientes congelados en cada segundo (como v106); sin comisión.
