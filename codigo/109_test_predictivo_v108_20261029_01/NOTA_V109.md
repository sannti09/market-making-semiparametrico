# NOTA v109 — test 4–20 sep con modelos v108 (29 oct)

Repetición de la evaluación de v104 con `modelos_finales_v108.pkl` (pkl sha256 verificado contra `MANIFIESTO_v108.json`). Enmienda `ENMIENDA_V109.md` verificada antes de correr. Salida: `salida/resultados_test_v101.json`, `salida/por_dia_test_v109.json`, `salida/stdout_test_v109.txt`. Tablas: `tablas_tesis/T5_test.{md,csv,tex}`.

**Advertencia:** el periodo 4–20 sep ya fue consultado con v103 y con una versión anterior de E3. No es una evaluación ciega.

## Criterios (preregistro v101)

| Criterio | v109 |
|---|---|
| C1 jerarquía (IC95 > 0 frente a E1+h-f, E1+S, E1+X49, E2m+h-f, E2m+S, ambos lados) | True |
| C2 consistencia vs E2m+S (E3 gana ≥ 14/17 días, ambos lados) | True |
| C3 AUC ≥ 0,80 (ambos lados) | True |
| C4 rebote ≤ 0,15 (vendedores y compradores) | True |

## Tabla por modelo (dll = ll/bin de E3 tesis menos ll/bin del modelo)

| Modelo | dll ask [IC95] | Días ask | AUC ask | dll bid [IC95] | Días bid | AUC bid |
|---|---|---|---|---|---|---|
| E3 tesis (ref.) | — | — | 0,8128 | — | — | 0,8126 |
| E3-fkX (44 cov.) | +0,002 [−0,004; +0,008] | 10/17 | 0,8130 | +0,015 [+0,003; +0,029] | 13/17 | 0,8125 |
| E3 base | +0,053 [+0,034; +0,073] | 16/17 | 0,8120 | +0,087 [+0,047; +0,134] | 17/17 | 0,8095 |
| AS base (E1) | +1,316 [+0,880; +1,810] | 17/17 | 0,5000 | +1,340 [+0,835; +1,953] | 17/17 | 0,5000 |
| AS + hora + f(δ) (E1+h-f) | +1,191 [+0,789; +1,671] | 17/17 | 0,6119 | +1,200 [+0,759; +1,714] | 17/17 | 0,6127 |
| AS + 7 señales (E1+S) | +0,742 [+0,508; +1,010] | 17/17 | 0,7137 | +0,764 [+0,526; +1,036] | 17/17 | 0,7145 |
| GLM lineal 49 cov. (E1+X49) | +0,110 [+0,077; +0,145] | 16/17 | 0,8007 | +0,140 [+0,089; +0,193] | 16/17 | 0,7982 |
| Hawkes 1 esc. + hora + f(δ) (E2+h-f) | +1,170 [+0,775; +1,644] | 17/17 | 0,6268 | +1,175 [+0,743; +1,678] | 17/17 | 0,6268 |
| Hawkes 1 esc. + señales (E2+S) | +0,723 [+0,494; +0,985] | 17/17 | 0,7173 | +0,742 [+0,510; +1,007] | 17/17 | 0,7178 |
| Hawkes 2 esc. + hora + f(δ) (E2m+h-f) | +0,523 [+0,377; +0,692] | 17/17 | 0,7535 | +0,505 [+0,355; +0,681] | 17/17 | 0,7434 |
| Hawkes 2 esc. + señales (E2m+S) | +0,345 [+0,251; +0,454] | 17/17 | 0,7679 | +0,354 [+0,263; +0,457] | 17/17 | 0,7578 |

Los dll con signo positivo indican que E3 tesis tiene mayor verosimilitud que el modelo de la fila.

## Brechas de E3 tesis (E3-fkX+B), v109

- Vendedores: +0,115 (v103: +0,116). Subconjunto con precio al alza: +0,124; a la baja: +0,111.
- Compradores: −0,140 (v103: −0,139). Subconjunto con precio al alza: −0,235; a la baja: −0,048.

Ambas dentro del umbral de C4 (|brecha| ≤ 0,15).

## Comparación v103 vs v109

Diferencia en dll (v109 − v103) y en AUC medio por modelo. Todas las cifras se redondean a 6 decimales.

| Modelo | dll ask: v103 → v109 (dif.) | dll bid: v103 → v109 (dif.) | AUC ask (dif.) | AUC bid (dif.) |
|---|---|---|---|---|
| E3 tesis (ref.) | cambia (ref.) | cambia (ref.) | 0,8128 → 0,8128 (sin cambio a 4 decimales) | 0,8126 → 0,8126 (sin cambio a 4 decimales) |
| E3-fkX | +0,001803 → +0,001799 (−0,000004) | +0,015150 → +0,015182 (+0,000031) | +0,000005 | 0,000000 |
| E3 base | +0,052503 → +0,052521 (+0,000018) | +0,086526 → +0,086507 (−0,000019) | 0,000000 | 0,000000 |
| E1, E1+h-f, E1+S, E1+X49, E2+h-f, E2+S, E2m+h-f, E2m+S | cambian ±0,000018 a 0,000019 | cambian ±0,000019 | 0,000000 | 0,000000 |

Lectura: las log-verosimilitudes de E1, E1+h-f, E1+S, E1+X49, E2+h-f, E2+S, E2m+h-f y E2m+S son idénticas día a día en ambas versiones. Sus dll cambian solo porque el dll es relativo a E3-fkX+B, que sí cambió: la verosimilitud total de E3-fkX+B sube 26,7 en ask y baja 27,7 en bid. Todos los dll se desplazan menos de 0,00004 y no cambia ningún IC, número de días ni criterio. La única diferencia material es la de E3-fkX, con lls diarias distintas.

Los criterios C1–C4 son idénticos en v103 y v109.
