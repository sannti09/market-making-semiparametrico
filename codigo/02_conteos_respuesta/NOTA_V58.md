# NOTA v58: test ciego 1 de P1 (26 ago – 15 sep 2026, capa extendida v2)

Corrida única, 2026-10-27. Pre-registro vinculante: `02_configuracion/PROTOCOLO_CIEGO1_V58.md` y `PARTICION_V58.json`, sin tocar.

## 1. Hashes y compuerta
- PARTICION_V58.json 5aefa80a… y PROTOCOLO_CIEGO1_V58.md 822d93d8… coinciden con `SHA256_PREREGISTRO.txt` (verificado en el código antes de ajustar).
- Orden respetado: (a) ajuste de todos los modelos con 29 jun – 17 ago (50 días, 4.319.971 bins); modelos en `salida/modelos_ajustados_v58.pkl`, sha256 d901cd27… (`SHA256_MODELOS.txt`); (b) calibración interna 18–21 ago (4 días, capa v1); (c) solo después se abre el ciego.
- Compuerta: `CALIBRACION_V58.json` (referencia de O4 y c_δ de E3-cal), sha256 298d17d1… en `SHA256_COMPUERTA.txt`. El guardia del cargador exige ese archivo y ese hash para leer cualquier fecha de la capa v2 (en código, no por convención).
- Guardia único (`cargador_v58.py`): v1 para 29 jun – 21 ago, v2 para 26 ago – 15 sep, `PermissionError` en 22–25 ago y desde el 16 sep. Fechas leídas (registro del guardia): de 2026-06-29 a 2026-09-15; no se leyó ningún 22–25 ago ni ≥ 16 sep. No se leyó `control/` de la capa v2.

## 2. Prueba de reproducción de v52 (smoke test, regla 6)
Con la ventana original de v52 (ajuste 29 jun – 12 jul, calibración 13–16 jul, y el día 17 jul) el código v58 reproduce, para ambos lados y los siete modelos (E1, E1+h, E3, E3-lag, E3-kX, E2, GLM), la ll_pp de calibración y del 17 jul de `CALIBRACION_Y_AJUSTE_V52.json`, `RESULTADOS_POR_DIA_V52.json` y `RESULTADOS_GLM_V53.json` con diferencia relativa máxima 2,2e-16. Alfa NB y k idénticos (k ask 0,619892; bid 0,746902). Ejemplo: ll_pp E3 ask calibración 13–16 jul = −418.254,68 (igual que v52). Detalle en `salida/SMOKE_REPRODUCCION_V58.json` y `smoke_v58.log`. La adaptación no cambió la maquinaria. (El smoke se ejecutó con el venv del scratchpad, sklearn 1.9.1; no se pudo comparar con el entorno original de v52, pero reproduce al redondeo.)

## 3. Datos
- 21 días presentes (26 ago – 15 sep), ninguno faltante ni sustituido. Bins válidos: 1.814.315 por lado (de 1.814.400 nominales). Pérdidas: 08-26 (1), 08-28 (12), 09-02 (39), 09-04 (13), 09-09 (1), 09-10 (19), todas por `state_valid`/OFI nulo. Calibración 18–21 ago: 345.554 bins (08-21 pierde 46).
- Umbral de O1–O3: 18 de 21 (≥ 85,7 %), sin ajuste proporcional necesario.

## 4. Veredicto principal (E3 frente a E1 y E1+h), por lado
| | ask | bid |
|---|---|---|
| O1 días E3>E1 / mejora media por bin [IC95 bootstrap días, B=2000] | 21/21; 1,304 [0,958; 1,691]; cumple | 21/21; 1,286 [0,868; 1,785]; cumple |
| O2 días E3>E1+h | 21/21; cumple | 21/21; cumple |
| O3 AUC media (δ=2 bps, 1 s) / días E3>E1+h | **0,8099** / 21/21; cumple | **0,7982** / 21/21; **NO cumple** (0,798 < 0,80) |
| O4 cociente ciego/calibración 18–21 ago | **0,234** (1,304 vs 5,572); **NO cumple** | **0,246** (1,286 vs 5,216); **NO cumple** |
| P1 | **NO se cumple** | **NO se cumple** |

Lectura: E3 gana a E1 y a E1+h todos los días en ambos lados (p de signo 4,8e-7, descriptivo), pero P1 falla por O4 en ambos lados y, en bid, también por O3 (AUC media 0,798). AUC diaria de E3: ask mín 0,672, máx 0,905, 8 días < 0,80; bid mín 0,602, máx 0,892, 9 días < 0,80. AUC medias: E1+h 0,630/0,625, E2 0,649/0,634.

