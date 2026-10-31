# NOTA v115-fills (EXPLORATORIA): anatomía de las ejecuciones con R0 y R1

**Naturaleza:**
- Análisis exploratorio, sin protocolo previo: se diseñó después de ver los resultados de v115 para revisar la hipótesis de que las ejecuciones extra de R1 «ganan el spread casi sin selección adversa».
- No cambia ningún resultado de v115 ni de la tesis.
- Todavía no está decidido si entra en el documento.

**Corrida:**
- `codigo/fills_v115.py` reutiliza `cola_v115.py` sin editarlo: mismas cotizaciones, inventario y reglas.
- Cubre solo la HJB exacta, con tres intensidades: E3 tesis, E3 base y E1.
- Primer intento: falló al resumir por un error de dimensión (registros de 7 campos tratados como de 8). Se corrigió y se relanzó completo; los logs de v115 no se tocaron.

**Control:** el número de ejecuciones coincide exactamente con v115 en los dos periodos, en las seis combinaciones. Por ejemplo, E3 tesis con R1 da 124 433 en el test y 246 074 en la simulación.

## Definiciones
- **Por cruce:** antes del instante de la ejecución, en ese segundo, hubo alguna transacción agresora estrictamente más allá del precio de la orden.
- **Solo toque:** la ejecución la dispara una transacción exactamente al precio, sin transacciones más allá antes de ella. La clasificación se hace en el instante de la ejecución; puede haber transacciones más allá después, dentro del mismo segundo.
- **En el mejor precio:** la orden estaba en el mejor bid o ask al inicio del segundo.
- **Captura:** precio de la orden frente al mid de la decisión, en bps, con signo a favor del market maker.
- **Markout a H s:** precio de la orden frente al mid en el instante de la ejecución más H s (convención de v110; incluye la captura).
- **Movimiento:** markout − captura (aproximado).

## Resultados (HJB exacta, medias por ejecución en bps)

| Periodo | Intensidad | Regla | Tipo | n | % | En mejor precio | Captura | Markout 1 s | Markout 10 s | Markout 60 s |
|---|---|---|---|---|---|---|---|---|---|---|
| Test | E3 tesis | R0 | por cruce | 41 675 | 100 | 0,07 | +1,08 | −1,00 | −1,28 | −1,34 |
| Test | E3 tesis | R1 | por cruce | 39 858 | 32 | 0,02 | +1,15 | −0,99 | −1,27 | −1,33 |
| Test | E3 tesis | R1 | solo toque | 84 575 | 68 | 1,00 | +0,004 | +0,10 | +0,56 | +0,78 |
| Test | E3 base | R1 | solo toque | 106 431 | 81 | 1,00 | +0,003 | +0,10 | +0,55 | +0,76 |
| Test | E1 | R1 | solo toque | 428 | 1 | 0,39 | +0,89 | −0,45 | −1,00 | −0,12 |
| Sim. | E3 tesis | R0 | por cruce | 85 507 | 100 | 0,06 | +1,04 | −0,89 | −1,24 | −1,30 |
| Sim. | E3 tesis | R1 | por cruce | 81 982 | 33 | 0,02 | +1,10 | −0,88 | −1,23 | −1,28 |
| Sim. | E3 tesis | R1 | solo toque | 164 092 | 67 | 1,00 | +0,004 | +0,13 | +0,62 | +0,81 |
| Sim. | E3 base | R1 | solo toque | 204 767 | 81 | 1,00 | +0,002 | +0,13 | +0,61 | +0,79 |
| Sim. | E1 | R1 | solo toque | 614 | 1 | 0,22 | +1,14 | −0,55 | −1,15 | −1,46 |

**Captura de las ejecuciones de solo toque con E3:**
- Es positiva en el 100 % de los casos.
- Mediana: 0,0006 bps, que es medio tick frente al mid (percentiles 5–95: 0,0006–0,0007).
- Media: 0,002–0,004 bps.
- No es exactamente cero: es el medio spread de un mercado con spread de un tick, ≈ 0,001 bps.

**Markout a 10 s de esas mismas ejecuciones:**
- Media: +0,55 a +0,62 bps.
- Mediana: +0,18 a +0,29 bps.
- Positivo en el 83–85 % de los casos.

## Lectura (prudente)
- **R1 añade otro tipo de ejecución.** Con E3, R1 añade sobre todo ejecuciones en el mejor precio disparadas por transacciones exactamente a ese precio. Su markout medio es positivo, mientras que el de las ejecuciones por cruce es negativo (≈ −1,27 bps) e igual al de R0.
- **El PnL de R1 no viene de capturar spread.** La captura de esas ejecuciones es la de un tick (medio tick frente al mid, ≈ 0,0006 bps). Lo que las distingue es un movimiento posterior del mid a favor, en promedio.
- **Lo que esto no demuestra:**
  - que R1 seleccione exclusivamente episodios de «toque y rebote»: la clasificación se hace en el instante de la ejecución y no examina la trayectoria completa del precio;
  - cuántas de esas ejecuciones obtendría una orden real, que depende de su posición en la cola.
- **Lo que sí respalda** es que las ejecuciones al toque y las ejecuciones por cruce tienen markouts distintos. Por eso el supuesto de cola de R1 es el que determina el resultado, y R1 debe leerse como escenario optimista.
- **Con AS (E1)**, las ejecuciones de solo toque son pocas (≈ 1 %) y su markout no es favorable.

## Archivos
- `codigo/fills_v115.py` (uso: `python fills_v115.py test|sim`).
- `salida/fills_v115_{test,sim}.json`: resumen por tipo.
- `salida/fills_v115_{test,sim}.npz`: una fila por ejecución con lado, por cruce, en mejor precio, captura y markout a 1, 10 y 60 s.
- `salida/stdout_fills_{test,sim}.txt`.
