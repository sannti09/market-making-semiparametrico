# Captura de datos en el servidor

Los datos de la tesis se capturaron en vivo en un servidor Linux dedicado en Alemania, desde los flujos públicos de Binance Spot para BTC/USDT. Esta carpeta contiene los scripts que corrían allí, copiados sin cambios del repositorio público del proyecto, [Market-Making-with-Statistical-Learning](https://github.com/sannti09/Market-Making-with-Statistical-Learning). Ese repositorio contiene también la reconstrucción del libro (`src/reconstruction/`) y la construcción de las capas (`src/trades/`, `src/features/`).

## Qué corría en el servidor

| Proceso | Script | Servicio systemd |
|---|---|---|
| Libro, captura primaria (`depth@100ms` + instantáneas REST) | `python/live_lob_capture.py` | `systemd-lob-capture-binance.service` |
| Libro, captura de respaldo | `python/live_lob_capture.py --storage-exchange binance_backup` | `systemd-lob-capture-binance-backup.service` |
| Transacciones, captura primaria (`@trade`) | `python/live_trade_capture.py` | `systemd-lob-capture-binance-trades.service` |
| Transacciones, captura de respaldo | `python/live_trade_capture.py --storage-stream binance_trades_backup` | `systemd-lob-capture-binance-trades-backup.service` |
| Descarga diaria del archivo oficial de transacciones (Binance Vision), 04:00 UTC | `python/run_daily_binance_vision_trades.py` → `python/download_binance_vision_trades.py` | `systemd-lob-binance-vision-trades-daily.service` + `.timer` |

- Las cuatro capturas corren como servicios permanentes: se reinician solas si fallan (`Restart=always`) y rotan sus archivos cada 12 horas.
- Cada mensaje se guarda sin modificar, en formato JSONL, junto con su hora de recepción (`recv_ns`): los archivos abiertos van en `raw_live/` y, al cerrarse, se comprimen en `raw_done/`.
- Primaria y respaldo son capturas separadas del mismo flujo. Al reconstruir el libro se combinan por número de secuencia (`U/u`), de modo que un mensaje perdido en una puede recuperarse de la otra.

## Instalación en el servidor (Shell)

```bash
# usuario y estructura
sudo useradd --system --create-home --home-dir /opt/lob_system lob
sudo -u lob mkdir -p /opt/lob_system/scripts
sudo -u lob python3 -m venv /opt/lob_system/venv
sudo -u lob /opt/lob_system/venv/bin/pip install websockets
sudo cp python/*.py /opt/lob_system/scripts/

# servicios
sudo cp systemd/systemd-lob-capture-binance.service                /etc/systemd/system/lob-capture-binance.service
sudo cp systemd/systemd-lob-capture-binance-backup.service         /etc/systemd/system/lob-capture-binance-backup.service
sudo cp systemd/systemd-lob-capture-binance-trades.service         /etc/systemd/system/lob-capture-binance-trades.service
sudo cp systemd/systemd-lob-capture-binance-trades-backup.service  /etc/systemd/system/lob-capture-binance-trades-backup.service
sudo cp systemd/systemd-lob-binance-vision-trades-daily.service    /etc/systemd/system/lob-binance-vision-trades-daily.service
sudo cp systemd/systemd-lob-binance-vision-trades-daily.timer      /etc/systemd/system/lob-binance-vision-trades-daily.timer
sudo systemctl daemon-reload
sudo systemctl enable --now lob-capture-binance lob-capture-binance-backup lob-capture-binance-trades lob-capture-binance-trades-backup
sudo systemctl enable --now lob-binance-vision-trades-daily.timer
```

Los capturadores solo necesitan `websockets`; la descarga diaria usa solo la biblioteca estándar.

## Operación y control (Shell)

```bash
systemctl status lob-capture-binance lob-capture-binance-backup        # estado de las capturas
journalctl -u lob-capture-binance --since "1 hour ago"                 # registro de un servicio
systemctl list-timers lob-binance-vision-trades-daily.timer            # próxima descarga diaria
ls -lh /opt/lob_system/raw_done/                                       # archivos cerrados (rotación de 12 h)
```

Las rutas exactas de salida y los nombres de archivo los fija cada script con `--root`, `--storage-exchange` y `--storage-stream`.

## Del servidor a la tesis

1. **Captura:** archivos JSONL inmutables (libro y transacciones, primaria y respaldo).
2. **Transacciones oficiales:** archivo diario de Binance Vision, con su suma de verificación.
3. **Reconstrucción del libro:** instantánea REST más diferenciales en orden `U/u`. Los huecos sin cubrir se marcan como inválidos y no se interpolan (repositorio público, `src/reconstruction/`).
4. **Capa canónica de 100 ms:** 120 días y 202 columnas, más las transacciones por evento. Su catálogo de huellas está en `codigo/00_datos_canonicos/`.
5. **Modelos y evaluación:** carpetas `codigo/01_` a `codigo/20_` de este repositorio.

Los archivos no incluyen credenciales: los flujos de Binance son públicos y no requieren clave.
