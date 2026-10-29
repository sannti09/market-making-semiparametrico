# NOTA v98: E3 con ajuste largo (33 días) y datos unificados

Plan `PLAN_V98.md` (sha256 verificado). Cargador `codigo/cargador_v98.py`: solo la carpeta unificada, idéntico al de v58 en 7 jul, 15 ago y 27 ago (bins, X y conteos), y ahora incluye 22–25 ago. Ajuste 29 jun–31 jul (33 días); evaluación 1 ago–3 sep (34 días). No es ciega. Tablas: `salida/tablas_v98.md`.

## Veredicto
- **Modelo elegido: E3-fkX+B (49).** BT (+ tendencia) no mejora de forma significativa (Δll ask +0,007 [−0,001; +0,015], bid +0,002 [−0,010; +0,011]).
- **Rebote corregido (criterio 1 ✓):** brecha tras barridos vendedores **+0,091** y tras compradores −0,036 (ambas ≤ 0,10).

## Brechas del rebote por modelo (O/E contrario − base, δ = 2)
| modelo | tras venta | tras venta, 1 h al alza | tras compra | tras compra, 1 h a la baja |
|---|---|---|---|---|
| E3 (−kδ, 44) | +0,454 | +0,509 | +0,063 | −0,072 |
| E3-fkX (44) | +0,295 | +0,326 | −0,105 | −0,265 |
| **E3-fkX+B (49)** | **+0,091** | +0,133 | −0,036 | −0,200 |
| E3-fkX+BT (51) | +0,129 | +0,140 | −0,083 | −0,242 |

## Progresión P1 en esta partición (Δll por bin frente a E3, IC95 por días)
| lado | E3-fkX | E3-fkX+B | E3-fkX+BT | AUC E3 → B |
|---|---|---|---|---|
| ask | +0,120 [+0,058; +0,204] (33/34) | +0,131 [+0,061; +0,228] (31/34) | +0,138 [+0,071; +0,230] (33/34) | 0,8310 → 0,8308 |
| bid | +0,102 [+0,039; +0,206] (32/34) | +0,107 [+0,042; +0,211] (32/34) | +0,108 [+0,044; +0,213] (34/34) | 0,8224 → 0,8237 |

## Lectura
- **Con más días de ajuste el GBM sí aprende el rebote** usando las covariables de barrido: la brecha tras ventas pasa de 0,25 (v94, 14 días) a 0,09. La hipótesis 3 de v96 (pocos ejemplos) era la que faltaba.
- La tendencia larga ya no hace falta: con 33 días el modelo de 49 la absorbe.
- Queda un sesgo menor: tras barridos compradores en tendencia bajista, E3 sobreestima a los vendedores que siguen (−0,20).
- La mejora de E3-fkX sobre E3 en esta evaluación (+0,10 a +0,14 por bin) es mayor que en v90, porque agosto es más volátil y la cola lejana pesa más.

## Especificación de E3 que queda para la tesis
log λ(t, δ) = g(X_t) + h(t) + m(X)·f(δ), con g = GBM Poisson sobre 49 covariables (44 originales + 5 de barrido), h = hora UTC (solo ask), f(δ) monótona libre y m(X) = exp(b·z) con 4 z. Ajuste 29 jun–31 jul con la carpeta unificada.

## Aclaración del sesgo menor (limitación declarada)
Es del **modelo elegido E3-fkX+B**: tras un barrido **comprador** con el mercado **bajando en la última hora**, la brecha es −0,20 (sobreestima a los vendedores que responden). E3 base daba −0,07; aparece con f(δ)·m(X) (−0,27) y las covariables de barrido lo reducen solo en parte. En el agregado no se ve (tras compras −0,04) porque se compensa con el caso alcista (+0,05). Lectura posible: en tendencia bajista, una compra brusca (cierre de cortos o rebote técnico) no recibe tantos vendedores como espera el modelo.

## Cuadro completo 2 × 2 del rebote (brecha del lado contrario; tendencia = cambio del mid en la hora previa)
| modelo | barrido | mercado subiendo | mercado bajando | total |
|---|---|---|---|---|
| E3 base | vendedor | +0,509 | +0,380 | +0,454 |
| E3 base | comprador | +0,132 | −0,072 | +0,063 |
| E3-fkX | vendedor | +0,326 | +0,250 | +0,295 |
| E3-fkX | comprador | −0,022 | −0,265 | −0,105 |
| **E3-fkX+B (elegido)** | vendedor | +0,133 | +0,033 | **+0,091** |
| **E3-fkX+B (elegido)** | comprador | +0,048 | **−0,200** | **−0,036** |
| E3-fkX+BT | vendedor | +0,140 | +0,114 | +0,129 |
| E3-fkX+BT | comprador | +0,000 | −0,242 | −0,083 |
Positivo = llegan más agresores del lado contrario de los que E3 espera (subestima el rebote); negativo = llegan menos (lo sobreestima). La única celda con error relevante en el modelo elegido es barrido comprador en mercado bajista.

## v99: interacción barrido × tendencia (plan `PLAN_V99.md`) — NO pasa; se cierran las correcciones
- Celda comprador-bajista: −0,200 → −0,217 (no se corrige). Vendedor-bajista empeora 0,033 → 0,080 (> 0,02). Vendedor-alcista mejora 0,133 → 0,087.
- ll (BI − B): ask +0,006 [−0,000; +0,013], bid +0,008 [−0,002; +0,019] (no peor, no significativamente mejor). AUC +0,0015 en ambos lados.
- **Decisión (fijada en el plan):** la celda comprador-bajista queda como **limitación declarada** y no se intentan más correcciones. Modelo final: **E3-fkX+B (49)**.
