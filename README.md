# Market Making con Aprendizaje Estadístico: intensidades semiparamétricas de órdenes en BTC/USDT

Trabajo de grado, Ciencia de Datos, Pontificia Universidad Javeriana (2026). Autor: Santiago Rueda. Tutor: Vladimir Moreno.

El repositorio contiene el documento y el código, los protocolos y los resultados de la fase final del trabajo. La fase exploratoria anterior está resumida en los apéndices B y C del documento.

## Estructura

```
documento/                      Tesis en LaTeX (main.tex, capitulos/, figuras/) y PDF
captura_datos/                  Captura en el servidor: scripts de Python, servicios systemd y comandos Shell
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
| Cap. 7, datos: captura y capa canónica | `captura_datos/`, `00_datos_canonicos/`, `03_cargador_datos/` |
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

Los datos (unos 45 GB: libro reconstruido cada 100 ms y 337 millones de transacciones de BTC/USDT en Binance Spot, 29 jun–26 oct de 2026) no se incluyen en Git. Esta sección resume cómo se obtuvieron y cómo se usan.

### 1. Captura en el servidor

Los datos se capturaron en vivo en un servidor Linux dedicado, con dos capturas en paralelo (primaria y de respaldo) por flujo, servicios systemd y rotación de archivos cada 12 horas. Los scripts de Python, las unidades systemd y los comandos de instalación y operación están en [`captura_datos/`](captura_datos/README.md):

```bash
# libro: wss://data-stream.binance.vision/ws/btcusdt@depth@100ms (+ instantáneas REST /api/v3/depth)
python captura_datos/python/live_lob_capture.py --exchange binance --symbol BTCUSDT --rotate-hours 12 --root /opt/lob_system

# transacciones: wss://data-stream.binance.vision/ws/btcusdt@trade
python captura_datos/python/live_trade_capture.py --exchange binance --storage-stream binance_trades --symbol BTCUSDT \
  --binance-stream trade --rotate-hours 12 --root /opt/lob_system
```

El libro se reconstruye siguiendo el procedimiento oficial de Binance: instantánea REST y diferenciales en orden de secuencia `U/u`; los huecos no cubiertos se marcan como inválidos y no se interpolan. El código de reconstrucción y de las capas está en el repositorio público del proyecto, [Market-Making-with-Statistical-Learning](https://github.com/sannti09/Market-Making-with-Statistical-Learning) (`src/reconstruction/`, `src/trades/`, `src/features/`).

### 2. Transacciones oficiales (Binance Vision)

Las transacciones se verifican y completan con el archivo diario oficial, que incluye su suma de verificación:

```bash
D=2026-09-04
URL=https://data.binance.vision/data/spot/daily/trades/BTCUSDT/BTCUSDT-trades-$D.zip
curl -sO "$URL" && curl -sO "$URL.CHECKSUM"
shasum -a 256 -c "BTCUSDT-trades-$D.zip.CHECKSUM"
```

En el servidor, esta descarga corría cada día a las 04:00 UTC (temporizador systemd). Para un rango de fechas: `python captura_datos/python/download_binance_vision_trades.py --root /ruta --symbol BTCUSDT --start-date AAAA-MM-DD --end-date AAAA-MM-DD`, que verifica cada archivo contra su suma de verificación.

### 3. Uso en este repositorio

Colocar la capa canónica dentro de `codigo/00_datos_canonicos/`, con un archivo por día:

```
codigo/00_datos_canonicos/
  market_features_100ms/binance_market_features_100ms_BTCUSDT_AAAA-MM-DD.parquet   # 864 000 filas, 202 columnas
  trades_event/binance_trades_events_BTCUSDT_AAAA-MM-DD.parquet                     # una fila por transacción
  CATALOGO.json
```

Si los datos están en otro disco, basta con enlaces simbólicos:

```bash
cd codigo/00_datos_canonicos
ln -s /ruta/datos/market_features_100ms market_features_100ms
ln -s /ruta/datos/trades_event trades_event
```

Verificar la integridad de los 240 archivos contra el catálogo:

```bash
cd codigo/00_datos_canonicos
python - <<'EOF'
import json, hashlib
from pathlib import Path
cat = json.load(open("CATALOGO.json"))["dias"]; malos = 0
for d, capas in cat.items():
    for capa, info in capas.items():
        nombre = (f"binance_market_features_100ms_BTCUSDT_{d}.parquet" if capa == "market_features_100ms"
                  else f"binance_trades_events_BTCUSDT_{d}.parquet")
        h = hashlib.sha256(Path(capa, nombre).read_bytes()).hexdigest()
        malos += h != info["sha256"]
print("archivos que no coinciden:", malos)
EOF
```

Lectura de un día. Los archivos son grandes; conviene leer solo las columnas necesarias, con PyArrow o DuckDB, en lugar de concatenar todo en un DataFrame:

```bash
python - <<'EOF'
import pyarrow.parquet as pq
d = "2026-09-04"
libro = pq.read_table(f"codigo/00_datos_canonicos/market_features_100ms/binance_market_features_100ms_BTCUSDT_{d}.parquet",
                      columns=["ts_ms", "state_valid", "best_bid", "best_ask", "mid"])
trades = pq.read_table(f"codigo/00_datos_canonicos/trades_event/binance_trades_events_BTCUSDT_{d}.parquet",
                       columns=["event_time_us", "price", "qty", "aggressor_buy"])
print(libro.num_rows, trades.num_rows)
EOF
```

En la capa, el libro en el instante `t` es el estado conocido en `t`; las variables `past_*` excluyen el intervalo actual. Las filas con `state_valid = False` (resincronizaciones) deben descartarse, nunca interpolarse.

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
