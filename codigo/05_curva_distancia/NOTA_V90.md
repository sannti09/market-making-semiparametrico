# NOTA v90: curva monótona de distancia f(δ) en E3

Plan `PLAN_V90.md` (sha256 en `PLAN_V90.sha256`, verificado al inicio; aprobado por Santiago el 29 oct sin cambios). Solo entrenamiento: ajuste 29 jun–12 jul, inclusión 13–16 jul, evaluación 17 jul–3 sep. **La evaluación no es ciega** (días ya vistos en v52 y en las exploraciones económicas). Test y corrida libre cerrados (guardia: `PermissionError` > 3 sep, comprobado).

## Resultado corto
1. **Reproducción exacta.** E3 en calibración interna: ask −418 255, bid −468 377, idéntico a v45.
2. **Paso 0: E3 está muy mal calibrado por distancia.** La exponencial −kδ cae demasiado rápido: a 20 bps E3 subestima los cruces por un factor e^5,6 (ask) y e^8,1 (bid) en la evaluación. Con la curva libre, f(20) = −6,4 (ask) y −8,9 (bid), frente a −kδ = −12,1 y −14,6. Los δ ≤ 5 bps también tienen errores de 0,1–0,6 en log.
3. **E3-f cumple los cuatro criterios en los dos lados:**

| lado | Δll por bin E3-f − E3 [IC95 días] | días gana | max / media \|log O/E\| E3 → E3-f | AUC δ=2 E3 → E3-f |
|---|---|---|---|---|
| ask | +0,031 [+0,022; +0,044] (+3,45 %) | 45/45 | 5,61 / 1,35 → 0,41 / 0,23 | 0,8219 → 0,8219 |
| bid | +0,032 [+0,016; +0,057] (+3,38 %) | 45/45 | 8,15 / 2,06 → 2,35 / 0,62 | 0,8195 → 0,8195 |

   Inclusión (cal. interna): ask 4/4, +3,37 %; bid 4/4, +2,66 %.
4. **Forma frente a estado (criterio 5, informativo).** E3-kX sigue mejor que E3-f en ll (ask −0,021, bid −0,038 por bin para E3-f − E3-kX; IC incluyen 0; E3-f gana 21/45 días). **La combinación E3-fkX es la mejor en ll**: +0,016 [+0,007; +0,025] (ask) y +0,011 [+0,004; +0,019] (bid) por bin sobre E3-kX. En calibración por δ, E3-fkX es la mejor en bid (max 0,52) y E3-f la mejor en ask (max 0,41). Ninguna variante cambia la AUC más de 0,002 (E3-fkX baja 0,001–0,002).
5. **Lectura:** la mejora de E3-kX de v47 era **en parte forma de la curva y en parte estado**: la forma sola recupera ≈ 60 % (ask) y ≈ 46 % (bid) de la mejora de kX, y las dos juntas superan a cada una. La discriminación (AUC) no cambia: esto es calibración de niveles por δ, no mejor ordenamiento temporal. P1 (E3 > E1, E2) no depende de esto, pero la verosimilitud de E3 con −kδ estaba penalizada por la forma.

## log(O/E) por δ en la evaluación (δ = 0,5 … 20 bps)
- ask E3: +0,12 −0,13 −0,48 −0,56 −0,32 +0,33 +1,21 +3,36 +5,61
- ask E3-f: −0,02 −0,09 −0,19 −0,26 −0,35 −0,41 −0,29 −0,22 −0,24
- bid E3: −0,08 −0,27 −0,49 −0,43 +0,14 +1,28 +2,56 +5,10 +8,15
- bid E3-f: −0,18 −0,22 −0,24 −0,23 −0,19 +0,14 +0,67 +1,39 +2,35
- Tablas completas (E3-kX, E3-fkX, todas las comparaciones): `salida/tablas_v90.md`.

## Método (detalles y desviaciones declaradas)
- **Estimación de f.** Con g y h fijos, el máximo de la verosimilitud en f es cerrado: f_j = log(N_j/N_1), con N_j el total de cruces a δ_j en el ajuste. Como los cruces están anidados, N_j no crece y f es monótona sin que la restricción se active. Es exactamente la parametrización del plan (θ_i libres) resuelta en forma cerrada, **no por Newton** como decía el plan; el resultado es el mismo máximo. E3-fkX (log λ = η + m(X)·f(δ), m = exp(b·z), mismas 4 z de v47) sí usa L-BFGS con gradiente analítico (verificado contra numérico, error 4e-5).
- Backfit de 3 iteraciones en todos los modelos (como v47); historiales en `resultados_v90.json`.
- **Días de evaluación: 45, no ≈ 49.** Del 22 al 25 ago no hay capa canónica (fin de v1 el 24 ago 12:00, v2 empieza el 26 ago). Se usa el cargador de v58 (capas v1/v2) importado sin editar, con tope 3 sep.
- **Sin figuras:** el entorno `04_entorno/venv_e3` no tiene matplotlib; no se instaló nada. Los datos de las figuras previstas están en `salida/analisis_v90.json`.
- E1, E1+h y E2 no se reajustaron (sus comparaciones con E3 ya están en v52–v59 y ningún criterio de v90 los usa).

