# NOTA v110 — HJB exacta con la curva real de cada modelo (29 oct). Solo números; sin interpretación.

Archivos: PLAN_V110.md (+sha), ENMIENDA_V110B.md (+sha), codigo/{hjb_general,datos_v110,verif_v110,econ_v110}.py, salida/{verificacion_v110,resumen_v110,por_dia_v110}.json, tablas_tesis/{T6_pnl_test,T7_hjb_test}.md. El test 4–20 sep ya había sido consultado (v104/v105/v106): no es ciego.

## 1. Verificaciones (entrenamiento, 3 sep y días de rango)

- (a) Exponencial exacta vs estacionario() de v49: máx |Δ diferencias de θ| = 1.35e-14 en 10 casos (criterio < 1e-8; prueba hecha sin el dominio [−5; 40]; con el dominio, el caso sintético k=0,3, σ=3, A=0,2/0,5 difiere 0.405, los 9 restantes < 1e-13). Resultado: OK.
- (b) H por tramos vs fuerza bruta (200 001 puntos + nodos; 270 combinaciones modelo×lado×forma×p): error relativo máx = 1.86e-08 (criterio < 1e-6). Resultado: OK.
- (c) Monotonía en 20 segundos reales por modelo: segundos con violación = 0 de 220. Resultado: OK.
- (d) Interpolación de tablas vs exacta, 150 segundos por modelo, error de δ* (bps):

| Modelo | \|q\|≤5 p50 | p99 | máx | \|q\|≤10 p50 | p99 | máx | frac. recortada |
|---|---|---|---|---|---|---|---|
| E3-fkX+B | 0.0025 | 0.0273 | 0.786 | 0.0028 | 0.0238 | 0.786 | 0.000 |
| E3-fkX | 0.0027 | 0.0128 | 0.369 | 0.0028 | 0.0144 | 0.536 | 0.000 |
| E3 | 0.0002 | 0.0007 | 0.001 | 0.0004 | 0.0012 | 0.002 | 0.000 |
| E1+X49 | 0.0009 | 0.0037 | 0.400 | 0.0008 | 0.0034 | 0.589 | 0.000 |
| E2m+S | 0.0009 | 0.0037 | 0.163 | 0.0008 | 0.0035 | 0.395 | 0.000 |
| E2m+h-f | 0.0009 | 0.0039 | 0.163 | 0.0007 | 0.0034 | 0.385 | 0.000 |
| E2+S | 0.0009 | 0.0038 | 0.163 | 0.0008 | 0.0033 | 0.164 | 0.000 |
| E1+S | 0.0009 | 0.0037 | 0.165 | 0.0008 | 0.0033 | 0.165 | 0.000 |
| E2+h-f | 0.0011 | 0.0038 | 0.164 | 0.0010 | 0.0035 | 0.396 | 0.000 |
| E1+h-f | 0.0011 | 0.0035 | 0.164 | 0.0010 | 0.0032 | 0.396 | 0.000 |
| E1 | 0.0002 | 0.0010 | 0.001 | 0.0003 | 0.0014 | 0.002 | 0.000 |

Criterios p99 < 0,05 (|q|≤5) y < 0,1 (|q|≤10). Resultado: OK.
- Forma fija: desviación máxima de la forma normalizada entre segundos (3 sep) = 1.8e-15; reproducción de g=m·f en E3-fkX(+B) (3 sep) = 3.6e-15.
- Tramos con k_s < 0,01 (corregidos a k_min): modelos con forma fija: 0 tramos; E3-fkX(+B): fracción de segundos con tramo corregido (3 sep) = 0.0000. Menor pendiente k_s de las formas fijas: 0.1619; de f (m=1) en E3-fkX(+B): 0.3058.
- Rango de m (6 días de entrenamiento, percentiles 0,1–99,9 ×0,9/×1,1): E3-fkX+B|ask: [0.510; 1.466]; E3-fkX+B|bid: [0.465; 1.532]; E3-fkX|ask: [0.511; 1.464]; E3-fkX|bid: [0.462; 1.530].
- Tiempos: verificación completa 48 s (tablas, 8 procesos: 35 s; 4D ≈ 16–17 s cada una); test (11 modelos × 4 políticas + comparación v103, 17 días) 186 s.

