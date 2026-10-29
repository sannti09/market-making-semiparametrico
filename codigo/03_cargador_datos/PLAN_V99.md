# v99: covariables de interacción "barrido × tendencia" (aprobado por Santiago el 29 oct; escrito antes de correr). Último intento de corrección.

**Motivo:** en v98, el modelo elegido E3-fkX+B (49) deja una celda con error: tras un barrido comprador con el mercado bajando en la hora previa, brecha −0,20 (11 878 eventos). Con la tendencia por separado (BT) empeoraba (−0,24): el GBM no combina las dos piezas.
**Cambio:** E3-fkX+BI = 49 + 2 covariables: `inter_1h` = barr_rec_signo × dmid_1h y `inter_15m` = barr_rec_signo × dmid_15m (positivas si el último barrido va a favor de la tendencia, negativas si va a contracorriente; 0 sin barrido en 60 s). Sin fuga: producto de covariables ya verificadas.
**Datos y partición:** idénticos a v98 (carpeta unificada; ajuste 29 jun–31 jul; evaluación 1 ago–3 sep, 34 días). Se reajusta también E3-fkX+B con la misma semilla como referencia.
**Criterios (fijos):**
1. Celda comprador-bajista: |brecha| ≤ 0,10.
2. Las otras tres celdas: |brecha| no sube más de 0,02 frente a B.
3. Δll (BI − B) con IC95 por días cuyo límite superior ≥ 0 en ambos lados (no peor).
4. AUC δ = 2 no baja más de 0,005.
Si no cumple 1–4, la celda queda como limitación declarada y **se cierran las correcciones**.
