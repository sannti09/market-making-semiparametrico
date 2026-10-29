# NOTA v111 — simulación 21 sep–26 oct (36 días) con los modelos finales congelados (29 oct)
- **Control:** el script reproduce el 4 sep de v109 (predicción) y v110 (economía) con diferencia 0. Una sola ejecución (498 s).
- **Predicción:**
  - AUC de E3 tesis: 0,848 ask / 0,842 bid (en el test fue 0,813).
  - Ventaja de E3 tesis por segundo [IC95] y días ganados:

    | Frente a | ask | bid |
    |---|---|---|
    | AS base | +1,16 [0,95; 1,42], 36/36 | +1,29 [1,02; 1,58], 36/36 |
    | Hawkes 2 escalas + S | +0,35 [0,30; 0,41], 36/36 | +0,38 [0,32; 0,44], 36/36 |
    | GLM lineal | +0,11 [0,07; 0,15], 32/36 | +0,13 [0,08; 0,18], 35/36 |
    | E3-fkX | −0,003 [−0,010; 0,005], 16/36 | +0,008 [0,003; 0,014], 28/36 |

  - Criterios descriptivos: C1, C2 y C3 cumplen. **C4 no:** la brecha del rebote es +0,107 tras barridos vendedores y **+0,222 tras compradores** (en el test fue −0,14).
- **Economía (E3 tesis):**

  | Política | ejec./día | USDT/día | bps por ejecución [IC95] | días > 0 |
  |---|---|---|---|---|
  | HJB | 2 375 | −249 | −1,26 [−1,34; −1,18] | 0/36 |
  | Miope | 4 406 | −449 | −1,22 | 0/36 |
  | GLFT | 3 065 | −309 | −1,21 | 0/36 |

- **Diferencia pareada E3 − modelo, por ejecución:**
  - HJB: frente a AS base −0,056 [−0,120; +0,001], no significativa; frente a los demás, IC con 0.
  - **Miope:** frente a AS, Hawkes y GLM con f(δ) (todos cotizan siempre a 1 bp), **−0,079 [−0,128; −0,028], significativa: E3 pierde más.**
  - GLFT: todos con IC que incluye 0.
- **Resumen:** E3 sigue siendo el mejor en predicción fuera de muestra; en PnL ningún modelo es rentable ni gana con claridad, y con la regla miope E3 pierde algo más.