## 2. Fuera de rango, bordes y correcciones en el test (media / máx. por día)

| Modelo | tabla recortada (media) | máx día | m_ask fuera | m_bid fuera | seg. con k corregido | δ* en borde [−5;40] |
|---|---|---|---|---|---|---|
| E3-fkX+B | 0.0029 | 0.0100 | 0.0007 | 0.0008 | 0.0000 | 0.00e+00 |
| E3-fkX | 0.0029 | 0.0099 | 0.0007 | 0.0008 | 0.0000 | 0.00e+00 |
| E3 | 0.0013 | 0.0082 | nan | nan | nan | 0.00e+00 |
| E1+X49 | 0.0022 | 0.0172 | nan | nan | nan | 0.00e+00 |
| E2m+S | 0.0024 | 0.0173 | nan | nan | nan | 0.00e+00 |
| E2m+h-f | 0.0038 | 0.0271 | nan | nan | nan | 0.00e+00 |
| E2+S | 0.0025 | 0.0188 | nan | nan | nan | 0.00e+00 |
| E1+S | 0.0025 | 0.0188 | nan | nan | nan | 0.00e+00 |
| E2+h-f | 0.0046 | 0.0354 | nan | nan | nan | 0.00e+00 |
| E1+h-f | 0.0046 | 0.0355 | nan | nan | nan | 0.00e+00 |
| E1 | 0.0047 | 0.0323 | nan | nan | nan | 0.00e+00 |

Desviación de la forma fija en el test frente a la del 3 sep (máx. sobre días y modelos de forma fija): 1.78e-15.

## 3. Resultados del test por modelo y política (4–20 sep, γ=0,01, Q=10, bruto)

Tablas completas con IC95: tablas_tesis/T6_pnl_test.md (miope) y T7_hjb_test.md (HJB exacta, GLFT, HJB aprox. de control). Resumen:

