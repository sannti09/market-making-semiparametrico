# v96 (diagnóstico, 29 oct; aprobado por Santiago): ¿por qué E3-fkX+B sigue subestimando el rebote tras barridos vendedores?
Modelo E3-fkX+B (49 covariables) reajustado igual que v94. Eventos de v92 (θ = 0,5). Evaluación: 45 días. Brecha = O/E del lado contrario tras el barrido − O/E base del mismo lado.
1. **Tendencia:** brecha según el signo del cambio del mid en los 15 min y en la 1 h previas al barrido (sube / baja), y por mes (jul / ago–sep).
2. **Tiempo:** brecha en los bins +1 … +10 s tras el barrido (solo bins contiguos).
4. **Distancia:** brecha por δ en el primer bin.
Sin criterio de éxito: es diagnóstico. Si la brecha tras ventas se concentra en tendencia alcista → falta una covariable de tendencia larga.

## Resultado (`salida/diag_v96.md`; brecha = O/E contrario − O/E base, δ = 2 salvo el punto 4)
| | tras barrido VENDEDOR (ask) | tras barrido COMPRADOR (bid) |
|---|---|---|
| 1 h previa al alza / a la baja | **+0,38 / +0,06** | +0,11 / −0,19 |
| 15 min previos al alza / a la baja | +0,33 / +0,15 | +0,10 / −0,16 |
| julio / ago–sep | +0,29 / +0,24 | −0,23 / +0,06 |
| segundos +1 / +2 / +3 / +4…+10 | +0,25 / +0,24 / +0,18 / 0,01–0,11 | 0,01–0,04 / … / ≈ 0 |
| por δ (0,5 → 20 bps) | +0,18 … +0,25 (≤ 5 bps); +0,45 / +1,0 / +1,7 / +2,0 (7,5–20) | ≈ 0 (≤ 3 bps); −0,2 a −1,0 (≥ 5) |

**Lectura:**
- **Es la tendencia, no el mes.** Tras barridos vendedores, la brecha es +0,38 si el mercado venía subiendo en la última hora y +0,06 si venía bajando ("comprar el dip" en tendencia alcista). Julio y agosto dan casi lo mismo. E3 no tiene ninguna covariable de más de 60 s.
- **El rebote es inmediato:** está en los primeros 3 s y luego desaparece. No es un efecto retrasado.
- **Por distancia:** crece mucho en δ ≥ 7,5 bps (compradores que cruzan lejos tras la caída). Coincide con la deriva de la cola lejana ya vista en v90.
- **Corrección propuesta:** covariables de tendencia larga (cambio del mid en 15 min y 1 h) en g(X), y posiblemente en m(X) para la cola lejana.
