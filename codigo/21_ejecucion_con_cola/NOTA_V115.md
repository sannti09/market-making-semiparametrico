# NOTA v115 — Ejecución con cola aproximada (robustez de la evaluación económica)

Plan `PLAN_V115.md`, sha256 `e736e3c2e79101f5cc4ace2b2557886438ace498d2de6150ff2f097dd751bce3` (sellado el 30 oct 23:41, antes de correr; verificado al arrancar). Corridas: test 30 oct 23:43–23:49 (347 s); simulación 30 oct 23:50–31 oct 00:03 (800 s). Modelos v108 y políticas v110 congelados; solo cambia la regla de ejecución.

## Controles
- **R0 reproduce exactamente** v110 en los 17 días del test y v111 en los 36 días de la simulación (ejecuciones y PnL por día, todas las combinaciones, dif. < 1e-9).
- La primera ejecución de la simulación se detuvo porque `19_simulacion/salida/por_dia_econ_v111.json` no estaba en el repositorio. Se copió desde la carpeta original de la corrida v111 (su `resultados_v111.json` y su log son idénticos byte a byte a los del repositorio) y se relanzó sin cambiar el código.

## Qué permiten los datos
- Los 20 niveles por lado de la capa canónica llegan a ~0,4–0,5 bps del mid. La cola en el precio de la orden solo es visible cuando la política cotiza en el mejor precio o muy cerca.
- Con la HJB, las políticas con E3 cotizan a menudo ahí (por el sesgo de inventario y el cociente entre lados): en el test, ~142 000 segundos con transacciones exactamente a su precio, con la cola visible el 99 % de las veces. AS y Hawkes, ~2 000–3 000 segundos.

## Resultados (PnL bruto por ejecución, bps [IC95 por días])

Nombres: R1 «ejecución optimista al toque» es la regla «toque sin cola» del plan; R2 «FIFO aproximada con profundidad imputada» es la «cola FIFO aproximada» del plan. Las reglas son las mismas.

| Política HJB exacta | Regla | Test (17 días) | Ejec./día | Simulación (36 días) | Ejec./día | Días > 0 (sim.) |
|---|---|---|---|---|---|---|
| E3 tesis | R0 cruce estricto | −1,32 [−1,42; −1,21] | 2 451 | −1,26 [−1,33; −1,18] | 2 375 | 0/36 |
| E3 tesis | R2 FIFO aproximada con profundidad imputada | −1,32 [−1,42; −1,21] | 2 454 | −1,25 [−1,33; −1,18] | 2 378 | 1/36 |
| E3 tesis | R1 ejecución optimista al toque | +0,11 [−0,00; +0,24] | 7 320 | +0,15 [+0,08; +0,24] | 6 835 | 30/36 |
| E3 base | R1 | +0,35 [+0,24; +0,47] | 7 769 | +0,44 [+0,37; +0,51] | 7 018 | 35/36 |
| GLM 49 (E1+X49) | R1 | −0,59 [−0,70; −0,46] | 3 862 | −0,49 [−0,57; −0,41] | 3 805 | 4/36 |
| AS y Hawkes (7 variantes) | R0, R1, R2 | −1,22 a −1,29 | 2 200–4 000 | −1,20 a −1,26 | 2 100–4 200 | 0–1/36 |

- **R2 ≈ R0** en todo: cambio máximo con la HJB de 0,003 (test) y 0,005 bps (simulación). Con la cola visible o imputada y avance solo por transacciones, la orden casi nunca llega a ejecutarse en su precio (42 ejecuciones extra en 17 días para E3 tesis). Esto muestra que el resultado no cambia **bajo esos supuestos**; no demuestra que la cola real produzca el resultado de R0.
- **R1 cambia solo la HJB con E3 y con el GLM 49**: E3 tesis pasa de −1,3 a ≈ +0,1/+0,15 bps, con el triple de ejecuciones y markout agregado a 10 s ≈ 0 (frente a −1,24). Con AS y Hawkes el cambio es ≤ 0,07 bps.
- **GLFT y la regla miope:** cambio ≤ 0,03 (test) y ≤ 0,02 bps (simulación) con cualquier regla.
- Con R1, E3 tesis supera con la HJB a todos los modelos AS y Hawkes por ≈ +1,35 bps por ejecución (IC excluye 0 en los dos periodos). Con R0 y R2 no.

## Lectura fijada en el plan
- *Conclusión económica se mantiene* (IC95 superior < 0 en todas las combinaciones con miope, HJB exacta y GLFT): **no se cumple con ninguna regla, ni con R0**, porque la política de δ fijo 5 (126 ejecuciones/día) tiene un IC muy ancho (hasta +0,96 en el test y +3,6 en la simulación). El código incluyó las políticas de δ fijo; el plan hablaba de "modelo". **Restringido a los 11 modelos (lectura añadida después de ver los resultados, declarada):** se mantiene con R0 y R2 en los dos periodos; no con R1, por la HJB con E3 (extremo superior +0,47 en el test y +0,51 en la simulación, E3 base).
- *E3 gana con la HJB exacta:* solo con R1 (test y simulación).
- *Poco sensible a la cola* (|cambio| < 0,2 bps en la HJB con R1 y R2): **no**; R1 cambia la HJB con E3 en +1,4 a +1,7 bps.

## Interpretación y limitaciones
- Para AS, Hawkes, GLFT y la regla miope, las tres reglas dan el mismo resultado (diferencias ≤ 0,07 bps).
- Para la HJB con E3 el resultado bruto depende de la regla: −1,26 bps con cruce estricto o FIFO aproximada y +0,15 bps con ejecución optimista al toque (simulación).
- **R1 es un escenario optimista, no una estimación de la prioridad real:** supone que la orden se ejecuta completa en cuanto un agresor negocia a su precio, como si no tuviera cola delante. No prueba que más velocidad volviera rentable a E3.
- **R2 es una FIFO aproximada con profundidad imputada:** usa la cantidad mostrada cada 100 ms (o la mediana de los 20 niveles cuando el precio está más lejos), no cuenta las cancelaciones de quienes están delante y pierde la prioridad cada segundo. Los datos de 100 ms no permiten saber dónde cae la cola real entre R2 y R1.
- **Neto de comisiones:** con las comisiones maker evaluadas en la tesis (7,5 y 10 bps por ejecución), ninguna política es rentable con ninguna de las tres reglas: la mayor ganancia bruta (+0,44 bps, E3 base con R1) queda muy por debajo. No se afirma nada para otras tarifas.
- **Mecanismo no verificado aquí:** que R1 añada ejecuciones en el mejor precio con poca selección adversa es una hipótesis compatible con el PnL y el markout agregados. Comprobarlo requiere analizar las ejecuciones individuales (captura frente a movimiento posterior, separando las que cruzan de las que solo tocan el precio); ese análisis es exploratorio y se reporta aparte.
- La lectura restringida a los 11 modelos se añadió después de ver los resultados (ver arriba).

## Archivos
- `codigo/cola_v115.py` (uso: `python cola_v115.py test|sim`).
- `salida/por_dia_v115_{test,sim}.json`, `salida/resumen_v115_{test,sim}.json` (todas las fichas y la lectura), `salida/tabla_v115_{test,sim}.md`, `salida/log_v115_{test,sim}.txt`, `salida/stdout_{test,sim}.txt`.
