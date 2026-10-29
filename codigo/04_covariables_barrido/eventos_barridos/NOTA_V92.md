# NOTA V92 — taker que sigue el barrido tras spread ancho (29 jun – 3 sep 2026, 67 días)

**Veredicto: NEGATIVO.** Ninguna de las 72 celdas cumple el criterio (cumple 0). No se ejecutó el filtro OOF (solo se hace si es prometedor). Plan congelado: `PLAN_EXPLORATORIO_V92.md` (sha256 en `.sha256`; sin enmiendas). Nota: la frase del criterio sobre "sin top-3" quedó redactada de forma enrevesada en el plan; se aplicó la lectura estricta (media sin top-3 > 3,4 bps). Con cualquier lectura el resultado es el mismo, porque ninguna celda llega a IC inferior > 3,4 (el máximo IC inferior de las 72 es 0,52 bps y la máxima media 2,93).

Celdas: 3 θ × 2 disparadores (S = spread/barrido v91, T = trades) × 3 L × 4 H = 72 (selección múltiple: la mejor de 72 queda sobrevalorada).
Eventos: S: 1 566 / 749 / 244 (θ = 0,5 / 1 / 2) antes de quitar solapes; T: 255 567 / 51 937 / 9 016 eventos. T sí es factible con los datos de trades.

## Mejores celdas (bruto en bps, taker ida y vuelta, IC95 por días)
| celda | n | op/día | media [IC95] | mediana | % pos | neto a 1,7/lado |
|---|---|---|---|---|---|---|
| S θ2 L1 H30 | 162 | 2,4 | 2,93 [0,35; 5,52] | 0,04 | 50 | −0,47 |
| S θ2 L1 H60 | 157 | 2,3 | 2,89 [−0,07; 5,60] | −0,17 | 50 | −0,51 |
| S θ2 L2 H60 | 156 | 2,3 | 2,50 [−0,04; 4,87] | −0,22 | 47 | −0,90 |
| S θ1 L1 H10 | 562 | 8,4 | 1,48 [0,31; 2,88] | 0,00 | 50 | −1,92 |
| S θ0,5 L1 H10 | 1 236 | 18,5 | 0,94 [0,49; 1,40] | 0,00 | 50 | −2,46 |
| T θ0,5 L1 H30 | 70 816 | 1 057 | 0,57 [0,52; 0,61] | 0,33 | 55 | −2,83 |
| T θ1 L1 H10 | 30 960 | 462 | 0,25 [0,20; 0,31] | 0,00 | 47 | −3,15 |
Comisión de equilibrio por lado = media/2: 1,5 bps (la mejor), ≤ 0,5 en T. Con 7,5 bps por lado todo es muy negativo (≤ −12).
Con latencia creciente (L = 2, 3) la media baja; L = 1 es la mejor, y ya es optimista frente a los 130 ms reales.

## Robustez
- **Alza/baja:** S θ2 L1 H30: alza +5,51, baja −0,64 (falla). La asimetría se repite en casi todas las celdas S (baja ≈ 0 o negativa). T θ0,5: alza ≈ baja ≈ +0,5.
- **Jul/ago:** S θ2 L1 H30: julio +5,60, agosto +0,90; en las celdas S el efecto se concentra en julio. Sin top-3 días: 3,28 (< 3,4). La semana 18–24 ago se retiró y se guarda en el JSON (`sin_sem18_24ago`).
- **Placebos:** dirección aleatoria ≈ 0 (−0,2 a +0,1; es el coste de dos medios spreads); dirección invertida −3,6 (la misma celda): el signo del barrido importa. Tendencia de 60 s previos en los mismos instantes: media 1,27; diferencia contra seguir el barrido [−0,82; +4,37] (no significativa). En T θ0,5 la diferencia es positiva y significativa (+0,4 bps) pero la media es 0,5 bps.
- Las colas son gruesas: mediana ≈ 0 y 50 % de positivos en S; la media la mueven pocos eventos.

## Cautelas
Latencia real 130 ms + lotes de 100 ms (L = 1 = 100 ms es optimista; el spread ancho dura mediana 100 ms y puede ser artefacto de la reconstrucción del libro, sin verificar con diferencias); impacto propio ignorado (tamaño 1 unidad; los precios al touch tras un barrido son de libro fino); cola gruesa; eventos autocorrelados y concentrados en pocos días/horas (rally de agosto); selección entre 72 celdas; el detector S exige tipo barrido de v91 y lado ask/bid con umbral 75 %.

## Rutas
- Código: `codigo/eventos_v92.py` (eventos y ejecución), `codigo/analiza_v92.py` (métricas y robustez).
- Salidas: `salida/eventos_v92.pkl`, `salida/resultados_v92.json` (72 celdas con robustez completa), `salida/resumen_v92.txt`.
