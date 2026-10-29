# v37: resumen v36 con interpretación corregida (2026-10-26)

> Cifras de v36 sin recalcular. Se obtuvieron con el código anterior a la censura de horizontes de v37 (afecta como mucho a las ejecuciones de los últimos H segundos de cada día) y con el AUC sin rangos medios. Todas las conclusiones se limitan al modelo, a la muestra (ajuste y calibración interna) y a la política examinados: cotización simétrica alrededor del mid, cruces hipotéticos sin cola. **Un cruce hipotético no es un fill, y nada aquí demuestra rentabilidad.** La causalidad de X frente al target está PENDIENTE (ver `NOTA_V37.md`).

## Qué se hizo

- **Modelo E3, según el anteproyecto:** λᵢ(t,δ|X) = exp(gᵢ(X) + hᵢ(hora UTC))·e^{−kᵢδ}.
  - g se estima con HistGradientBoosting (pérdida Poisson); RF se usa como robustez.
  - h es la hora UTC, centrada.
  - k se obtiene por perfil, con backfitting.
  - Familias: Poisson y "NB con media Poisson fija" (solo se perfila α; la media no se reajusta bajo NB).
- **Datos:** capa canónica de 100 ms (`Comparativa 1/binance_canonical_100ms_unified_v1_…`), 44 covariables en 4 grupos (libro, OFI, volatilidad, flujo), y `trades_event` agrupados en eventos agresores (mismo tiempo de ejecución y lado). Bins de 1 s y δ de 0,5 a 20 bps.
- **Partición del anteproyecto:** ajuste del 29 de junio al 12 de julio y calibración interna del 13 al 16 de julio. Validación, test y robustez están cerrados por candado.

## Resultados (calibración interna, 4 días)

| Modelo | ll ask | ll bid |
|---|---|---|
| E1 (A·e^{−kδ}) | −903 215 | −803 621 |
| E1 + h(hora) | −789 821 | −758 297 |
| **E3-GBM Poisson** | **−426 463** | **−478 516** |
| E3-RF Poisson | −423 054 | −467 766 |

- **E3 frente a E1:** E3 gana a E1 en los 4 días y en los dos lados. El AUC de "al menos un cruce a 2 bps en 1 s" es 0,84, frente a 0,82 en el piloto del anteproyecto.
- **Ablaciones:** el flujo de trades es el grupo que más aporta, seguido de volatilidad y libro. El OFI aporta casi nada una vez incluidos los demás. h ayuda en el lado ask, pero no en el bid.
- **Distancia:** k_ask = 0,62/bps y k_bid = 0,75/bps. A 7,5 bps, la intensidad cae al ≈1 % (ask) y al ≈0,4 % (bid) de λ₀.
- **NB con media Poisson fija:** α ≈ 70. Esta variante mejora la verosimilitud de recuentos frente a Poisson, pero no es un ajuste propio de la media NB.
- **RF frente a GBM:** el RF es algo mejor, pero 35 veces más lento. El GBM aún no tiene los hiperparámetros ajustados.

## ¿Puede ser rentable?

**Todavía no se puede afirmar ni descartar.** Lo demostrado es que E3 **predice mejor cuándo llegan los cruces**, que es la parte de intensidad (P1 del anteproyecto). La rentabilidad (P2) depende de tres cosas que aún no están medidas:

1. **Fill real:** que un trade cruce el precio no significa que la orden se llene. Falta el replay L2 con la cola: la orden se coloca detrás de la cantidad visible.
2. **Selección adversa:** lo que hace el precio después de ejecutarse la orden (markouts).
3. **Comisión:** con 7,5 bps por lado, un ciclo completo cuesta 15 bps.

**Cuenta rápida con la comisión de 7,5 bps:**
- Para cubrir solo la comisión hay que cotizar a δ ≥ 7,5 bps por lado.
- A esa distancia, en bins de 1 s, la tasa de cruce es de unos 0,02/s en el lado ask y 0,01/s en el bid (día de ejemplo, 29 de junio). Eso equivale a unas 40–80 oportunidades por hora y lado, y es una **cota superior**, porque no todo cruce es un fill.
- Esos cruces ocurren cuando el precio se mueve 7,5 bps o más en menos de un segundo. Es plausible que la selección adversa sea mayor en esos momentos (hipótesis, no medida aquí).

