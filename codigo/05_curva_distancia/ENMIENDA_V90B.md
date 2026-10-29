# Enmienda v90b (escrita antes de correr; aprobada por Santiago el 29 oct): robustez a la verosimilitud compuesta (opción 6, Heagerty–Lele)

**Problema.** La ll de v90 suma las 9 distancias por bin, pero los cruces están anidados (un cruce a 5 bps también cuenta a 0,5–3 bps): es una verosimilitud compuesta y sobrepondera la evidencia.

**Prueba.** Mismos modelos, partición y evaluación que v90. Se reajustan con la misma semilla (deben dar exactamente los totales de v90) y se guarda la ll **por δ** por día. Para cada δ por separado, la ll de un solo δ es una verosimilitud de Poisson propia (no compuesta). Comparaciones: E3-f − E3, E3-fkX − E3, E3-kX − E3, E3-fkX − E3-kX; Δll por bin con IC95 bootstrap por días (2 000, semilla 20261028).

**Criterios (fijados ahora):**
- **Principal, δ = 2 bps** (la distancia de la AUC de P1): v90 se mantiene si E3-f − E3 tiene IC95 > 0 en los dos lados.
- **Robustez:** se reporta en cuántos de los 9 δ el IC95 de E3-f − E3 es > 0, = 0 o < 0, por lado. Si hay δ con IC < 0 se declaran.
- **Peso efectivo:** se reporta qué parte de la mejora compuesta de v90 viene de δ ≥ 7,5 bps (donde E3 estaba peor calibrado).

No cambia ningún criterio de v90; es un chequeo adicional.
