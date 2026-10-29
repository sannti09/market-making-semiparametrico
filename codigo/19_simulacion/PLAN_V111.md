# v111: simulación del 21 sep al 26 oct de 2026 con los modelos finales congelados (29 oct; aprobado por Santiago: "hagamos el plan de simulación y sus respectivas simulaciones")

**Para qué:** ver cómo predicen y cómo operan los modelos finales en un periodo que no usaron para nada. Ningún parámetro, hiperparámetro ni decisión del protocolo final se tomó con datos posteriores al 20 sep (verificado en el código: guardas ≤ 3 sep para entrenamiento y 3–20 sep para el test).

**Qué se congela (no se reajusta nada):**
- modelos v108 (pkl sha 861bc7d5…);
- tablas HJB, rangos y formas de v110 (sha de las tablas verificado al cargar);
- γ = 0,01, Q = 10, 0,01 BTC por orden, |q| ≤ 10;
- simulador idéntico a v110: decisión al inicio del segundo sin latencia de envío, cruce estricto, una ejecución por lado y segundo, PnL valorado al último mid del día.

**Código:**
- `sim_v111.py` importa sin cambios las funciones de v110 (economía) y replica la evaluación diaria de v109 (predicción).
- Solo cambia el guarda de fechas: permite 20 sep–26 oct; el 20 sep solo se lee para la tendencia de la primera hora del 21.

**Control antes de abrir la simulación (obligatorio):** con el guarda original, el script reproduce el día 4 sep (ya consultado):
- predicción: ll de los 11 modelos por lado, idéntica a `por_dia_test_v109.json` (diferencia relativa < 1e-9);
- economía: ejecuciones y PnL de todas las políticas, idénticos a `por_dia_v110.json`.

Si algo no coincide, se detiene sin leer la simulación.

**Periodo:** 21 sep–26 oct (36 días), una sola ejecución.

**Métricas:**
- **Predicción** (como v104/v109):
  - log-verosimilitud por segundo de E3 tesis menos cada modelo, con IC95 bootstrap por días (2 000 réplicas, semilla 20261029);
  - días ganados, AUC a δ = 2 bps (promedio diario), parte de la mejora frente a AS base;
  - brecha del rebote tras barridos.
- **Economía:** miope, HJB con curva interpolada y GLFT. Por modelo:
  - ejecuciones/día, |q| medio, PnL/día y PnL por ejecución (IC95);
  - días positivos y markout a 10 s;
  - diferencia pareada E3 tesis − modelo;
  - neto con comisión de 7,5 y 10 bps.
- **Por semana** (21–27 sep, 28 sep–4 oct, 5–11 oct, 12–18 oct, 19–26 oct): AUC de E3 tesis y ventaja frente a AS base, al mejor Hawkes y al GLM; PnL por ejecución de E3 tesis con HJB.
- **Fuera de rango:** fracción de segundos fuera del rango de las tablas HJB y de m, media y máximo diario.

**Criterios (descriptivos, los del test escalados a 36 días):**
- C1: E3 tesis supera a las 5 referencias principales con IC95 > 0 en ambos lados;
- C2: gana a Hawkes 2 escalas + S en ≥ 30 de 36 días (≥ 82 %, como 14/17) en ambos lados;
- C3: AUC ≥ 0,80;
- C4: |brecha del rebote| ≤ 0,15.

No son condición de nada: se reportan tal cual.
