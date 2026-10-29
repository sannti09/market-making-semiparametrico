# v112: descomposición de la pérdida por ejecución (selección adversa) con los modelos finales (29 oct; aprobado por Santiago: "dale … pon a correr ahora los modelos nuevos")

**Tipo:** análisis descriptivo de las ejecuciones que ya produce el simulador de v110/v111. No hay criterio ni decisión asociada; no se reajusta nada.

**Datos y modelos:**
- test 4–20 sep y simulación 21 sep–26 oct, reportados por separado;
- modelos v108 y políticas de v110 (miope, HJB con curva interpolada, GLFT) para E3 tesis, Hawkes 2 escalas + S, GLM lineal, AS + h + f y AS base.

**Descomposición de cada ejecución** (s = +1 venta, −1 compra; p = precio; m_0 = mid al inicio del segundo de la decisión; m_H = mid H segundos después de la ejecución):
- distancia capturada = s·(p − m_0)/p·10⁴;
- movimiento posterior a H = s·(m_0 − m_H)/p·10⁴, para H = 1, 10 y 60 s;
- markout_H = capturada + movimiento_H (definición de la tesis).

**Reporte:**
- por período, política y modelo: ejecuciones, media de la capturada, del movimiento a 1/10/60 s y del markout a 10 s;
- fracción de ejecuciones con markout a 10 s > 0;
- IC95 por días para movimiento y markout a 10 s;
- deciles de la intensidad predicha por E3 tesis a δ = 2 bps en el segundo de la ejecución, con el markout medio a 10 s por decil (E3 tesis con HJB).

**Control:** para cada día y combinación, el número de ejecuciones y el PnL que salen de la lista de ejecuciones deben coincidir con los del simulador de v110 (diferencia < 1e-9); si no, se detiene.
