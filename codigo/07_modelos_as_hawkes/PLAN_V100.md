# v100: E1 y E2 con las señales descubiertas (aprobado por Santiago el 29 oct; escrito antes de correr)

**Principio:** no dar ventaja al semiparamétrico. Todo lo descubierto en v90–v99 que se pueda expresar sin árboles se da también a E1 y E2.
**Forma:** log λ_i(b, δ) = log Λ_i(b) + nivel_i(hora) + f_i(δ) + γ_i · Z_b (Poisson; γ por lado; backfit de 3 iteraciones entre γ y (nivel, f); Z estandarizada con media y sd del ajuste, NaN → 0).
- Λ = 1 (E1) o Λ del Hawkes de 1 escala (E2) o de 2 escalas (E2m), como en `correr_local.py` pero con la rejilla de β ampliada porque en esa corrida el β de 1 escala quedó en el borde (100): 1 escala {0,05 … 100, 300, 1000}; 2 escalas lenta {0,05; 0,2; 1} × rápida {20; 80; 300; 1000}.
- **Señales S (7):** barr_rec_signo, barr_vol, barr_t, spread_max_1s (spread ancho / precursor de salto, v91), dmid_1s (v94); dmid_15m, dmid_1h (v97). Mismos archivos que E3 (cachés de v94, calculadas solo desde la carpeta canónica, sin fuga verificada).
- **E1+X49:** Λ = 1 con las 49 covariables de E3 (44 + 5 de barrido), lineales: el rival paramétrico con toda la información de E3.
**Partición y bins:** idénticos a v98 (ajuste 29 jun–31 jul; evaluación 1 ago–3 sep; mismos bins).
**Reporte (sin umbral de éxito; es la comparación final):** Δll por bin de E3-fkX+B frente a cada modelo con IC95 por días; parte de la mejora de E3 sobre E1 que recupera cada modelo; AUC δ = 2; brechas del rebote (4 celdas de v98) para E1+S, E2+S y E1+X49.