**Dónde podría estar el valor del modelo:** no en cotizar más lejos, sino en **retirar o ensanchar las cotizaciones cuando E3 prevé ráfagas de flujo** (evitar los fills malos) y estrecharlas cuando prevé calma. Es una pregunta empírica que solo responde el backtest.

**Prueba barata e informativa antes del backtest completo:** con los días de ajuste, medir el **markout** de cada cruce, es decir, cuánto se mueve el mid 1 s, 10 s y 60 s después de que un trade cruce mid ± δ.
- Si, para δ ≥ 7,5 bps, el mid sigue en promedio más allá de la cotización, vender o comprar en ese punto pierde antes de la comisión, y esta política (simétrica al mid, sin cola) no cubriría 7,5 bps; no dice nada de otras políticas.
- Si el markout revierte, hay margen y vale la pena el backtest completo con cola, inventario y HJB.

## Pendiente

- Ajustar los hiperparámetros del GBM y decidir sobre h y el OFI, usando solo la calibración interna.
- Corregir el AUC con empates.
- E2 (Hawkes) con la misma partición.
- Prueba de markouts.
- Replay L2 con cola y PnL como función de la comisión (rejilla de 0 a 10 bps).
- Abrir la validación externa, que requiere autorización.

## Prueba de markouts (bloque de ajuste, 14 días): resultado

Script `markouts_ajuste.py`; salida en `salida/MARKOUTS_AJUSTE.json`.

**Metodología:**
- En cada segundo se pone una cotización hipotética a mid·(1 ± δ). Se cuenta como ejecución el primer evento agresor que la alcanza. Es una cota superior porque no hay cola.
- El markout es el resultado por ejecución **antes de comisión**, valorando el inventario al mid H segundos después.
- **Control de signo:** con ejecuciones en momentos aleatorios, el markout es ≈ +δ, como debe ser.

| δ (bps) | Ejecuciones/día (ask) | Markout ask 1 s / 10 s / 60 s | Markout bid 1 s / 10 s / 60 s |
|---|---|---|---|
| 0,5 | 5 467 | −0,88 / −1,26 / −1,31 (0/14 días positivos) | −0,85 / −1,25 / −1,24 (0/14) |
| 1 | 2 869 | −0,93 / −1,25 / −1,28 (0/14) | −0,88 / −1,22 / −1,11 (0/14) |
| 2 | 860 | −1,15 / −1,36 / −1,27 (0/14) | −1,01 / −1,27 / −1,02 |
| 5 | 92 | −1,71 / −1,74 / −1,10 | −1,18 / −1,27 / −0,80 |
| 7,5 | 30 | −2,34 / −2,70 / −1,56 | −0,61 / −1,06 / +0,01 |
| 10 | 12 | −2,79 / −3,57 / −1,01 | +0,69 / +0,25 / +0,95 (pocas ejecuciones, ruido alto) |

**Lectura:**
1. **Sin comisión, el markout medio por cruce hipotético de la cotización estática y simétrica es de unos −1 bps** en todas las distancias hasta 5 bps, en los 14 días y en ambos lados. En promedio, el mid a H se mueve en contra más que δ. Es consistente con selección adversa, en esta muestra y con cruces hipotéticos.
2. **Con 7,5 bps de comisión** la pérdida por ejecución está entre 8 y 10 bps. Las ejecuciones a 10–15 bps en el lado bid son pocas (2–8 al día) y demasiado ruidosas para afirmar nada.
3. **Cola: efecto no medido.** Con cola, solo se llenarían algunos de estos cruces. Que el markout medio de los llenados sea mejor o peor que el de todos los cruces es una pregunta empírica que requiere el replay L2; no se afirma en ninguna dirección.
4. **Consecuencia para la tesis:**
   - El problema principal no es la comisión, sino **qué ejecuciones se aceptan**.
   - Una política útil debe condicionar la cotización a la **selección adversa esperada**, no solo a la intensidad: retirarse o ensanchar cuando E3 prevé flujo informado.
   - Esto sugiere estimar, junto a λ(t,δ|X), el **markout esperado dado X** (otro objetivo para el mismo GBM) e incluirlo en la recompensa de la HJB.

## Filtro de toxicidad (ajuste → calibración interna): resultado negativo

Script `filtro_markout.py`; salida en `salida/FILTRO_MARKOUT.json`.

