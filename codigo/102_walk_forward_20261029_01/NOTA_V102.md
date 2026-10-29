# NOTA v102 — walk-forward (29 oct 2026)

- 5 ventanas semanales expandibles (ajuste desde 29 jun hasta 31 jul / 7 / 14 / 21 / 28 ago; evaluación en la semana siguiente). Son 34 días fuera de muestra (1 ago–3 sep). Test 4–20 sep NO abierto.
- La ventana 1 reproduce exactamente v98/v100b (diferencia relativa 0).
- C1 estabilidad: cumple. E3 tesis supera a los 10 modelos en las 5 ventanas y en los dos lados.
- C2 global: cumple. El IC95 > 0 frente a todos los modelos; la diferencia más pequeña es frente a E3-fkX 44 cov.: ask +0.024 [+0.005; +0.050], bid +0.008 [+0.002; +0.015].
- C3 sobreajuste: no marcado. Hay 2 de 5 ventanas con cociente frente al GLM < 0,5 (V4 y V5, en los dos lados).
  - Corrección de implementación: el código contaba ventana×lado (4 de 10). El plan dice "ventanas", así que se corrigió solo el conteo; los números no cambian.
  - Limitación declarada: V4 y V5 tienen dentro de muestra la semana agitada del 15–28 ago, que infla la ventaja dentro de muestra.
- Orden estable: E3 tesis > E3-fkX > E3 base > GLM 49 > Hawkes 2 escalas + S > Hawkes 2 escalas + h-f > Hawkes 1 escala / AS + S > Hawkes 1 escala / AS + h-f > AS base.
- Modelos finales (v103, 29 jun–3 sep) guardados en 103_modelos_finales_20261029_01/modelos/, sha ba72c1c1…
- Tablas T1–T4 y gráficos G1–G4 en tablas_tesis/ (md, csv, tex, png, pdf).