## Cautelas
1. **Evaluación no ciega** (declarado en el plan).
2. **Deriva en bid a δ grandes:** E3-f queda en +1,4 / +2,3 a 15 / 20 bps, es decir, en la evaluación hay e^2 veces más cruces lejanos que en el ajuste (29 jun–12 jul). La forma de f se estimó en 14 días tranquilos; con más volatilidad posterior, la cola en δ cambia. E3-fkX lo corrige en parte (0,52) porque m(X) depende de la volatilidad.
3. Verosimilitud compuesta (filas δ anidadas), como en v34–v47: los Δll no son log-verosimilitudes independientes por δ.
4. Exploratorio frente a la partición nueva; criterios fijados antes de correr.

## Archivos
`codigo/modelo_f.py`, `codigo/corrida_v90.py`, `codigo/analisis_v90.py`; `salida/resultados_v90.json`, `salida/analisis_v90.json`, `salida/tablas_v90.md`, `salida/corrida_v90.log`; caché de bins en `salida/cache/` (≈ 2 GB, se puede borrar).

## Progresión de versiones de E3 (evaluación 17 jul–3 sep, 45 días; mejora de ll frente a E3 base, IC95 por días)
Todas comparten g(X) (GBM, 44 covariables) y h(t); solo cambia el término en δ.

| lado | versión | término en δ | Δll por bin vs E3 [IC95] | mejora rel. | días gana | max \|log O/E\| | AUC δ=2 |
|---|---|---|---|---|---|---|---|
| ask | E3 base | −kδ | — | — | — | 5,61 | 0,8219 |
| ask | E3-kX | −k(X)δ | +0,052 [+0,020; +0,108] | +5,8 % | 42/45 | 0,67 | 0,8220 |
| ask | E3-f | f(δ) | +0,031 [+0,022; +0,044] | +3,5 % | 45/45 | 0,41 | 0,8219 |
| ask | E3-fkX | m(X)·f(δ) | +0,068 [+0,038; +0,118] | +7,6 % | 45/45 | 0,74 | 0,8209 |
| bid | E3 base | −kδ | — | — | — | 8,15 | 0,8195 |
| bid | E3-kX | −k(X)δ | +0,070 [+0,016; +0,166] | +7,3 % | 35/45 | 1,08 | 0,8195 |
| bid | E3-f | f(δ) | +0,032 [+0,016; +0,057] | +3,4 % | 45/45 | 2,35 | 0,8195 |
| bid | E3-fkX | m(X)·f(δ) | +0,081 [+0,024; +0,177] | +8,5 % | 39/45 | 0,52 | 0,8174 |

Lectura: E3-fkX da el mejor ajuste; E3-f es la más estable (45/45 días en ambos lados). Ninguna cambia la discriminación. **Uso económico:** no se hace backtest; todas las δ ya probadas pierden (v39, v86, v88, v89), así que cambiar la δ elegida no cambia el signo (§3.27).

## v90b: robustez a la verosimilitud compuesta (ENMIENDA_V90B.md, escrita y con hash antes de correr)
- Reajuste con la misma semilla: totales de ll **idénticos** a v90 (diferencia 0). Se guarda la ll de Poisson **por δ** (cada δ por separado es una verosimilitud propia, no compuesta). Tablas: `salida/v90b/tablas_v90b.md`.
- **Criterio principal, δ = 2 bps: se cumple.** E3-f − E3: ask +0,0114 [+0,0077; +0,0145] (43/45 días), bid +0,0099 [+0,0079; +0,0121] (43/45). E3-fkX − E3: +0,0186 (44/45) y +0,0139 (45/45).
- **Por δ (IC>0 / ≈0 / <0):** E3-f − E3: ask 5/3/1, bid 7/1/1. Los únicos δ en contra son pequeños: ask δ=5 (−0,0003) y bid δ=0,5 (−0,0058, 13/45). **E3-fkX − E3: ask 6/3/0, bid 7/2/0, ningún δ en contra.**
- **Peso de los δ lejanos (≥ 7,5) en la mejora compuesta:** E3-f 25 % (ask) y 65 % (bid); E3-fkX 30 % y 55 %.
- **Matiz:** en δ ≥ 7,5 las mejoras tienen IC > 0 pero ganan pocos días (8–26 de 45): se concentran en los días volátiles. En δ = 2–3 la mejora es diaria (40–45/45).
- **Lectura:** la mejora de v90 no es un artefacto de sumar distancias anidadas. A la distancia de referencia de P1 (2 bps) todas las variantes superan a E3 base casi todos los días, y E3-fkX es la única sin ningún δ en contra en ninguno de los dos lados.

## Qué significa "gana" en v90/v90b (aclaración para la tesis)
"Gana" = mejor verosimilitud predictiva: las predicciones de cuántos agresores cruzan cada distancia δ del mid en el siguiente segundo, por lado, se parecen más a lo observado. **No es PnL** (no se simula ninguna operación; el market making sigue en ≈ −1,2 bps por ejecución con cualquier versión de E3, §3.27) **ni dirección** (el modelo no predice si el precio sube o baja; eso es ŝ). v90/v90b mejoran P1, no P2.
