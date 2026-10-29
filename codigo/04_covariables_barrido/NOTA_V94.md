# NOTA v94: covariables de barrido en g(X) para corregir el rebote subestimado

Plan `PLAN_V94.md` (sha256 verificado; aprobado por Santiago el 29 oct). Paso 0 en `PASO0_V94.md` (causa: faltan covariables). Ajuste 29 jun–12 jul; evaluación 45 días (17 jul–3 sep sin 22–25 ago). E3-fkX (44 covariables) frente a E3-fkX+B (44 + 5 de barrido: recorrido firmado, volumen y tiempo del último barrido; spread máximo 1 s; cambio del mid 1 s). Test de no fuga superado (2 días, capas v1 y v2).

## Veredicto: cumple los 3 criterios
| criterio | E3-fkX | E3-fkX+B |
|---|---|---|
| Brecha del rebote tras ventas (O/E contrario − base, ask) | 0,332 (1,205 vs 0,872) | **0,248** (1,101 vs 0,853) |
| Brecha del rebote tras compras (bid) | 0,060 (0,831 vs 0,771) | **0,011** (0,819 vs 0,808) |
| Δll total por bin [IC95 días] | — | ask +0,011 [+0,003; +0,023] (31/45); bid +0,020 [+0,007; +0,036] (39/45) |
| Δll solo δ = 2 | — | ask +0,002 [+0,001; +0,004]; bid +0,004 [+0,002; +0,006] |
| AUC de cruce δ = 2 | ask 0,8209 / bid 0,8174 | ask 0,8205 / bid 0,8192 |
| AUC de dirección a 10 s tras barridos (informativo) | 0,700 | 0,701 |

## Lectura
- El rebote tras compras queda prácticamente corregido (brecha 0,06 → 0,01). Tras ventas baja un 25 % (0,33 → 0,25), pero **no desaparece**: tras una caída rápida siguen llegando más compradores de los que E3 espera.
- La mejora fuera de muestra es real pero pequeña (+1–2 % de ll). En el ajuste fue mucho mayor (ask −1 130 242 → −1 018 207, ≈ +10 %): parte de lo aprendido no se traslada a la evaluación (más volátil, rally de agosto).
- La discriminación y la dirección no cambian: las nuevas covariables mejoran el **nivel** tras barridos, no el ordenamiento.

## Cautelas
Evaluación no ciega; los barridos de evaluación son los de v92 (θ = 0,5 bps); el resto del rebote tras ventas puede ser de régimen (paso 0: en el ajuste el efecto era simétrico).

## Archivos
`codigo/feats_v94.py` (covariables y test de no fuga), `codigo/corrida_v94.py`, `codigo/analisis_v94.py`; `salida/por_dia_v94.json`, `salida/eventos_v94.npy`, `salida/tablas_v94.md`, `salida/analisis_v94.json`.

## v94b: importancia por permutación (E3-fkX+B, 49 covariables; 10 días de evaluación; `salida/permutacion_v94.md`)
- **Por grupo (pérdida de ll por bin, ask / bid):** flujo +0,61 / +0,62; libro +0,23 / +0,30; volatilidad +0,08 / +0,05; **barrido (nuevas) +0,07 / +0,05**; OFI +0,005 / +0,005.
- **Las más importantes:** número de agresores del mismo lado en el último segundo (+0,12 y +0,11, de lejos la primera); **dmid_1s (nueva) segunda en ambos lados**; volatilidad realizada a 1 s y 60 s; pendiente del libro.
- **≈ 0 (no aportan):** 9 (ask) y 10 (bid) de 49; entre ellas las 4 de OFI y mid_change_bps_100ms (sustituida por dmid_1s).
- **Negativas (desordenarlas mejora la ll):** sobre todo flujo de ventanas largas (30–60 s) y volumen firmado; en bid, past_n_sell_sum_30000ms −0,022, past_n_sell_sum_60000ms −0,013, realized_vol_10000ms −0,010. Indican relaciones aprendidas en 14 días tranquilos que no se trasladan a agosto (sobreajuste o cambio de régimen).
- **Tiempos de ajuste (M5):** E3-f con 44 covariables 28–31 s por lado, con 49 34–42 s; E3-fkX completo 86–101 s por lado.
- Cautelas: con covariables correlacionadas, la permutación subestima la importancia de cada una (otras la sustituyen); una sola permutación por día; 10 días.

## v95: E3 reducido a 24 covariables (plan `PLAN_V95.md`; 35 días no usados en la selección) — NO pasa
- ll (reducido − 49): ask −0,003 [−0,013; +0,007] (empate); **bid −0,028 [−0,047; −0,012], peor** (gana 11/35 días).
- AUC δ = 2: ask 0,8247 → 0,8235; bid 0,8221 → 0,8201 (dentro del margen).
- Rebote: brecha tras venta 0,264 → 0,288 (sube más de 0,02: falla); tras compra 0,030 → 0,042.
- Tiempo de ajuste: 85–97 s → 68–72 s por lado (≈ −20 %).
- **Lectura:** quitar 25 covariables a la vez empeora el bid. La permutación subestima las covariables correlacionadas (libro: desbalances, profundidades): una por una parecen inútiles, pero el grupo sí aporta. **Se mantiene E3-fkX+B con 49 covariables.**

## v97: + tendencia de 15 min y 1 h (51 covariables; plan `PLAN_V97.md`; no fuga verificada) — NO pasa
- ll (51 − 49): ask +0,002 [−0,010; +0,012] (31/45); bid **+0,015 [+0,008; +0,023]** (39/45). Falla C2 por el ask.
- AUC δ = 2: ask 0,8205 → **0,8231**; bid 0,8192 → **0,8223** (sube en ambos).
- Brecha del rebote tras ventas: 0,248 → 0,260 (no baja: falla C1). Con tendencia de 1 h al alza: 0,370 → 0,350; a la baja 0,072 → 0,122.
- **Lectura:** la tendencia larga mejora el modelo en general (AUC en ambos lados, ll en bid), pero **no corrige el rebote**. El GBM no aprende la interacción "barrido vendedor × mercado alcista" con 14 días tranquilos de ajuste (hipótesis 3 de v96: pocos ejemplos). Por los criterios fijados se mantiene E3-fkX+B (49).
- Cargador: v90–v97 usaron el cargador de v58 (capas de `Comparativa 1/`), que excluye 22–25 ago por la partición antigua. La carpeta unificada `00_DATOS…` sí tiene esos días; pendiente repetir con 49 días.
