# Comparación justa E1 / E2 / E3 (29 oct 2026)

Mismos bins y días que v98 (ajuste 29 jun–31 jul; evaluación 1 ago–3 sep, 34 días), solo datos canónicos (`paquete/MANIFIESTO_ORIGEN.json`). Código: `correr_local.py` (= notebook). Salida completa: `correr_local.log`, `paquete/por_dia_E1_E2.json`.

## Paso 1: mejoras estructurales (f(δ), hora, ajuste largo, Hawkes de 2 escalas)
Parte de la mejora de E3 (E3-fkX+B) sobre E1 que recupera cada modelo, y AUC δ = 2 (ask / bid):
| modelo | ask | bid | AUC ask / bid |
|---|---|---|---|
| E1 | 0 % | 0 % | 0,50 / 0,50 |
| E1+h-f | 7,8 % | 7,2 % | 0,62 / 0,62 |
| E2 (1 escala) | 5,5 % | 6,2 % | 0,67 / 0,66 |
| E2+h-f | 13,2 % | 13,3 % | 0,65 / 0,64 |
| **E2m-f (2 escalas)** | **61,6 %** | **59,7 %** | **0,78 / 0,77** |
| E2m+h-f | 62,6 % | 60,8 % | 0,76 / 0,76 |
| E3 (−kδ, 44) | 92,1 % | 93,5 % | 0,83 / 0,82 |
| E3-fkX (44) | 99,3 % | 99,7 % | 0,83 / 0,82 |
- E3-fkX+B gana a **todas** las variantes de E1 y E2 en 34/34 días, con IC por días > 0.
- **El Hawkes de 2 escalas cambia mucho el panorama:** β elegidas 0,2 s⁻¹ (memoria ~5 s) y 80 s⁻¹ (~12 ms), ρ = 0,77. Recupera ~60 % de la mejora de E3, frente a 2–3 % del Hawkes de 1 escala de v52–v59. La afirmación "el Hawkes captura solo el 2–3 %" dependía del núcleo de una sola escala.
- Cautela: el β de 1 escala quedó en el borde de la rejilla (100); en v100 se amplía la rejilla.

## Paso 2 (v100 + enmienda v100b): señales descubiertas y rejilla de β ampliada — TABLA FINAL
Enmienda `ENMIENDA_V100B.md` (escrita antes de repetir): covariables estandarizadas recortadas a [−5, 5] (E1+X49 divergía sin recorte) y Hawkes con rejilla ampliada en todas las variantes (1 escala β = 300 s⁻¹; 2 escalas β = 1 y 300 s⁻¹, ρ = 0,71). Tabla completa: `tabla_final_E1_E2_E3.txt`.

| modelo | qué tiene | parte de la mejora de E3 (ask / bid) | AUC ask / bid | días que gana E3 |
|---|---|---|---|---|
| E1+h-f | AS + hora + f(δ) | 7,8 % / 7,2 % | 0,62 / 0,62 | 34 / 34 |
| E2+h-f | Hawkes 1 escala + hora + f(δ) | 9,6 % / 9,2 % | 0,63 / 0,63 | 34 / 34 |
| E2m+h-f | Hawkes 2 escalas + hora + f(δ) | 62,0 % / 59,2 % | 0,76 / 0,75 | 34 / 34 |
| E1+S | AS + hora + f(δ) + 7 señales (lineal) | 52,3 % / 48,2 % | 0,73 / 0,72 | 34 / 34 |
| E2+S | Hawkes 1 escala + 7 señales | 53,8 % / 50,0 % | 0,73 / 0,73 | 34 / 34 |
| **E2m+S** | **Hawkes 2 escalas + 7 señales** | **80,5 % / 75,8 %** | 0,78 / 0,77 | 34 / 34 |
| **E1+X49** | **las 49 covariables de E3, lineales (GLM)** | **92,8 % / 89,7 %** | 0,82 / 0,81 | 30 / 32 |
| E3 (−kδ, 44) | GBM | 92,1 % / 93,5 % | 0,83 / 0,82 | 31 / 32 |
| **E3-fkX+B** | **E3 de la tesis** | 100 % | 0,83 / 0,82 | — |

Brechas del rebote (vend↑ / vend↓ / comp↑ / comp↓): E1+S +0,21 / +0,28 / +0,95 / −0,31; E2m+S −0,11 / −0,04 / +0,23 / −0,51; E1+X49 +0,28 / +0,22 / +0,30 / −0,13; **E3-fkX+B +0,13 / +0,03 / +0,05 / −0,20**.

## Lectura
1. **La jerarquía se mantiene con una comparación justa:** E3 de la tesis gana a todas las variantes de E1 y E2 con IC por días > 0 (34/34 días frente a todas salvo E1+X49: 30–32/34).
2. **Gran parte de la ventaja es información, y se puede dar a los modelos clásicos:** las 7 señales llevan a AS de ~8 % a ~50 %, y al Hawkes de 2 escalas a ~78 %.
3. **El GLM lineal con las 49 covariables recupera ~90 %** (coherente con el 88–93 % de v53). El GBM añade el 7–10 % restante, +0,01 de AUC y, sobre todo, **el rebote**: ningún modelo lineal lo calibra (brechas de hasta +0,95), porque el efecto depende del signo del barrido y del contexto.
4. **El Hawkes de 2 escalas es el mejor modelo clásico sin covariables** (~60 %): la idea de que el Hawkes aporta solo 2–3 % dependía del núcleo de una escala.