| Modelo | Política | δ_a q=0 | Ejec./día | \|q\| | PnL/día | PnL/ejec. (bps) [IC95] |
|---|---|---|---|---|---|---|
| E3-fkX+B | Miope | 1.00 | 4222 | 5.8 | -442.8 | -1.34 [-1.48; -1.19] |
| E3-fkX+B | HJB exacta | 0.85 | 2451 | 2.5 | -252.5 | -1.32 [-1.42; -1.20] |
| E3-fkX+B | GLFT | 1.25 | 3008 | 2.2 | -289.2 | -1.23 [-1.32; -1.11] |
| E3-fkX+B | HJB aprox. (exp. local, v108) | 1.27 | 1728 | 2.4 | -175.8 | -1.30 [-1.44; -1.15] |
| E3-fkX | Miope | 1.00 | 4220 | 5.8 | -442.0 | -1.34 [-1.48; -1.19] |
| E3-fkX | HJB exacta | 0.85 | 2454 | 2.5 | -251.2 | -1.31 [-1.40; -1.21] |
| E3-fkX | GLFT | 1.26 | 3015 | 2.2 | -288.3 | -1.22 [-1.32; -1.10] |
| E3-fkX | HJB aprox. (exp. local, v108) | 1.26 | 1731 | 2.4 | -172.9 | -1.28 [-1.41; -1.14] |
| E3 | Miope | 2.00 | 1173 | 5.5 | -120.6 | -1.32 [-1.84; -0.78] |
| E3 | HJB exacta | 1.50 | 1677 | 2.4 | -175.1 | -1.34 [-1.51; -1.15] |
| E3 | GLFT | 1.51 | 2297 | 2.0 | -223.7 | -1.25 [-1.36; -1.10] |
| E3 | HJB aprox. (exp. local, v108) | 1.50 | 1677 | 2.4 | -175.1 | -1.34 [-1.51; -1.15] |
| E1+X49 | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E1+X49 | HJB exacta | 1.14 | 2549 | 2.4 | -262.2 | -1.32 [-1.40; -1.22] |
| E1+X49 | GLFT | 1.49 | 2330 | 1.9 | -226.5 | -1.24 [-1.35; -1.11] |
| E1+X49 | HJB aprox. (exp. local, v108) | 1.63 | 1700 | 2.4 | -174.4 | -1.31 [-1.46; -1.17] |
| E2m+S | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E2m+S | HJB exacta | 1.11 | 3543 | 1.9 | -354.8 | -1.28 [-1.35; -1.18] |
| E2m+S | GLFT | 1.49 | 2321 | 1.8 | -227.6 | -1.25 [-1.36; -1.12] |
| E2m+S | HJB aprox. (exp. local, v108) | 1.55 | 2054 | 1.7 | -202.5 | -1.26 [-1.36; -1.13] |
| E2m+h-f | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E2m+h-f | HJB exacta | 1.11 | 3567 | 2.1 | -357.7 | -1.28 [-1.36; -1.17] |
| E2m+h-f | GLFT | 1.48 | 2301 | 1.9 | -223.3 | -1.24 [-1.35; -1.11] |
| E2m+h-f | HJB aprox. (exp. local, v108) | 1.55 | 2016 | 2.0 | -195.4 | -1.24 [-1.34; -1.09] |
| E2+S | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E2+S | HJB exacta | 1.11 | 3805 | 1.8 | -382.3 | -1.28 [-1.36; -1.19] |
| E2+S | GLFT | 1.49 | 2311 | 1.8 | -226.8 | -1.26 [-1.35; -1.14] |
| E2+S | HJB aprox. (exp. local, v108) | 1.55 | 2230 | 1.7 | -226.5 | -1.30 [-1.41; -1.17] |
| E1+S | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E1+S | HJB exacta | 1.11 | 3820 | 1.8 | -386.1 | -1.29 [-1.37; -1.20] |
| E1+S | GLFT | 1.49 | 2310 | 1.7 | -226.9 | -1.26 [-1.35; -1.14] |
| E1+S | HJB aprox. (exp. local, v108) | 1.55 | 2246 | 1.7 | -228.2 | -1.30 [-1.41; -1.17] |
| E2+h-f | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E2+h-f | HJB exacta | 1.11 | 3966 | 2.1 | -394.5 | -1.27 [-1.35; -1.17] |
| E2+h-f | GLFT | 1.48 | 2255 | 1.8 | -222.5 | -1.26 [-1.36; -1.13] |
| E2+h-f | HJB aprox. (exp. local, v108) | 1.55 | 2232 | 1.9 | -224.7 | -1.29 [-1.40; -1.14] |
| E1+h-f | Miope | 1.00 | 3806 | 5.5 | -385.3 | -1.29 [-1.45; -1.14] |
| E1+h-f | HJB exacta | 1.11 | 3982 | 2.1 | -398.2 | -1.28 [-1.35; -1.18] |
| E1+h-f | GLFT | 1.48 | 2253 | 1.8 | -221.7 | -1.26 [-1.36; -1.12] |
| E1+h-f | HJB aprox. (exp. local, v108) | 1.55 | 2252 | 1.9 | -225.7 | -1.28 [-1.39; -1.14] |
| E1 | Miope | 2.00 | 1173 | 5.5 | -120.6 | -1.32 [-1.84; -0.78] |
| E1 | HJB exacta | 1.55 | 2218 | 2.0 | -219.2 | -1.26 [-1.37; -1.14] |
| E1 | GLFT | 1.49 | 2223 | 1.9 | -218.0 | -1.25 [-1.35; -1.13] |
| E1 | HJB aprox. (exp. local, v108) | 1.55 | 2218 | 2.0 | -219.2 | -1.26 [-1.37; -1.14] |

## 4. HJB exacta vs HJB con exponencial local (ambas con modelos v108, test)

Precio distinto = precio cotizado distinto tras redondear al tick (decisiones = segundos × q × lado; q=0 por separado). Diferencias = exacta − aproximada, [IC95 bootstrap por días]. Comisión maker c por ejecución (bps del nocional): neto en bps/ejec. = bruto − c; PnL neto/día = PnL − c·1e-4·nocional.

