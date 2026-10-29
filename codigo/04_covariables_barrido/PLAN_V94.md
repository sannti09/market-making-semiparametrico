# v94 paso 1: covariables de barrido en g(X) (aprobado por Santiago el 29 oct; escrito antes de correr)

**Motivo:** paso 0 mostró que E3-fkX subestima el lado contrario tras barridos incluso dentro del ajuste (O/E 1,16–1,27 frente a ≈ 1,0): faltan covariables.

**Cambio:** a las 44 covariables de g(X) se añaden 5, calculadas en cada inicio de bin t solo con información anterior (trades con event_time < t; filas de 100 ms con ts ≤ t; capa unificada `00_DATOS_…`):
1. `barr_rec_signo`: recorrido firmado (bps, + compra / − venta) del último barrido (evento agresor del mismo instante y lado con recorrido ≥ 0,5 bps, definición de v92) en los 60 s previos; 0 si no hay.
2. `barr_vol`: log1p del volumen (BTC) de ese barrido; 0 si no hay.
3. `barr_t`: log1p(segundos desde ese barrido), tope 60.
4. `spread_max_1s`: máximo de spread_bps en las 10 filas que terminan en t.
5. `dmid_1s`: cambio firmado del mid en bps entre t − 1 s y t.
Test de no fuga obligatorio: recalcular las 5 covariables quitando todos los trades y filas posteriores a un corte; las de bins con t ≤ corte deben ser idénticas.

**Modelos:** E3-fkX (44) frente a E3-fkX+B (49). Mismos hiperparámetros, backfit, semilla, k(X) y partición que v90. Ajuste 29 jun–12 jul; evaluación 17 jul–3 sep sin 22–25 ago (45 días).

**Criterios (fijos):**
1. **Rebote:** el O/E del lado contrario tras barridos (vendedores y compradores, δ = 2 bps, eventos de v92) se acerca al O/E de la base: |O/E_contrario − O/E_base| baja frente a E3-fkX en ambos sentidos.
2. **Ajuste:** Δll total por bin de E3-fkX+B − E3-fkX con IC95 por días que no incluya valores negativos (≥ 0).
3. **Discriminación:** AUC de cruce a δ = 2 no baja más de 0,005 por lado.
Informativo: AUC de dirección a 10 s de la asimetría en los barridos (como v93).