**Diseño:**
- Un GBM predice el markout a 10 s de cada ejecución usando X_t, el estado del mercado al cotizar, antes de la ejecución, más δ (de 0,5 a 5 bps).
- Se entrena en ajuste. Los umbrales se fijan en ajuste con validación cruzada por días, y la evaluación se hace en la calibración interna.

**Resultado:**
- **Ask:** la correlación entre lo predicho y lo real es −0,03. Todos los deciles quedan entre −1,2 y −1,6 bps, y el decil "más seguro" es incluso peor (−1,46). El top 5 % da −1,90 bps.
- **Bid:** la correlación es 0,06. El top 5 % da +0,04 bps de media, pero por día sale −1,13 / +1,57 / −1,98 / −0,71: no es estable.

**Lectura:**
- Con renovación de cotizaciones cada 1 s, el estado del mercado al cotizar **no permite anticipar** qué ejecuciones serán tóxicas. La información que delata a la ejecución mala llega dentro del propio segundo: Hawkes estimó una memoria de unos 17 ms.
- Con esta forma de cotizar (estática, simétrica, renovada cada 1 s) y con cruces hipotéticos, el markout medio es negativo antes de comisión. El GBM examinado sobre X_t no lo volvió positivo en la calibración interna; otros modelos, covariables o políticas no se probaron.
- **Lo que queda por probar:** filtrar a la escala del agrupamiento, renovando cada 100 ms con X_t de como mucho 100 ms de antigüedad. Esto requiere declarar la latencia de forma explícita, porque en la realidad cancelar también tarda.

## Filtro de toxicidad a 100 ms: E1 / E2 / E3 / E3+E2 (ajuste → calibración interna)

Script `filtro_100ms.py`; salida en `salida/FILTRO_100MS.json` y registro en `filtro_100ms.log`.

**Supuestos:**
- Renovación de la cotización cada 100 ms, con **latencia cero** (supuesto optimista).
- Ejecuciones como cota superior (sin cola), δ de 0,5 a 5 bps y markout a 10 s.
- Hawkes ajustado con 3 días de ajuste (1,2 millones de eventos): μ = (1,55; 1,31), α propio ≈ 0,35–0,40, **β ≈ 183/s (unos 5 ms)** y ρ = 0,40.

| Lado | E1 sin filtro | E2 top 10 % | E3 top 10 % | E3+E2 top 10 % | Mejor decil (E3) | Peor decil (E2/E3) |
|---|---|---|---|---|---|---|
| ask | −1,47 | −1,35 | −1,74 | −1,93 | – | −2,6 |
| bid | −1,26 | −1,06 | +0,24 | +0,16 | −0,22 | −1,6 |

**Por día (top 10 %):**
- **bid E3:** −1,48 / **+2,97** / −1,56 / −0,87. El resultado positivo se debe a un solo día (14 de julio).
- **ask:** todos los días son negativos con todos los filtros.

**Lectura:**
1. **Ninguno de los filtros examinados** (GBM sobre E2, E3 y E3+E2) dio un markout positivo y estable entre días, con renovación cada 100 ms y latencia cero. Las correlaciones entre predicción y realidad están entre 0,05 y 0,15.
2. **Los filtros sí identifican las peores ejecuciones:** el peor decil está en unos −2,6 bps frente a −1,47 de media en el lado ask. Retirarse en esos momentos **reduce la pérdida**, pero no la convierte en ganancia.
3. **E2 frente a E3:** E2 (Hawkes) es más estable como detector del peor decil. E3 capta más varianza en el lado bid, pero de forma inestable entre días. La combinación E3+E2 no supera a E3.

**Conclusión económica provisional**, con 14 días de ajuste y 4 de calibración, a falta del replay con cola:
- En esta muestra de BTCUSDT spot y con cruces hipotéticos, la cotización simétrica alrededor del mid tiene markout medio negativo antes de comisión, también con los filtros examinados.
- Con comisión retail (7,5 bps), el markout neto por cruce hipotético sería de unos −9 bps.
- La contribución defendible del modelo es predictiva (P1): estima mejor la intensidad y detecta las ejecuciones peores. No se ha mostrado una estrategia rentable.
- Para explorar rentabilidad habría que cambiar la política, por ejemplo con una referencia distinta del mid (microprecio o precio de reserva con sesgo direccional), un horizonte de inventario más largo o un rebate maker.
