# v90: curva monótona de distancia f(δ) en E3

Fecha: 2026-10-28. Estado: **aprobado por Santiago el 2026-10-29 sin cambios** (partición, umbrales y E3-f+kX como secundario).

## Pregunta
¿Sustituir el decaimiento exponencial −kδ de E3 por una función monótona decreciente f(δ) mejora el ajuste y la calibración por distancia fuera de muestra, sin perder discriminación?

E3 congelado (v45): log λ(t, δ) = g(X_t) + h(t) − kδ, con k escalar por lado.
E3-f (v90): log λ(t, δ) = g(X_t) + h(t) + f(δ), con f decreciente, f(δ₁) = 0 por identificación.

**Motivación (ya documentada):** O10 mostró que k no es estable en el bloque A (+27 % ask, −23 % bid). v47 (E3-kX) mejoró ll_pp en +4,1 % (ask) y +2,2 % (bid), pero su propia nota advierte que esa mejora "puede reflejar la forma del perfil en δ". v90 separa las dos cosas: forma en δ (f) frente a escala dependiente del estado (k(X)).

**Esto es una mejora de P1 (predicción). No dice nada sobre rentabilidad** (P2 queda pausada: §3.27).

## Especificación (fija antes de correr)
- **Datos, δ y respuesta:** idénticos a v45: rejilla δ ∈ {0,5; 1; 2; 3; 5; 7,5; 10; 15; 20} bps, bins de 1 s, mismas 44 covariables, misma respuesta (eventos agresores que cruzan mid(1 ± δ)).
- **Forma de f:** lineal a trozos sobre los 9 nodos de δ, monótona por construcción:
  f(δ_j) = −Σ_{i=2..j} exp(θ_i)·(δ_i − δ_{i−1}), j = 1..9 (8 parámetros por lado).
  Con θ_i iguales se recupera exactamente E3 (−kδ), así que E3 está anidado en E3-f.
  No hace falta interpolar: solo se evalúa en los 9 nodos. (SCAM de Pya y Wood es la referencia metodológica para una f suave si en el futuro se usa δ continuo.)
- **Estimación:** mismo backfit que v47 (copias de `modelo_kx.py`, sin editar el original): g con HistGradientBoosting Poisson e hiperparámetros congelados de v45; h como en v45 (ask con hora, bid sin hora); f por Newton amortiguado sobre θ dado η = g + h. **Número de iteraciones de backfit fijado en 3**, igual que v47, y se reportan ll_pp por iteración para ver la convergencia (cautela heredada de v47).
- **Modelos comparados (por lado):** E1, E1+h, E2 (congelados), E3 (k escalar), E3-kX, **E3-f**, y como secundario **E3-f+kX** (f(δ)·k(X)/k̄; solo si E3-f pasa la inclusión).

## Partición (solo entrenamiento 29 jun – 3 sep; guardia PermissionError para fechas posteriores)
- **Ajuste:** 29 jun – 12 jul (el mismo de v45/v47).
- **Inclusión:** calibración interna 13–16 jul (mismo uso que v47).
- **Evaluación:** 17 jul – 3 sep (≈ 49 días). **No es ciega**: estos días ya se vieron en la validación v52 y en las exploraciones económicas. Se declara.
- Test 4–20 sep y corrida libre 21 sep – 26 oct: **cerrados**. Usarlos para P1 requiere autorización explícita y una versión nueva de la partición.

## Criterios (fijos antes de correr)
1. **Inclusión (calibración interna, como v47):** ll_pp de E3-f > E3 en ≥ 3 de 4 días y mejora total ≥ 0,5 % de |ll_pp E3|.
2. **Principal (evaluación):** mejora de ll por bin de E3-f sobre E3 con IC95 bootstrap por días (2 000 réplicas, semilla 20261028) que excluye 0, y E3-f gana en ≥ 80 % de los días.
3. **Calibración por distancia:** para cada δ, razón observado/esperado (O/E) agregada en la evaluación. Éxito si la máxima |log(O/E)| sobre los 9 δ baja frente a E3, y la media de |log(O/E)| baja en ambos lados.
4. **Discriminación (no empeorar):** AUC a δ = 2 bps no baja más de 0,005 frente a E3.
5. **Frente a E3-kX:** se reporta la comparación directa (ll, O/E, AUC) para saber si lo que capturaba kX era forma o estado. No es criterio de éxito.

Paso 0 (diagnóstico, antes de ajustar E3-f): tabla O/E por δ de E3 y E3-kX congelados en la calibración interna. Si E3 ya está bien calibrado por δ (|log(O/E)| < 0,05 en todos los δ), se reporta y **se detiene v90**: no hay nada que arreglar.

## Salidas
`salida/` (JSON de resultados, O/E por δ y día, ll por día e iteración), `figuras/` (f(δ) estimada frente a −kδ, por lado; O/E por δ), `NOTA_V90.md`.

## Reglas
- Exploratorio respecto a la partición nueva; los criterios están fijados aquí para que el resultado no dependa de verlo.
- No se edita código de carpetas anteriores. No mercado, no servicios externos.
- Si la reproducción de E3 congelado (totales ll de v45/v47 en ajuste: ask −418 255, bid −468 377) no coincide, se detiene y se reporta.

## Decisiones pendientes de Santiago
- Aprobar o cambiar la partición (en particular, si la evaluación 17 jul – 3 sep es aceptable sabiendo que no es ciega).
- Aprobar los umbrales de los criterios 1–4.
- Confirmar si E3-f+kX entra como secundario o se omite para ahorrar tiempo.
