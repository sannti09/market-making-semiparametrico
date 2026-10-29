# v97: covariables de tendencia larga en g(X) (aprobado por Santiago el 29 oct; escrito antes de correr)

**Motivo:** v96 mostró que el rebote subestimado tras barridos vendedores depende de la tendencia de la última hora (+0,38 alcista frente a +0,06 bajista) y que E3 no tiene covariables de más de 60 s.

**Cambio:** E3-fkX+B (49) + 2 covariables = E3-fkX+BT (51):
- `dmid_15m`, `dmid_1h`: cambio firmado del mid en bps entre t − 15 min / t − 1 h y t (filas con ts ≤ t de la capa unificada; para la primera hora del día se usa el día anterior; NaN si no existe, p. ej. 29 jun). Test de no fuga como en v94.
Resto idéntico a v94 (ajuste 29 jun–12 jul, hiperparámetros, backfit, semilla, k(X)).

**Evaluación:** 45 días (17 jul–3 sep sin 22–25 ago). **Declarado:** el diagnóstico v96 usó estos mismos días, así que la evaluación no es independiente de la motivación.

**Criterios (fijos):**
1. **Rebote:** la brecha tras barridos vendedores baja frente a E3-fkX+B, y la brecha tras compradores no sube más de 0,02 en valor absoluto. Se reporta también la brecha con tendencia de 1 h al alza / a la baja.
2. **Ajuste:** Δll total por bin (BT − B) con IC95 por días cuyo límite inferior ≥ 0 en ambos lados.
3. **AUC** de cruce a δ = 2: no baja más de 0,005 por lado.
