# AUC para P1: E1 vs E3 (v37, 2026-10-27)

Material de apoyo para P1 (capacidad predictiva de la intensidad). Las cifras salen de `salida/RESULTADO_AJUSTE_CALIBRACION_E3.json` (v37), con los modelos ajustados en **ajuste** (29 jun–12 jul) y evaluados en **calibración interna** (13–16 jul). **No es validación externa ni test.**

## Definición
- **Evento binario por bin de 1 s:** hay al menos un evento agresor que cruza mid·(1 ± 2 bps) en [t, t+1 s). Lado ask: compradores; lado bid: vendedores.
- **Score:** la intensidad predicha λ(t, δ=2 | X) de cada modelo. El AUC solo depende del orden de los scores, así que basta con η = g(X) + h(hora).
- **AUC (Mann–Whitney) con rango medio en los empates.** Un predictor constante da exactamente 0,5. Código en `01_pipeline/metricas.py`; pruebas 04 y 05 en `test_correcciones_v37.py`.
- **Corrección v37:** v36 no promediaba los empates y daba para E1 valores inválidos (0,354 / 0,375). Los valores de E3 no cambian.

## Resultados (calibración interna, por día: 13 / 14 / 15 / 16 jul)

| Modelo | AUC ask (media) | por día | AUC bid (media) | por día |
|---|---|---|---|---|
| E1: A·e^{−kδ} | 0,500 | 0,500 en los 4 días | 0,500 | 0,500 en los 4 días |
| E1 + h(hora) | 0,695 | 0,645 / 0,740 / 0,719 / 0,677 | 0,676 | 0,632 / 0,753 / 0,684 / 0,635 |
| **E3-GBM Poisson** | **0,837** | 0,827 / 0,873 / 0,832 / 0,817 | **0,840** | 0,832 / 0,875 / 0,825 / 0,829 |
| E3-RF Poisson | 0,840 | 0,827 / 0,878 / 0,838 / 0,819 | 0,844 | 0,832 / 0,878 / 0,834 / 0,833 |

**Ablaciones de E3-GBM (AUC medio ask / bid; entre paréntesis, la caída frente al modelo completo):**

| Sin… | ask | bid |
|---|---|---|
| flujo | 0,812 (−0,025) | 0,818 (−0,022) |
| volatilidad | 0,833 (−0,004) | 0,832 (−0,008) |
| libro | 0,827 (−0,010) | 0,832 (−0,008) |
| OFI | 0,836 (≈0) | 0,839 (≈0) |
| h(hora) | 0,835 (−0,002) | 0,841 (+0,001) |

## Lectura útil para P1
1. **E1 no discrimina:** con A y k constantes, el AUC es 0,5 por construcción. E1 + h solo capta la estacionalidad intradía, con un AUC de unos 0,69.
2. **E3 discrimina bastante mejor:** su AUC es de unos 0,84, y supera a E1 + h en los 4 días y en ambos lados, con una ventaja de 0,10 a 0,19 por día. Es coherente con la log-verosimilitud, que en E3 es aproximadamente la mitad de negativa que en E1.
3. **El flujo de trades es la señal principal**, seguido del libro y la volatilidad. El OFI no añade nada una vez incluidos los demás grupos. h aporta poco cuando X ya está en el modelo. El ranking por AUC coincide con el de log-verosimilitud.
4. **RF ≈ GBM**, con una diferencia de 0,003 a 0,004 de AUC, pero el RF tarda unas 35 veces más. GBM sigue como estimador principal y RF como robustez.

## Cautelas para el texto de la tesis
- **El AUC es una métrica secundaria.** Mide solo el orden de los scores para un umbral (δ = 2 bps, Δ = 1 s), no la calibración de la intensidad. La métrica principal de P1 es la log-verosimilitud de proceso puntual (y de recuentos), fuera de muestra.
- **Solo 4 días de calibración, sin independencia estricta entre ellos.** Con la prueba del signo por fechas, el p mínimo alcanzable es 0,0625. Hay que presentarlo como evidencia descriptiva y consistente, no como significativa.
- **Hiperparámetros no ajustados.** Los del GBM aún no están fijados en calibración, así que la cifra puede subir algo o variar.
- **Causalidad:** sin fuga detectable (sonda del reloj en v37). El libro va unos 90 ms por detrás del reloj de los trades, de modo que X(t) es causal pero algo antiguo.
- **Comparación con el piloto del anteproyecto:** allí el AUC fue 0,82, con otra partición y otra muestra. La comparación es solo orientativa.
- **Pendiente para la versión final de P1:**
  - repetir en validación externa (requiere autorización), con la especificación congelada;
  - añadir el AUC por δ (0,5–5 bps) y por Δ (100 ms, 1 s);
  - añadir intervalos por bootstrap de bloques por día.
