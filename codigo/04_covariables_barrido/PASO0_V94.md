# v94 paso 0 (diagnóstico, 29 oct): ¿el rebote subestimado aparece también dentro del ajuste?

Mismo cálculo que v93 (O/E del lado contrario y del mismo lado tras barridos, δ = 2 bps; E3 y E3-fkX ajustados en 29 jun–12 jul con la semilla de v90), pero sobre los **días de ajuste** (in-sample) y repitiendo la evaluación (17 jul–3 sep) para comparar.
- Si el O/E del lado contrario tras barridos vendedores también sube claramente frente a la base dentro del ajuste → **faltan covariables** (causa 1).
- Si dentro del ajuste está como la base y solo sube en la evaluación → **faltan ejemplos o cambió el régimen** (causa 2).

## Resultado (O/E a δ = 2 bps; `salida/paso0_v94.json`)
| bloque | modelo | base ask / bid | tras venta: contrario (ask) / mismo (bid) | tras compra: contrario (bid) / mismo (ask) |
|---|---|---|---|---|
| ajuste | E3 | 0,72 / 0,78 | **0,95** / 0,79 | **1,12** / 0,80 |
| ajuste | E3-fkX | 0,99 / 1,02 | **1,16** / 0,93 | **1,27** / 1,00 |
| evaluación | E3 | 0,62 / 0,61 | **0,99** / 0,62 | 0,71 / 0,65 |
| evaluación | E3-fkX | 0,87 / 0,77 | **1,21** / 0,73 | 0,83 / 0,82 |

**Veredicto: causa 1 (faltan covariables).** El rebote se subestima **incluso dentro de los días de ajuste**: con E3-fkX, bien calibrado en la base (≈ 1,0), el lado contrario queda en 1,16–1,27. El modelo no puede aprenderlo con las covariables actuales. En el ajuste el efecto aparece en los dos sentidos; en la evaluación, sobre todo tras ventas (posible componente de régimen).
