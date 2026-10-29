# v107: verificación del gradiente y de la convergencia de la curva de E3 (29 oct; solo entrenamiento; aprobado por Santiago: "haz eso")

**Problema (revisión externa):**
- en `ModeloFKX._paso`, m(X) = exp(clip(Z·b, −5, 5)), pero el gradiente respecto de b no incorpora el recorte;
- el ajuste usa `res.x` sin comprobar `res.success`.

**Qué se hace, sin tocar los GBM ni los Hawkes:**
1. Se cargan los 67 días de entrenamiento y los modelos finales v103.
2. Para E3 tesis (E3-fkX+B) y E3-fkX, en cada lado, se fijan g + h + c0 en sus valores finales (`eta` del modelo).
3. Desde la solución final (a = 0, θ = θ(f), b) se ejecuta:
   - **A.** El paso original (gradiente sin recorte, maxiter 200): se registran success, nit y la norma del gradiente.
   - **B.** El paso con el gradiente corregido (derivada nula donde el recorte está activo) y maxiter 2000: se registran success, nit, la ganancia de log-verosimilitud por segundo y los cambios máximos en f y en b.
   - **C.** Una comprobación del gradiente analítico frente a diferencias finitas, en una submuestra.

**Criterio fijado antes de correr:**
- Si en B la ganancia de log-verosimilitud es < 1e-4 por segundo, max|Δf| < 0,01 y max|Δb| < 0,005 en los cuatro casos, los modelos v103 quedan verificados y no se reentrena nada.
- Si no, se informa a Santiago antes de reentrenar.

El test no se toca.
