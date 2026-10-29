# v101: confirmación de P1 en el TEST (4–20 sep 2026). Preregistro (autorizado por Santiago el 29 oct; escrito antes de cargar ningún dato del test)

**Uso único del test.** Nada se reajusta ni se cambia después de ver el test. La corrida libre (21 sep–26 oct) sigue cerrada. No se leen los `test_*79.json` de v79.
**Datos:** solo la carpeta canónica unificada `00_DATOS…`. Guardia: el ajuste solo lee 29 jun–31 jul (y la tendencia el día previo); el test solo 4–20 sep (y 3 sep para la tendencia de la primera hora). Cualquier fecha ≥ 21 sep lanza PermissionError.

**Modelos congelados** (exactamente las especificaciones evaluadas en v98 y v100/v100b; ajuste 29 jun–31 jul; mismas semillas e hiperparámetros):
- E3-fkX+B (49 covariables) — **E3 de la tesis**; E3 (−kδ, 44); E3-fkX (44).
- E1+h-f; E1+S (7 señales); E1+X49 (GLM lineal con las 49; recorte ±5); E2m+h-f y E2m+S (Hawkes de 2 escalas, rejilla ampliada de v100b).
**Compuerta antes del test:** los modelos reajustados deben reproducir la ll de v98 (E3-fkX+B) y v100b (E2m+S, E1+X49) en el 1 ago con diferencia relativa < 1e-9. Si no, se detiene sin abrir el test. Se guardan los modelos (pickle) y un manifiesto con sha256 y hora antes de leer el primer archivo del test.

**Métricas (las de v98/v100):** ll por bin (9 δ, sin log y!), IC95 bootstrap por días (2 000, semilla 20261029); AUC δ = 2; brechas del rebote (barridos por trades θ = 0,5 bps, separación ≥ 10,1 s como v92; tendencia de 1 h; 4 celdas).

**Criterios (fijos):**
1. **Jerarquía:** E3-fkX+B supera a cada uno de E1+h-f, E1+S, E1+X49, E2m+h-f, E2m+S con IC95 de Δll por bin > 0 en ambos lados.
2. **Consistencia:** gana en ≥ 14 de 17 días a E2m+S (el mejor clásico sin covariables de E3) en ambos lados.
3. **Discriminación:** AUC δ = 2 de E3-fkX+B ≥ 0,80 en ambos lados.
4. **Rebote:** |brecha total| tras barridos vendedores y compradores ≤ 0,15 para E3-fkX+B.
5. **Informativo (sin criterio):** frente a E1+X49, E3 y E3-fkX; parte de la mejora; brechas por celda.