| Modelo | % dec. distintas | % en q=0 | Ejec./día ex / ap | Δ ejec./día [IC] | \|q\| ex / ap | Δ\|q\| [IC] | bps/ejec. bruto ex / ap | Δ bruto [IC] |
|---|---|---|---|---|---|---|---|---|
| E3-fkX+B | 86.38 | 92.23 | 2451 / 1728 | +723.941 [+545.463; +889.651] | 2.52 / 2.40 | +0.120 [+0.031; +0.212] | -1.317 / -1.302 | -0.015 [-0.082; +0.051] |
| E3-fkX | 86.15 | 91.93 | 2454 / 1731 | +722.941 [+544.703; +886.656] | 2.50 / 2.38 | +0.118 [+0.018; +0.213] | -1.309 / -1.278 | -0.031 [-0.108; +0.043] |
| E3 | 7.68 | 0.90 | 1677 / 1677 | +0.118 [+0.000; +0.353] | 2.42 / 2.42 | -0.000 [-0.000; +0.000] | -1.337 / -1.337 | -0.000 [-0.001; -0.000] |
| E1+X49 | 90.71 | 98.14 | 2549 / 1700 | +849.353 [+622.332; +1068.238] | 2.42 / 2.42 | +0.005 [-0.081; +0.090] | -1.316 / -1.313 | -0.003 [-0.074; +0.081] |
| E2m+S | 97.87 | 100.00 | 3543 / 2054 | +1489.176 [+1145.434; +1815.931] | 1.86 / 1.73 | +0.125 [+0.026; +0.225] | -1.281 / -1.262 | -0.019 [-0.085; +0.057] |
| E2m+h-f | 98.52 | 100.00 | 3567 / 2016 | +1551.059 [+1188.346; +1894.863] | 2.13 / 1.99 | +0.145 [+0.022; +0.268] | -1.282 / -1.240 | -0.042 [-0.100; +0.015] |
| E2+S | 98.27 | 99.95 | 3805 / 2230 | +1575.471 [+1227.882; +1904.075] | 1.83 / 1.68 | +0.156 [+0.072; +0.249] | -1.284 / -1.300 | +0.015 [-0.047; +0.091] |
| E1+S | 98.26 | 99.94 | 3820 / 2246 | +1574.412 [+1225.375; +1902.178] | 1.83 / 1.67 | +0.156 [+0.068; +0.257] | -1.292 / -1.300 | +0.008 [-0.053; +0.079] |
| E2+h-f | 99.05 | 100.00 | 3966 / 2232 | +1734.529 [+1351.663; +2099.309] | 2.05 / 1.94 | +0.108 [+0.005; +0.206] | -1.272 / -1.289 | +0.017 [-0.047; +0.081] |
| E1+h-f | 99.05 | 100.00 | 3982 / 2252 | +1730.941 [+1348.831; +2091.496] | 2.05 / 1.94 | +0.113 [+0.009; +0.216] | -1.278 / -1.283 | +0.004 [-0.056; +0.064] |
| E1 | 6.28 | 0.79 | 2218 / 2218 | -0.353 [-0.706; +0.000] | 1.99 / 1.99 | -0.000 [-0.000; +0.000] | -1.265 / -1.264 | -0.000 [-0.001; +0.000] |

Neto con comisión (bps/ejec. exacta / aproximada; la diferencia por ejecución es igual a la bruta) y PnL neto/día en USDT:

