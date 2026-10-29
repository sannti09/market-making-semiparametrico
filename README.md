# Market Making con Aprendizaje Estadístico: intensidades semiparamétricas de órdenes en BTC/USDT

Trabajo de grado, Ciencia de Datos, Pontificia Universidad Javeriana (2026). Autor: Santiago Rueda. Tutor: Vladimir Moreno.

El repositorio contiene el documento y el código, los protocolos y los resultados de la fase final del trabajo. La fase exploratoria anterior está resumida en los apéndices B y C del documento.

## Estructura

```
documento/                      Tesis en LaTeX (main.tex, capitulos/, figuras/) y PDF
codigo/
  00_datos_canonicos/           Catálogo de los 120 días (huella SHA-256 por archivo); los datos no se incluyen
  01_nucleo_e3/                 Capa de datos, convenciones y modelo E3 base (g + h − kδ)
  02_conteos_respuesta/         Conteo de eventos agresores que alcanzan cada distancia (variable respuesta)
  03_cargador_datos/            Cargador de la capa canónica con guarda de fechas
  04_covariables_barrido/       Covariables de barrido y tendencia; eventos_barridos/ genera los barridos
  05_curva_distancia/           Curva monótona f(δ) y modulación m(X) (versión original)
  06_modulacion_estado/         Variante k(X) de la fase de desarrollo
  07_modelos_as_hawkes/         Avellaneda–Stoikov y Hawkes de 1 y 2 escalas
  08_hjb_exponencial/           Solucionador HJB con intensidad exponencial y sus pruebas
  09_protocolo_test/            Preregistro del test y funciones comunes (GLM, señales, evaluación)
  10_walk_forward/              Walk-forward de cinco ventanas (11 modelos)
  11_modelos_finales/           Ajuste de los modelos finales (29 jun–3 sep)
  12_test_predictivo_ajuste_original/
  13_pnl_miope_ajuste_original/
  14_pnl_hjb_aproximada_ajuste_original/
  15_verificacion_gradiente/    Verificación del gradiente y la convergencia de la curva de E3
  16_curva_e3_corregida/        Curva de E3 corregida; modelos finales usados en la tesis (modelos_finales_v108.pkl)
  17_test_predictivo/           Test predictivo con el ajuste corregido
  18_hjb_curva_interpolada/     HJB con la curva de distancia interpolada: verificaciones y test económico
  19_simulacion/                Simulación del 21 sep al 26 oct con modelos y políticas congelados
  20_seleccion_adversa/         Descomposición de la pérdida por ejecución
```

Cada carpeta numerada contiene su protocolo (`PLAN_*.md` o `ENMIENDA_*.md`, con su `.sha256`), su código, su nota de resultados (`NOTA_*.md`) y sus salidas resumidas. Al ejecutarse, cada script comprueba que su protocolo no cambió.

## Correspondencia con el documento

| Documento | Carpeta |
|---|---|
| Cap. 6, metodología: respuesta, modelos y evaluación | `02_`, `05_`, `07_`, `09_` |
| Cap. 7, datos: capa canónica | `00_datos_canonicos/`, `03_cargador_datos/` |
| §8.1, especificación final de E3 | `01_` a `06_` |
| §8.2, walk-forward | `10_walk_forward/` |
| §8.3–8.4, test predictivo y calibración tras barridos | `17_test_predictivo/` (idéntico a `12_` a tres decimales) |
| §8.5, política HJB | `08_hjb_exponencial/`, `18_hjb_curva_interpolada/` |
| §8.6, valor económico en el test | `18_hjb_curva_interpolada/` (versiones anteriores: `13_`, `14_`) |
| §8.7, simulación | `19_simulacion/` |
| §8.8, origen de la pérdida | `20_seleccion_adversa/` |
| Apéndice A, covariables | `01_nucleo_e3/`, `04_covariables_barrido/` |
| Verificación del gradiente y la convergencia | `15_`, `16_` |

## Datos

Los datos (unos 45 GB: libro reconstruido cada 100 ms y 337 millones de transacciones de BTC/USDT en Binance Spot, 29 jun–26 oct de 2026) no se incluyen. Para reproducir:

- colocar las carpetas `market_features_100ms/` y `trades_event/` dentro de `codigo/00_datos_canonicos/`;
- verificar los archivos con `CATALOGO.json`.

## Archivos que se regeneran

No se incluyen por su tamaño; los genera el propio código:

| Archivo | Cómo se genera |
|---|---|
| `codigo/04_covariables_barrido/eventos_barridos/salida/eventos_v92.pkl` | `eventos_barridos/codigo/eventos_v92.py` |
| `codigo/07_modelos_as_hawkes/paquete/dias/` | `07_modelos_as_hawkes/exportar_paquete.py` (eventos para el Hawkes) |
| `codigo/18_hjb_curva_interpolada/salida/tablas_v110.pkl` | `18_hjb_curva_interpolada/codigo/verif_v110.py` |
| Cachés `salida/cache/` | se crean automáticamente |

## Orden de ejecución

1. `04_.../eventos_barridos/codigo/eventos_v92.py` y `07_.../exportar_paquete.py`: insumos.
2. `10_walk_forward/codigo/wf_v102.py`, después `tablas_v102.py`.
3. `11_modelos_finales/codigo/entrenar_v103.py`, después `16_curva_e3_corregida/codigo/actualizar_curva_v108.py`.
4. `17_test_predictivo/codigo/test_v109.py`.
5. `18_hjb_curva_interpolada/codigo/verif_v110.py`, después `econ_v110.py`.
6. `19_simulacion/codigo/sim_v111.py`.
7. `20_seleccion_adversa/codigo/sa_v112.py`.

**Comprobación de reproducibilidad:** desde esta estructura, con cachés construidas desde cero, el código reproduce exactamente un día del test (4 sep): diferencia nula en la predicción, en las ejecuciones y en el PnL.

Los nombres de archivo conservan el número de versión con que se ejecutaron (por ejemplo, `wf_v102.py`), porque los protocolos sellados y las notas se refieren a ellos.

## Entorno

Python 3.14; versiones en `requirements.txt`.