Sobre O4 (informativo, el criterio pre-registrado manda): la referencia 18–21 ago es muy distinta de la de v52 (13–16 jul): mejora por bin de E3 sobre E1 de 5,57 (ask) y 5,22 (bid) frente a 1,40 y 0,97. Esos cuatro días fueron de actividad extrema (ll de E1 −2,07 M ask / −1,93 M bid, c_δ en δ ≥ 15 bps de 377 a 12.050), con lo que E1 queda mucho peor que en un día normal y la mejora relativa de E3 se infla. La mejora del ciego (1,30/1,29) es similar a la de v52 (1,35/1,20 en 36 días). Con la referencia de v52 el cociente sería ≈ 0,93/1,33, pero eso NO es el criterio de v58 y no cambia el veredicto.

## 5. Latencia (E3-lag200), secundaria
E3-lag peor que E3 en 21/21 días en ambos lados.
| lado | mejora retenida sobre E1 | Δ AUC (lag − E3) | AUC E3-lag | Δ ll_pp |
|---|---|---|---|---|
| ask | 83,2 % | −0,030 | 0,780 | −398.008 |
| bid | 84,6 % | −0,029 | 0,770 | −359.157 |
| ambos | 83,9 % | | | |
Lectura pre-registrada de v52 (≥ 80 %): cautela de latencia cerrada en ambos lados.

## 6. O5 de E3 y E3-cal (secundario)
Cociente observado/predicho a δ = 2 bps (agregando los 21 días), global y rango de deciles de λ̂:
| | global | deciles (mín–máx) | O5 |
|---|---|---|---|
| E3 ask | 1,034 | 0,751 – 2,378 | NO (global sí, deciles no) |
| E3 bid | 0,774 | 0,550 – 2,933 | NO |
| E3-cal ask | 0,694 | 0,504 – 1,596 | NO |
| E3-cal bid | 0,777 | 0,551 – 2,943 | NO |
Sumando todos los δ: E3 ask 1,42, bid 1,00; E3-cal ask 0,85, bid 0,95 (deciles fuera de rango en los cuatro casos).
- Con los factores c_δ de 18–21 ago, E3-cal no recupera la calibración. En ask empeora el nivel a δ = 2 (c_2 = 1,49 estimado en ese bloque, mientras que en el ciego E3 ya tenía obs/pred 1,03); en bid c_δ ≈ 1 a δ ≤ 2 y casi no cambia nada. El defecto principal es la forma por decil: los deciles bajos de λ̂ están infrapredichos (2,4–2,9) y los altos sobrepredichos (0,5–0,8), es decir, el nivel no es el problema sino la pendiente de λ̂ frente a lo observado.
- ll_pp de E3-cal frente a E3 en el ciego: ask +53.299 (+0,029 por bin; mejor en 11/21 días); bid +25.469 (+0,014 por bin; mejor en 8/21 días). Mejora global pequeña, concentrada en δ grandes, donde c_δ es enorme (6.132 y 12.051 a 20 bps). AUC de E3-cal = AUC de E3 por construcción.

## 7. Otros secundarios
- **O6 (E3 > E2 > E1):** se cumple en ll_pp en ambos lados, E3>E2 y E2>E1 en 21/21 días. E1+h supera a E2 en ll_pp (ask −4,131 M vs −4,382 M), igual que en v52.
- **O7:** NB mejor que Poisson (ask −1,315 M vs −6,781 M; bid −1,356 M vs −6,857 M). Cautela: el alfa NB del ajuste cayó en la cota superior de la búsqueda (100) en ambos lados (en v52 era 87 y 75), así que su valor numérico es una cota, no un óptimo interior.
- **O9:** AUC por δ en `VEREDICTO_V58.json` (clave `O9_auc`). Δ=1 s, E3, δ=0,5/1/2/3/5 bps: ask 0,829/0,819/0,810/0,799/0,833; bid 0,826/0,813/0,798/0,784/0,799. Δ=100 ms (E3): ask 0,906/0,906/0,901/0,902/0,964; bid 0,905/0,902/0,893/0,920/0,954 (NaN en δ de cola, sin cruces suficientes).
- **O10:** k reestimado en el ciego: ask 0,838 vs 0,700 (+19,8 %, dentro de ±20 % por muy poco); bid 0,713 vs 0,747 (−4,6 %, dentro).
- **E3-kX:** supera a E3 en ll_pp (+95.641 ask, 19/21 días; +128.265 bid, 16/21), AUC prácticamente igual (+0,001 / +0,003).
- **O8 (RF) no se corrió; P2 no se evalúa.**

