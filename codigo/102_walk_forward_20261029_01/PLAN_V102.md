# v102: walk-forward dentro del entrenamiento (29 jun–3 sep), antes de entrenar los modelos finales y abrir el test. Escrito antes de correr (aprobado por Santiago el 29 oct)

**Orden acordado:** (1) walk-forward → (2) entrenar los modelos finales con 29 jun–3 sep y guardarlos → (3) test 4–20 sep una sola vez (preregistro v101 + enmienda v101b). Ningún paso lee fechas posteriores al 3 sep.

**Ventanas (expansivas, semanales):** entrena 29 jun–fin_k y evalúa los 7 días siguientes:
fin = 31 jul / 7 ago / 14 ago / 21 ago / 28 ago → evalúa 1–7 ago / 8–14 / 15–21 / 22–28 / 29 ago–3 sep (34 días fuera de muestra en total).
**Modelos: todos** (especificaciones fijas de v98/v100b; mismos hiperparámetros y semillas; actualizado a pedido de Santiago antes de correr): E3-fkX+B (E3 de la tesis), E3-fkX (44), E3 (44, −kδ); E1, E1+h-f, E1+S, E1+X49; E2+h-f, E2+S (Hawkes de 1 escala); E2m+h-f, E2m+S (2 escalas). Los Hawkes se reajustan en cada ventana con 1 de cada 3 días. Los criterios 1–2 se aplican a E3-fkX+B frente a cada uno de los demás.
**Métricas por ventana:** ll por bin (9 δ), AUC δ = 2, brechas del rebote (eventos de v92); y la misma ll **dentro de muestra** en la última semana de cada ventana de ajuste.

**Criterios (fijos):**
1. **Estabilidad:** E3-fkX+B supera a cada rival (Δll por bin > 0) en las 5 ventanas, en ambos lados.
2. **Global:** Δll de E3 frente a cada rival con IC95 bootstrap por días (34 días fuera de muestra) > 0 en ambos lados.
3. **Sobreajuste (diagnóstico):** cociente entre la ventaja de E3 sobre E1+X49 fuera de muestra y dentro de muestra. Se marca sobreajuste si es < 0,5 en 3 o más ventanas.
Si 1 o 2 fallan, o se marca sobreajuste, se informa a Santiago antes de entrenar los modelos finales.