| Modelo | neto 7,5 bps ex / ap | neto 10 bps ex / ap | USDT/día neto 7,5: ex / ap | Δ [IC] | USDT/día neto 10: ex / ap | Δ [IC] |
|---|---|---|---|---|---|---|
| E3-fkX+B | -8.82 / -8.80 | -11.32 / -11.30 | -1690 / -1189 | -502 [-618; -377] | -2170 / -1526 | -644 [-792; -484] |
| E3-fkX | -8.81 / -8.78 | -11.31 / -11.28 | -1691 / -1188 | -503 [-618; -381] | -2171 / -1526 | -644 [-791; -488] |
| E3 | -8.84 / -8.84 | -11.34 / -11.34 | -1158 / -1157 | -0 [-0; -0] | -1485 / -1485 | -0 [-0; -0] |
| E1+X49 | -8.82 / -8.81 | -11.32 / -11.31 | -1756 / -1170 | -586 [-739; -426] | -2254 / -1502 | -752 [-947; -548] |
| E2m+S | -8.78 / -8.76 | -11.28 / -11.26 | -2433 / -1406 | -1027 [-1258; -784] | -3125 / -1807 | -1318 [-1611; -1009] |
| E2m+h-f | -8.78 / -8.74 | -11.28 / -11.24 | -2450 / -1377 | -1073 [-1316; -820] | -3147 / -1771 | -1376 [-1688; -1054] |
| E2+S | -8.78 / -8.80 | -11.28 / -11.30 | -2614 / -1534 | -1081 [-1309; -837] | -3358 / -1969 | -1389 [-1678; -1077] |
| E1+S | -8.79 / -8.80 | -11.29 / -11.30 | -2627 / -1544 | -1082 [-1310; -838] | -3374 / -1983 | -1390 [-1680; -1079] |
| E2+h-f | -8.77 / -8.79 | -11.27 / -11.29 | -2721 / -1533 | -1188 [-1439; -921] | -3497 / -1969 | -1528 [-1848; -1186] |
| E1+h-f | -8.78 / -8.78 | -11.28 / -11.28 | -2734 / -1545 | -1189 [-1439; -924] | -3513 / -1985 | -1528 [-1849; -1188] |
| E1 | -8.76 / -8.76 | -11.26 / -11.26 | -1519 / -1519 | +0 [-0; +0] | -1953 / -1953 | +0 [-0; +1] |

## 5. Comparación con v105 (miope, modelos v103) y v106 (HJB aprox., modelos v103)

Controles de reproducción del simulador (máx. sobre 17 días de |Δ ejecuciones| y |Δ PnL| entre v110 y v105/v106 para los 9 modelos idénticos a v103): miope vs v105: 0 ejec., 0.00e+00 USDT; GLFT vs v106: 0 ejec., 0.00e+00 USDT; HJB aprox. (v110, tablas v49) vs HJB v106: 0 ejec., 0.00e+00 USDT.

Controles AS base (E1) y E3 base: HJB exacta vs HJB v106 (exponencial exacta en ambos): 
- E1: ejec./día 2218.1 vs 2218.5; |q| 1.990 vs 1.990; δ_a(q=0) 1.551 vs 1.551; bps/ejec. -1.2645 vs -1.2644; % decisiones con precio distinto (exacta vs aprox.) 6.28 (q=0: 0.79).
- E3: ejec./día 1676.9 vs 1676.8; |q| 2.422 vs 2.422; δ_a(q=0) 1.502 vs 1.502; bps/ejec. -1.3371 vs -1.3367; % decisiones con precio distinto (exacta vs aprox.) 7.68 (q=0: 0.90).

Por modelo (v105/v106 usan modelos v103; en E3-fkX+B y E3-fkX cambia además la curva v108):

| Modelo | Miope v105: ejec./día, bps/ejec., δ med. | Miope v110 | HJB v106: ejec./día, \|q\|, δ_a q=0, bps/ejec. | HJB exacta v110 | GLFT v106: ejec./día, bps | GLFT v110 |
|---|---|---|---|---|---|---|
| E3-fkX+B | 4220, -1.34, 1.00 | 4222, -1.34, 1.00 | 1729, 2.40, 1.27, -1.303 | 2451, 2.52, 0.85, -1.317 | 3012, -1.232 | 3008, -1.229 |
| E3-fkX | 4212, -1.34, 1.00 | 4220, -1.34, 1.00 | 1729, 2.38, 1.26, -1.272 | 2454, 2.50, 0.85, -1.309 | 3011, -1.222 | 3015, -1.222 |
| E3 | 1173, -1.32, 2.00 | 1173, -1.32, 2.00 | 1677, 2.42, 1.50, -1.337 | 1677, 2.42, 1.50, -1.337 | 2297, -1.246 | 2297, -1.246 |
| E1+X49 | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 1700, 2.42, 1.63, -1.313 | 2549, 2.42, 1.14, -1.316 | 2330, -1.244 | 2330, -1.244 |
| E2m+S | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2054, 1.73, 1.55, -1.262 | 3543, 1.86, 1.11, -1.281 | 2321, -1.255 | 2321, -1.255 |
| E2m+h-f | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2016, 1.99, 1.55, -1.240 | 3567, 2.13, 1.11, -1.282 | 2301, -1.242 | 2301, -1.242 |
| E2+S | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2230, 1.68, 1.55, -1.300 | 3805, 1.83, 1.11, -1.284 | 2311, -1.256 | 2311, -1.256 |
| E1+S | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2246, 1.67, 1.55, -1.300 | 3820, 1.83, 1.11, -1.292 | 2310, -1.257 | 2310, -1.257 |
| E2+h-f | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2232, 1.94, 1.55, -1.289 | 3966, 2.05, 1.11, -1.272 | 2255, -1.263 | 2255, -1.263 |
| E1+h-f | 3806, -1.29, 1.00 | 3806, -1.29, 1.00 | 2252, 1.94, 1.55, -1.283 | 3982, 2.05, 1.11, -1.278 | 2253, -1.259 | 2253, -1.259 |
| E1 | 1173, -1.32, 2.00 | 1173, -1.32, 2.00 | 2218, 1.99, 1.55, -1.264 | 2218, 1.99, 1.55, -1.265 | 2223, -1.255 | 2223, -1.255 |

