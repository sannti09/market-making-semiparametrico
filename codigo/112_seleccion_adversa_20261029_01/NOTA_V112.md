# NOTA v112 — descomposición de la pérdida por ejecución (selección adversa), modelos finales (29 oct; descriptivo)
- Ejecuciones del simulador de v110/v111 (modelos v108) en el test (4–20 sep) y en la simulación (21 sep–26 oct). En los 53 días y en todas las combinaciones, las ejecuciones y el PnL coinciden con el simulador.
- **Descomposición:** markout_10 = distancia capturada (respecto del mid de la decisión) + movimiento posterior a 10 s.

| Período | Combinación | Ejec./día | Capturada | Mov. 1 s | Mov. 10 s | Markout 10 s | % > 0 |
|---|---|---|---|---|---|---|---|
| test | E3 tesis, miope | 4 222 | +0,92 | −1,78 | −2,15 | −1,24 | 23 % |
| test | E3 tesis, HJB | 2 451 | +1,08 | −2,08 | −2,36 | −1,28 | 27 % |
| test | Hawkes 2 esc. + S, HJB | 3 543 | +1,01 | −1,96 | −2,28 | −1,27 | 26 % |
| test | AS base, HJB | 2 218 | +1,46 | −2,43 | −2,75 | −1,29 | 29 % |
| test | AS base, miope (δ = 2) | 1 173 | +2,00 | −3,04 | −3,31 | −1,31 | 32 % |
| simulación | E3 tesis, HJB | 2 375 | +1,04 | −1,93 | −2,28 | −1,24 | 27 % |
| simulación | AS base, HJB | 2 115 | +1,46 | −2,30 | −2,64 | −1,18 | 29 % |
| simulación | AS base, miope (δ = 2) | 975 | +2,00 | −2,92 | −3,21 | −1,21 | 32 % |

- **Regularidad, en ambos períodos y en todas las combinaciones:**
  - lo que se captura de más al cotizar más lejos (+0,9 a +2,0 bps) se pierde en un movimiento posterior mayor (−2,1 a −3,3 bps);
  - el markout queda en −1,16 a −1,31 bps;
  - el 80–90 % del movimiento a 10 s ocurre en el primer segundo.
- **Por decil de la intensidad predicha por E3 (E3 tesis, HJB):**
  - la distancia capturada sube con el decil (de 0,42 a 2,24 bps en el test);
  - el markout es casi plano (−1,03 a −1,42 en el test; −1,15 a −1,30 en la simulación).
  - Con la regla miope, el decil más alto es el peor (−1,39 test, −1,25 simulación).
