# PLAN v115 — Ejecución con cola aproximada (análisis de robustez de la evaluación económica)

Escrito el 30 oct 2026, antes de correr nada sobre el test ni la simulación. Se sella con `PLAN_V115.sha256`; el código verifica el sha al arrancar.

## Naturaleza
Análisis de **robustez**, no confirmatorio. El test (4–20 sep) y la simulación (21 sep–26 oct) ya se abrieron con la regla de cruce estricto (v110, v111); aquí solo cambia la regla de ejecución.

## Qué queda congelado
- Modelos finales v108 (`16_curva_e3_corregida/modelos/modelos_finales_v108.pkl`, sha del manifiesto), sin reentrenar.
- Políticas de v110 sin cambios: miope (11 modelos + δ fijo 0,5 / 2 / 5), HJB exacta (curva interpolada), GLFT y HJB aproximada; γ = 0,01, Q = 10, 0,01 BTC por orden, cotización recalculada cada segundo con el estado al inicio del segundo, |q| ≤ 10, inventario valorado al último mid del día.
- Mismas cotizaciones (precio en ticks) que v110/v111: se reutilizan `econ_v110.dia` y sus funciones sin editarlas; solo se sustituye la función de ejecución.

## Lo que permiten los datos (comprobado en días de entrenamiento: 15 jul, 20 ago, 2 sep)
- La capa canónica trae 20 niveles por lado cada 100 ms. El nivel 20 está a ~0,4–0,5 bps del mid (p90 ≈ 0,6–0,8 bps).
- Las políticas cotizan a 0,85–2 bps (mediana): la cantidad delante de la orden en su precio **casi nunca es visible**. No se puede reconstruir la posición real en cola; solo acotarla.
- Las transacciones traen precio, cantidad y lado del agresor (μs), lo que permite contar el volumen negociado exactamente al precio de la orden.

## Reglas de ejecución comparadas (por segundo y lado; como mucho una ejecución de 0,01 BTC por lado y segundo, igual que v110)
- **R0, cruce estricto (actual):** se ejecuta si un agresor negocia a un precio estrictamente más allá del de la orden. Control de reproducción.
- **R1, toque sin cola (cota optimista):** se ejecuta si un agresor negocia al precio de la orden o más allá (cola delante = 0).
- **R2, cola FIFO aproximada (intermedia):** se ejecuta si un agresor negocia estrictamente más allá, o si el volumen agresor acumulado **exactamente al precio de la orden** dentro del segundo alcanza Q_delante + 0,01 BTC. Q_delante:
  - si el precio está dentro de los 20 niveles visibles en el inicio del segundo: la cantidad mostrada en ese precio (0 si el precio no tiene órdenes);
  - si está más allá del nivel 20: **imputada** como la mediana de las 20 cantidades visibles de ese lado en ese instante.
  - Supuestos explícitos: la cola solo avanza con transacciones (las cancelaciones de quien está delante no se cuentan, como `RiskAverseQueueModel`); la prioridad se pierde cada segundo al recotizar; sin latencia de envío; las cantidades mostradas son las del libro reconstruido cada 100 ms.
- Momento de la ejecución: la primera transacción que cumple la condición (para el markout).

R0 ≤ R2 ≤ R1 en número de ejecuciones por segundo dado el inventario; la cola real cae entre R0 y R1 si las transacciones más allá del precio llenan la orden.

## Orden de ejecución
1. Test 4–20 sep. Control: R0 reproduce `18_/salida/por_dia_v110.json` (ejecuciones y PnL por día, todas las combinaciones, dif. < 1e-9). Si falla, se detiene.
2. Simulación 21 sep–26 oct, con el mismo código sin cambios. Control: R0 reproduce `19_/salida/por_dia_econ_v111.json`. Si falla, se detiene.

## Qué se reporta (por periodo, regla, política y modelo)
Ejecuciones/día; |q| medio; PnL/día (USDT); días > 0; PnL por ejecución (bps) con IC95 bootstrap por días (2 000 réplicas, semilla 20261030); markout a 10 y 60 s (selección adversa); E3 tesis − modelo (bps/ejec.) con IC95; cambio respecto de R0.

## Lectura fijada de antemano
- **La conclusión económica se mantiene bajo una regla** si, para todas las combinaciones modelo × {miope, HJB exacta, GLFT}, el extremo superior del IC95 del PnL por ejecución es < 0.
- **E3 gana bajo una regla** si, con la HJB exacta, el IC95 de E3 tesis − modelo es > 0 frente a todos los modelos AS y Hawkes.
- Si R1 y R2 difieren de R0 en menos de 0,2 bps por ejecución en todas las combinaciones de HJB exacta, se dirá que el resultado es poco sensible a la cola dentro de este rango de supuestos.
- Ningún resultado cambia los modelos, las políticas ni las tablas principales de la tesis; se reporta como análisis de robustez.
