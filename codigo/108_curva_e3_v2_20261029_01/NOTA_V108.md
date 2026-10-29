# NOTA v108 — versión 2 de la curva de E3 (29 oct)
- `modelo_f_v2.py` corrige el gradiente (derivada del recorte) y comprueba la convergencia. v90 y v103 no se editan.
- **Modelos v108** = v103 con la curva de E3 tesis y E3-fkX reoptimizada (g + h fijos, entrenamiento 29 jun–3 sep). pkl sha 861bc7d5…, manifiesto en `modelos/MANIFIESTO_v108.json`.
- **Convergencia:** los 4 ajustes terminan con success = True, en 70–102 iteraciones.
- **Cambios frente a v103:**
  - f(20 bps): ask −8,65 → −8,87 y bid −10,31 → −10,62 en E3 tesis; similar en E3-fkX;
  - δ ≤ 5 bps sin cambio material;
  - b ≤ 0,001;
  - ganancia de verosimilitud en el entrenamiento ≈ 6e-6 por segundo.
- **Uso:** el test (predictivo y económico) se correrá una sola vez con estos modelos, cuando se decida.
