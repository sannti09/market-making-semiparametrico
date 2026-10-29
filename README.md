# Market Making con Aprendizaje Estadístico: intensidades semiparamétricas de órdenes en BTC/USDT

Trabajo de grado, Ciencia de Datos, Pontificia Universidad Javeriana (2026). Autor: Santiago Rueda. Tutor: Vladimir Moreno.

El repositorio contiene el documento y **solo el código y los protocolos que corresponden a lo escrito en él**. El trabajo exploratorio anterior no se incluye; está resumido en los apéndices B y C del documento.

## Estructura
- `documento/`: fuente LaTeX (`main.tex`, `capitulos/`, `figuras/`, bibliografía) y el PDF.
  - Para compilar: `tectonic -X compile main.tex`.
  - Las figuras se regeneran con `figuras/generar_figuras.py <ruta a codigo/>`.
- `codigo/`: conserva la misma estructura de carpetas con que se ejecutó, para que las rutas relativas funcionen. Cada carpeta numerada es una etapa: su plan o protocolo (`PLAN_*.md`, con su `.sha256`), su código, su nota de resultados (`NOTA_*.md`) y sus salidas resumidas.
- `requirements.txt`: versiones usadas (Python 3.14).

## Correspondencia con el documento

| Documento | Código |
|---|---|
| Cap. 6, datos (capa canónica, catálogo) | `00_DATOS_.../` (catálogo e índice de archivos; los datos no se incluyen) |
| Respuesta y covariables (Cap. 7.1; Apéndice A) | `37_.../01_pipeline/datos_capa_100ms.py`, `98_.../cargador_v98.py`, `58_.../cargador_v58.py` (conteos), `94_.../feats_v94.py` (barridos), `94_.../corrida_v97.py` (tendencia) |
| E3: g + h + m(X)·f(δ) (Cap. 5.4, 7.3) | `37_.../modelo_e3_semiparametrico.py`, `90_.../modelo_f.py`, `90_.../corrida_v90.py` (hiperparámetros y m(X)) |
| AS y Hawkes de 1 y 2 escalas, GLM (Cap. 5.2–5.3, 7.3) | `99_.../paquete/e12_colab.py`, `101_.../test_v101.py` (GLM), `99_.../exportar_paquete.py` (eventos para el Hawkes) |
| Walk-forward (Cap. 8.2) | `102_.../` (`PLAN_V102.md`, `wf_v102.py`, `tablas_v102.py`) |
| Modelos finales congelados | `103_.../` (`entrenar_v103.py`, `modelos_finales_v103.pkl`, `MANIFIESTO_v103.json`) |
| Test (Cap. 8.3–8.4) | `101_.../` (preregistro y enmienda), `104_.../` (ajuste original), `109_.../` (ajuste corregido, idéntico a 3 decimales) |
| HJB y GLFT (Cap. 5.5, 8.5) | `49_.../hjb_numerico.py` (solucionador exponencial y pruebas), `110_.../hjb_general.py` (Hamiltoniano con curva interpolada) y `110_.../verif_v110.py` (verificaciones) |
| PnL en el test (Cap. 8.6) | `110_.../econ_v110.py` (versión reportada: miope, HJB con curva interpolada y GLFT, modelos v108); versiones anteriores en `105_...` y `106_...` |
| Simulación 21 sep–26 oct (Cap. 8.7) | `111_.../sim_v111.py` (modelos y políticas congelados; control de reproducción del 4 sep) |
| Descomposición de la pérdida por ejecución (Cap. 8.8) | `112_.../sa_v112.py` |
| Verificación del gradiente y la convergencia de E3 | `107_.../` (verificación), `108_.../` (curva versión 2: `modelo_f_v2.py`, `modelos_finales_v108.pkl`) |

## Datos
Los datos (120 días de libro reconstruido cada 100 ms y 337 millones de transacciones, unos 45 GB) no se incluyen por tamaño. Su integridad se verifica con `codigo/00_DATOS_BTCUSDT_100MS_20260629_20261026/CATALOGO.json`, que guarda la huella SHA-256 de cada archivo. Para reproducir, hay que colocar los archivos en esa carpeta con la misma estructura.

## Orden de ejecución
1. `102_.../codigo/wf_v102.py`: walk-forward. Después, `tablas_v102.py`.
2. `103_.../codigo/entrenar_v103.py`: modelos finales.
3. `104_.../codigo/test_v104.py`: test predictivo. Después, `tabla_test_v104.py`.
4. `108_.../codigo/actualizar_curva_v108.py`: ajuste corregido de la curva de E3.
5. `109_.../codigo/test_v109.py`: test predictivo con el ajuste corregido.
6. `110_.../codigo/verif_v110.py` y `econ_v110.py`: verificaciones de la HJB y test económico.
7. `111_.../codigo/sim_v111.py`: simulación 21 sep–26 oct.
8. `112_.../codigo/sa_v112.py`: descomposición de la pérdida por ejecución.

Cada script comprueba al ejecutarse que su protocolo no cambió (huella SHA-256).
