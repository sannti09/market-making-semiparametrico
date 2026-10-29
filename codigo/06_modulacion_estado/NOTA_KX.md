# v47: ¿mejora k(X) a E3? (protocolo PROTOCOLO_KX.json, sha256 en PROTOCOLO_KX.sha256)

Forma: k_i(X)=exp(c+b·z), z = [vol_realizada_10s, log1p(n_trades_5s), log(profundidad propia top5), imbalance_top5], estandarizadas con ajuste (NaN->0).
Ajuste en 14 días, evaluación en 4 de calibracion_interna. Referencia E3 escalar reajustada: ask -418255, bid -468377 (idéntico a v45).

| lado | b (vol, trades, prof., imb) | c | ll_pp kx | mejora | días | veredicto |
|---|---|---|---|---|---|---|
| ask | -0.071, -0.083, +0.015, +0.111 | -0.302 | -400954 | +4.14% | 4/4 | INCLUIR |
| bid | -0.067, -0.083, -0.038, -0.076 | -0.158 | -458287 | +2.15% | 3/4 | INCLUIR |

Diferencia diaria de ll_pp (kx - E3): ask +2592, +12839, +1266, +603; bid +3399, +6224, -682, +1150.
Criterio (>=3/4 días y >=0.5%): se cumple en ambos lados según la regla fijada ex ante.

AUC (δ=2 bps, media 4 días): ask 0.8402 -> 0.8386; bid 0.8426 -> 0.8425. No mejora la discriminación.

Distancia base GLFT (1/γ)ln(1+γ/k), γ=0.1, cuantiles 5/50/95% de k(X) en calibración:
- ask: k = 0.563/0.761/0.936 -> 1.635/1.234/1.015 bps (k escalar 0.620 -> 1.50)
- bid: k = 0.652/0.870/1.086 -> 1.427/1.088/0.881 bps (k escalar 0.747 -> 1.25)
Rango intercuantil ~0.6 bps en ask y ~0.55 bps en bid: k(X) sí mueve las cotizaciones, pero modestamente.

Caveats:
- Los efectos b son pequeños (|b|<=0.11 por sd); la ganancia es estadísticamente grande en ll_pp pero no en AUC.
- ll_pp es verosimilitud compuesta (filas δ anidadas); mejoras pueden reflejar la forma del perfil en δ, no un decaimiento "causal".
- El backfitting (3 it.) no está convergido: c y b siguen moviéndose y el ll_pp en ajuste no es monótono (GBM se reentrena desde cero cada iteración); resultado sensible al nº de iteraciones.
- k medio (exp(c)) difiere del k escalar de E3 porque el nivel de k(X) y g se reparten distinto; no son comparables 1 a 1.
- Un día de 4 concentra gran parte de la ganancia (ask 12839 de 17300); bid pierde un día.
- Sin muestra externa: la decisión de inclusión es sobre calibracion_interna, una sola vez; no se tocó validación externa.
