# Datos canónicos BTCUSDT 100 ms — 29 jun a 26 oct 2026 (120 días)

Carpeta única y ordenada, **un archivo por día**, para la partición nueva:
- entrenamiento: 29 jun – 3 sep;
- test: 4 – 20 sep;
- corrida libre: 21 sep – 26 oct.

Todo el código de aquí en adelante debe leer **solo de esta carpeta**.

## Contenido
- `market_features_100ms/binance_market_features_100ms_BTCUSDT_AAAA-MM-DD.parquet`: 864 000 filas por día, 202 columnas.
- `trades_event/binance_trades_events_BTCUSDT_AAAA-MM-DD.parquet`: trades oficiales de Binance Vision, 337 M en total.
- `CATALOGO.json`: para cada día y capa, el origen, el método, las filas, el sha256, los bytes, la fracción de filas válidas y la continuidad del reloj.
- `organiza_datos.py`: el script que armó la carpeta.

## Origen de cada tramo
| fechas | capa de origen | nota |
|---|---|---|
| 29 jun – 11 ago | canónico v1 (`Comparativa 1/…unified_v1…`) | enlace duro |
| 12 – 23 ago | canónico v1 | v1 venía en medios días: se **concatenaron** `_00-12` + `_12-00` (archivo nuevo, zstd) |
| 24 – 25 ago | ext_v2, construida en Colab (paquete de Drive) | llena el hueco de la v1, que terminaba el 24 a las 12:00 |
| 26 ago – 6 oct | ext_v2 local | el 16 sep es el **parche** (escaneo desde el 8 sep) |
| 7 – 26 oct | ext_v3, construida en Colab el 28 oct | el 13 oct es el **parche** (escaneo desde el 5 oct); ver `78_…/NOTA_V78.md` |

Las tres capas se construyeron con el mismo código (5 scripts con sha256 verificado).

## Verificaciones (28 oct 2026)
- **Paquete de Drive:** 48 de 48 sha256 coinciden con `MANIFIESTO_PAQUETE.json`.
- **v1 frente a v2 (20–21 ago, construidas por separado):**
  - trades: idénticos;
  - volatilidad y volúmenes acumulados: solo redondeo (error relativo mediano ~1e-12);
  - libro: 400–500 filas al día distintas en niveles profundos del ask, y 1–2 en el mejor precio (~0,06 %).
  - `segment_id` es una etiqueta propia de cada corrida y no es comparable entre capas.
- **Los 120 días:**
  - reloj continuo cada 100 ms y empiezan a las 00:00 UTC;
  - filas válidas ≥ 99,95 % en todos (mínimo: 21 ago).

## Cautelas para los cargadores
- **`segment_id` y bordes de tramo:** cambian en los inicios de tramo (26 ago; 2, 9, 16, 23 y 30 sep; 6, 13 y 20 oct) y en los días concatenados. El primer minuto de las ventanas causales arranca de cero.
- **Escala:** la profundidad está en **BTC**. Con el rally del 19 al 27 ago (de 64 000 a 79 000) baja casi a la mitad, así que conviene normalizarla (en USD o con ventanas móviles).
- **Enlaces duros:** casi todos los archivos son enlaces a las capas originales y no ocupan espacio extra.
  - **No editarlos:** modificar uno modifica también el original. Se dejaron de solo lectura.
  - Borrar `~/Downloads/PAQUETE_DESCARGA_20261028` no borra los datos de aquí.
