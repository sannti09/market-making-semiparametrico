# v98: E3 con ajuste largo y datos unificados (aprobado por Santiago el 29 oct; escrito antes de correr)

**Datos:** solo la carpeta unificada `00_DATOS…` (cargador `codigo/cargador_v98.py`, verificado idéntico al de v58 en 7 jul, 15 ago y 27 ago: bins, X y conteos). Guardia 29 jun–3 sep.
**Partición dentro del entrenamiento:** ajuste 29 jun–31 jul (33 días); evaluación 1 ago–3 sep (34 días, con 22–25 ago). No es ciega (estos días ya se vieron en v90–v97).
**Modelos (por lado, mismos hiperparámetros, backfit y semilla de v90):** E3 (44, −kδ); E3-fkX (44); E3-fkX+B (49, v94); E3-fkX+BT (51, v97).

**Pregunta:** con más días de ajuste, ¿el GBM aprende el rebote tras barridos (en especial en tendencia alcista)?

**Criterios (fijos):**
1. **Rebote corregido** (para el modelo elegido): |brecha tras barridos vendedores| ≤ 0,10 y |tras compradores| ≤ 0,10 (brecha = O/E del lado contrario − O/E base, δ = 2, eventos de v92). Se reportan también por tendencia de 1 h.
2. **Elección B frente a BT:** se adopta BT si Δll (BT − B) tiene IC95 por días con límite inferior ≥ 0 en ambos lados y la AUC no baja más de 0,005; si no, B.
3. Progresión P1 en esta partición: Δll por bin de cada modelo frente a E3, con IC95 por días.
