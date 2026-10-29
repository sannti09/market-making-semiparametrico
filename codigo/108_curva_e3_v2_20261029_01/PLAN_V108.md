# v108: versión 2 de la curva de E3 (29 oct; aprobado por Santiago: "corrige la curva, pero crea una versión 2")

**Motivo (v107):**
- el gradiente de m(X) no incorporaba el recorte a ±5, que se activa en ~0,0005 % de los segundos;
- el último paso de la curva se detenía por tolerancia relativa sin converger. Al reoptimizar cambia f solo en 15–20 bps (hasta 0,33 en log), con una ganancia de verosimilitud de ~6e-6 por segundo.

**Qué se hace:**
1. `modelo_f_v2.py` (copia en esta carpeta; v90 no se edita) agrega dos cosas al paso de la curva:
   - gradiente con la derivada del recorte (nula donde |Z·b| ≥ 5);
   - L-BFGS con maxiter 2000 y registro obligatorio de `success`.
2. Con g + h + c0 de v103 fijos, se reejecuta solo el último paso de la curva de E3 tesis (E3-fkX+B) y de E3-fkX, en ambos lados, con todo el entrenamiento (29 jun–3 sep). El GBM y el resto de los modelos no se tocan.
3. Se guarda `modelos_finales_v108.pkl`: igual a v103 salvo esas cuatro curvas (f, b, c0 += a), con manifiesto sha256. v103 queda intacto.

**Criterio:** los cuatro ajustes deben terminar con `success = True`. Si alguno no converge, se detiene y se informa.

El test no se toca. Se evaluará una sola vez con estos modelos cuando se decida.
