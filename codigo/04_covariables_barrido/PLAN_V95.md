# v95: E3 reducido (aprobado por Santiago el 29 oct; escrito antes de correr)

**Selección (fija, `salida/seleccion_v95.json`):** de las 49 covariables de E3-fkX+B se quitan 25: (1) las de importancia por permutación media < 0,0005 (incluye negativas); (2) en cada grupo redundante (|ρ Spearman| ≥ 0,85, `salida/redundancia_v94.txt`) se conserva la más importante (en el grupo grande del libro, las 2 más importantes: las pendientes ask y bid). Quedan 24. Las z de k(X) siguen calculándose con sus 4 covariables originales (solo g(X) se reduce).

**Para evitar circularidad:** la selección usó 10 días de evaluación (`permutacion_v94.json`); la comparación se hace en los **otros 35 días** de la evaluación (17 jul–3 sep sin 22–25 ago y sin esos 10).

**Modelos:** E3-fkX+B (49) frente a E3-fkX+R (24). Mismo ajuste (29 jun–12 jul), hiperparámetros, backfit y semilla.

**Criterios (fijos):**
1. **No peor en ll:** Δll total por bin (R − B) con IC95 por días cuyo límite superior ≥ 0 en ambos lados (si el límite inferior > 0, "mejor").
2. AUC de cruce a δ = 2: no baja más de 0,005 por lado.
3. Brechas del rebote (O/E contrario − base tras barridos): no suben más de 0,02.
4. Se reporta el tiempo de ajuste.
