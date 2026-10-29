# v37: correcciones tras la revisión de Astra sobre v36 (2026-10-26)

v36 queda intacta. No se recalculó mercado ni se abrieron bloques nuevos: las cifras de `36_…/salida/` siguen siendo las de v36.

## Cambios
1. **Horizonte de markout fuera de cobertura.**
   - Nuevo `indice_en_rejilla` en `01_pipeline/datos_capa_100ms.py`: devuelve −1 si τ+H no cae en [ts[k], ts[k]+100 ms), lo que cubre el fin de archivo y los huecos. La antigüedad del mid usado queda acotada a menos de 100 ms.
   - Aplicado en `markouts_ajuste.py:58`, `filtro_markout.py:57` y `filtro_100ms.py:96`, con la condición `k >= 0` y `state_valid` en k.
   - En v36 el sesgo afectaba solo a ejecuciones con τ > fin de día − H, es decir, a lo sumo H/86 400 de la muestra (≤ 0,07 % con H = 60 s), que se valoraban con el mid de 23:59:59.9. Cota analítica, no medida.
2. **NB.** `01_pipeline/modelo_e3_semiparametrico.py` (docstring, `etiqueta_familia`, `evaluar()["familia"]`) y `corrida_ajuste_calibracion.py:2,56` la etiquetan como **"NB con media Poisson fija"**. No se implementó otro estimador.
3. **AUC.** `01_pipeline/metricas.py` usa rango medio en los empates; `corrida_ajuste_calibracion.py:18` lo importa. El AUC = 0,84 de v36 no se recalculó. El de E1 (score constante) era inválido en v36 y sería 0,5.
4. **Interpretación.** `RESUMEN_V37_INTERPRETACION_CORREGIDA.md`:
   - se retiraron "ningún filtro con X_t lo corrige" y "la cola empeora el resultado";
   - las conclusiones se limitan al modelo, la muestra y la política examinados;
   - cruce hipotético ≠ fill.

## Causalidad (ver sección «Re-ejecución» para la sonda empírica)
- **Flujo `past_*`.** Según `CODE_REVIEW.md:62` ("excluyen el bin actual") y `code/check_feature_boundaries.py:42-47`:
  - `past_*_1000ms(t)` = Σ `target_*_next_100ms` de las 10 filas previas, es decir, trades en [t−1 s, t), en tiempo de trade del exchange (Binance Vision);
  - por tanto no comparten eventos con el target [t, t+Δ), salvo que la frontera µs/ms difiera entre `trades_100ms` y `trades_event`;
  - el código constructor no está disponible localmente.
- **LOB, OFI, volatilidad, `book_age_ms`.**
  - No hay documentación local de si la rejilla `ts_ms` usa el tiempo de evento del exchange (E) o el de recepción. La captura "conserva tiempos de recepción" (`CODE_REVIEW.md:21`), y la latencia del feed llega a ~241 ms (`hftbacktest_pilot_v1/README.md:65`).
  - Si la rejilla fuera de recepción, X(t) sería causal, pero frente a trades en tiempo del exchange habría un desfase de hasta ~0,24 s.
  - Si fuera de exchange, falta acreditar la frontera en t.
  - Requiere el código de reconstrucción (en `/opt/lob_system`, sin SSH).

## Pruebas
- `test_correcciones_v37.py`: 6 pruebas, todas OK.
  - cobertura al final y en huecos (reproduce el fallo de v36);
  - mini markout sintético;
  - AUC constante = 0,5, empates parciales y equivalencia con el conteo de pares;
  - etiqueta NB.
- `test_e3_semiparametrico_heredado_v36.py`: 7 de 7 OK. Los scripts de corrida compilan, pero no se ejecutaron.

## Re-ejecución autorizada (2026-10-26/27; solo ajuste y calibración interna)
**Metadatos del Parquet:**
- `lob_semantics = "state at ts_ms before events exactly at boundary"`;
- `target_semantics = "target_* covers [ts_ms, ts_ms+100ms); past_* excludes current bin"`.

**Sonda del reloj LOB** (`sonda_reloj_lob.py`, tres días de ajuste; salida en `salida/SONDA_RELOJ_LOB.json`):
- **Sin fuga.** La fracción de barridos que el libro de la fila de T+s ya refleja se mantiene en ≈1 % para s ≤ 80 ms. Es el mismo nivel que con s < 0, y en s = 0 vale ≈1 %.
- **Retraso.** El impacto aparece desde s ≈ 90 ms y se completa hacia s ≈ 200 ms. El libro va unos 90 ms por detrás del reloj de trades; la rampa de unos 100 ms corresponde a la rejilla.
- **Consecuencia.** X(t) es causal, pero tiene entre 90 y 190 ms de antigüedad, de modo que "latencia cero" en el filtro a 100 ms significa información con algo de retraso.
- **Pendiente documental.** Los datos no permiten distinguir entre el tiempo del exchange (con un desfase en la agregación de `depth@100ms`) y el tiempo de recepción con una latencia de unos 90 ms.

**Resultados frente a v36:**
- **Markouts:** la diferencia máxima es de 0,011 bps.
- **Filtro a 1 s:** se pierden menos de 5 ejecuciones en calibración, pero las colas del GBM se mueven. En bid, el top 5 % pasa de +0,04 a +0,30 bps (−1,00 / +1,85 / −1,52 / −0,66); en ask, el top 5 % pasa de −1,90 a −2,20 bps. Las colas son inestables.
- **Filtro a 100 ms:**
  - en bid, el top 5 % de E3 da +1,04 bps (−1,90 / +4,85 / −2,64 / −0,80), es decir, un solo día positivo (14 de julio);
  - en ask, el top 10 % de E3 da −1,92 bps;
  - E2 es el filtro más estable entre días, pero negativo (≈ −1,1 a −1,2).
- **AUC con empates:**
  - E1: 0,500 / 0,500 (v36 daba 0,354 / 0,375, un valor inválido);
  - E1 + h: 0,695 / 0,676;
  - E3-GBM: 0,837 / 0,840;
  - E3-RF: 0,840 / 0,844.
- **Log-verosimilitudes:** idénticas a v36, salvo el RF, que difiere en menos de 25 unidades de log-verosimilitud.

## Pendiente
- Acreditar con el código de reconstrucción qué reloj usa la rejilla LOB.
- Declarar en el backtest una latencia de al menos 90 ms en las covariables LOB.
