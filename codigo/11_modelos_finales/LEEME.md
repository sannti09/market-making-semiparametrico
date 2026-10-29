# v103: modelos finales (paso 1 del orden acordado con Santiago el 29 oct)
Entrena los 11 modelos con **todo el entrenamiento, 29 jun–3 sep** (carpeta canónica unificada), con las especificaciones fijas de v98/v100b, y los guarda (pickle + sha256 + hora). No lee ninguna fecha posterior al 3 sep.
Modelos: E3-fkX+B (E3 de la tesis), E3-fkX, E3; E1, E1+h-f, E1+S, E1+X49; E2+h-f, E2+S (Hawkes 1 escala); E2m+h-f, E2m+S (Hawkes 2 escalas).
Código: `codigo/entrenar_v103.py` (usa `ajustar` de `102_walk_forward…/codigo/wf_v102.py`, la misma función del walk-forward). Después: walk-forward (v102) y tablas/gráficos (`tablas_tesis/`).