## 6. Predicciones v103 vs v108 en el test: |Δ log λ̂| (curva completa)

| Modelo | Lado | δ ≤ 5: máx / p99 | δ ≥ 15: máx / p99 |
|---|---|---|---|
| E3-fkX+B | ask | 0.0202 / 0.00953 | 0.2860 / 0.27210 |
| E3-fkX+B | bid | 0.0108 / 0.00574 | 0.4649 / 0.39775 |
| E3-fkX | ask | 0.0135 / 0.00736 | 0.2170 / 0.20802 |
| E3-fkX | bid | 0.0076 / 0.00582 | 0.5042 / 0.42931 |

Por δ (máx / p99):

| Modelo | Lado | 0.5 | 1 | 2 | 3 | 5 | 7.5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| E3-fkX+B | ask | 0.000 / 0.0000 | 0.002 / 0.0013 | 0.007 / 0.0034 | 0.010 / 0.0046 | 0.020 / 0.0113 | 0.032 / 0.0198 | 0.047 / 0.0303 | 0.052 / 0.0323 | 0.286 / 0.2743 |
| E3-fkX+B | bid | 0.000 / 0.0002 | 0.001 / 0.0008 | 0.004 / 0.0016 | 0.006 / 0.0029 | 0.011 / 0.0067 | 0.021 / 0.0164 | 0.027 / 0.0203 | 0.164 / 0.1354 | 0.465 / 0.4046 |
| E3-fkX | ask | 0.000 / 0.0002 | 0.002 / 0.0018 | 0.009 / 0.0042 | 0.011 / 0.0080 | 0.014 / 0.0073 | 0.032 / 0.0181 | 0.065 / 0.0457 | 0.032 / 0.0140 | 0.217 / 0.2092 |
| E3-fkX | bid | 0.000 / 0.0002 | 0.001 / 0.0004 | 0.004 / 0.0021 | 0.005 / 0.0043 | 0.008 / 0.0063 | 0.009 / 0.0045 | 0.032 / 0.0257 | 0.091 / 0.0748 | 0.504 / 0.4369 |

## 7. Supuestos tomados
- Dominio δ ∈ [−5; 40] se aplica al supremo de H (no es un recorte posterior). k_min = 0,01 bps⁻¹.
- Forma fija de los modelos m≡1 = mediana del 3 sep (verificada constante en test).
- E3-fkX(+B): m por segundo se deriva de log λ̂(20)−log λ̂(0,5) dividido por f(20); δ* se evalúa con la m real (sin recortar); solo p sale de la tabla con m recortada.
- Tablas: 2D u∈[−7,5; 4,5] (81), v∈[−5; 5] (41); 4D u 41, v 21, m 9+9. HJB aprox. de control usa las rejillas de v106 con rango de k de los 6 días de entrenamiento (común a ambos fkX).
- Markouts, IC y semilla como v105/v106; la columna 'δ mediana' de T6 es la cotizada tras redondeo (como v105).