## 8. GLM (v53), primera evaluación limpia
| | ask | bid |
|---|---|---|
| Mejora de E3 sobre E1 recuperada por el GLM | 91,9 % | 90,3 % |
| Días E3 > GLM | 19/21 | 18/21 |
| Mejora por bin E3−GLM [IC95 bootstrap días] | 0,105 [0,074; 0,142] | 0,125 [0,086; 0,162] |
| AUC GLM / AUC E3 / días E3>GLM en AUC | 0,792 / 0,810 / 21 | 0,782 / 0,798 / 21 |
| AUC GLM ≥ 0,80 | no | no |
| O1–O4 del GLM frente a E1/E1+h | O1 sí, O2 sí, O3 no, O4 no (cociente 0,23 / 0,25) | igual |
| Lectura con la regla de v53 | "necesario" (E3 gana ≥ 18 días e IC excluye 0), aunque el GLM retiene > 90 % | "necesario" (18/21 = umbral exacto) |
Lectura por lado, sin regla de combinación: el GLM recupera ~90–92 % de la mejora en ll pero no llega a 0,80 de AUC; E3 es sistemáticamente mejor (AUC en 21/21 días), con ventaja pequeña en términos absolutos (ΔAUC ≈ 0,017). La regla de v53 daría "necesario" porque se evalúa la condición "necesario" antes que "prescindible"; las dos condiciones se cumplen a la vez, lo que apunta a un resultado intermedio práctico.

## 9. Desviaciones y decisiones de aplicación (ninguna cambia especificaciones, umbrales ni métricas)
1. **E2/Hawkes:** se usan los parámetros μ, α, β de la especificación congelada v46 (EM sobre los 4 días fijos 30 jun, 3 jul, 7 jul, 10 jul, todos dentro de la ventana de ajuste de 50 días), sin repetir el EM; a y k de E2 sí se recalcularon con los 50 días (ask a=−1,722, k=0,6996; bid a=−1,614, k=0,7472). Aplicación de la regla "4 días fijados a priori", no del número de días de ajuste.
2. **n_backfit = 3, hiperparámetros y covariables:** los congelados. Solo cambia la ventana de ajuste.
3. **Bootstrap B = 2000** (protocolo v58), frente a 10.000 de la función por defecto y de v52. El IC es del mismo tipo (percentil, remuestreo de días con semilla 0).
4. **Referencia de O4:** recalculada con la propia calibración 18–21 ago (no la de la especificación v45), como pide el protocolo. Referencia del GLM: ídem con la ll del GLM en esos días.
5. **Capa v2:** primera fila de 26 ago sin excepción de OFI nulo (la excepción de la fila 0 sigue solo para 29 jun de la capa v1); `fin_capa` de v37 (24 ago 12:00) se aplica solo a la capa v1. 12–21 ago de la capa v1 usan los dos archivos `_00-12` y `_12-00`, igual que v52.
6. **Entorno:** venv del scratchpad (sklearn 1.9.1). `analisis_v58.py` emite un aviso de nanmean (δ de cola sin cruces) que no afecta a veredictos.

## 10. Cautelas
- La capa extendida v2 se construyó en Colab con el mismo código que la v1 (copia local verificada 84/84 sha256); el esquema se comprobó antes, pero la equivalencia exacta del pipeline no se auditó con modelos.
- El 16 sep queda excluido (ciego 2). La reserva 22–25 ago no se leyó.
- Exposición previa declarada en la partición: v35 usó 20 jul; calendario Spot del 9 oct cubrió 25 jun – 5 sep; el anteproyecto §7.4 aplicó el piloto a bloques posteriores; la capa extendida se auditó (solo integridad, sin modelos ni PnL) el 27 oct. El ciego 1 no es estrictamente virgen en el sentido económico.
- Los 21 días no son independientes; p de signo y bootstrap por días son descriptivos.
- La rejilla está en tiempo de evento del exchange (~125 ms antes de la recepción); E3-lag200 mide sensibilidad, no latencia real.
- ll_pp es una verosimilitud compuesta (filas δ anidadas); la mejora frente a E1 incluye la forma en δ. E3 ordena bien pero sus niveles por decil no están calibrados (O5 falla otra vez).
- Esto es P1 (predicción de intensidad), no rentabilidad (P2 cerrada como negativa).

## 11. Archivos
`salida/`: VEREDICTO_V58.json, RESULTADOS_POR_DIA_V58.json, TABLA_POR_DIA_V58.csv, CALIBRACION_V58.json, SHA256_COMPUERTA.txt, SHA256_MODELOS.txt, modelos_ajustados_v58.pkl, SMOKE_REPRODUCCION_V58.json, smoke_v58.log, corrida_v58.log (+ `.out`), SHA256_SALIDAS_V58.txt, `cache/` (bins por día, 5,4 GB, borrable). Código en `01_codigo/`: cargador_v58.py (guardia), nucleo_v58.py, glm_v58.py, lib_v58.py, corrida_v58.py, analisis_v58.py, smoke_v58.py. Runtime: smoke 308 s; corrida principal 1.513 s (ajuste 1.405 s, calibración 19 s, ciego 89 s).
