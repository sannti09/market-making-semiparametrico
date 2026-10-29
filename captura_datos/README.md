# Data capture on the server

The thesis data were captured live on a dedicated Linux server in Germany, from Binance Spot's public BTC/USDT streams. This folder holds the scripts that ran there. They are copied unchanged from the project's public repository, [Market-Making-with-Statistical-Learning](https://github.com/sannti09/Market-Making-with-Statistical-Learning), which also contains the book reconstruction (`src/reconstruction/`) and the construction of the layers (`src/trades/`, `src/features/`).

## What ran on the server

| Process | Script | systemd service |
|---|---|---|
| Order book, primary capture (`depth@100ms` + REST snapshots) | `python/live_lob_capture.py` | `systemd-lob-capture-binance.service` |
| Order book, backup capture | `python/live_lob_capture.py --storage-exchange binance_backup` | `systemd-lob-capture-binance-backup.service` |
| Trades, primary capture (`@trade`) | `python/live_trade_capture.py` | `systemd-lob-capture-binance-trades.service` |
| Trades, backup capture | `python/live_trade_capture.py --storage-stream binance_trades_backup` | `systemd-lob-capture-binance-trades-backup.service` |
| Daily download of the official trade file (Binance Vision), 04:00 UTC | `python/run_daily_binance_vision_trades.py` → `python/download_binance_vision_trades.py` | `systemd-lob-binance-vision-trades-daily.service` + `.timer` |

- The four captures run as permanent services: they restart on failure (`Restart=always`) and rotate their files every 12 hours.
- Every message is stored unmodified, as JSONL, with its receive time (`recv_ns`). Open files live in `raw_live/`; when closed they are compressed into `raw_done/`.
- Primary and backup are separate captures of the same stream. The reconstruction merges them by sequence number (`U/u`), so a message lost by one can be recovered from the other.

## Installing on the server (shell)

```bash
# user and layout
sudo useradd --system --create-home --home-dir /opt/lob_system lob
sudo -u lob mkdir -p /opt/lob_system/scripts
sudo -u lob python3 -m venv /opt/lob_system/venv
sudo -u lob /opt/lob_system/venv/bin/pip install websockets
sudo cp python/*.py /opt/lob_system/scripts/

# services
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

The capture scripts only need `websockets`; the daily download uses the standard library only.

## Operation and monitoring (shell)

```bash
systemctl status lob-capture-binance lob-capture-binance-backup        # state of the captures
journalctl -u lob-capture-binance --since "1 hour ago"                 # log of one service
systemctl list-timers lob-binance-vision-trades-daily.timer            # next daily download
ls -lh /opt/lob_system/raw_done/                                       # closed files (12 h rotation)
```

Exact output paths and file names are set by each script through `--root`, `--storage-exchange` and `--storage-stream`.

## From the server to the thesis

1. **Capture:** immutable JSONL files (book and trades, primary and backup).
2. **Official trades:** the daily Binance Vision file, with its checksum.
3. **Book reconstruction:** a REST snapshot plus diffs in `U/u` order. Uncovered gaps are marked invalid and never interpolated (public repository, `src/reconstruction/`).
4. **Canonical 100 ms layer:** 120 days and 202 columns, plus trades by event. Its fingerprint catalogue is in `codigo/00_datos_canonicos/`.
5. **Models and evaluation:** folders `codigo/01_` to `codigo/20_` of this repository.

No credentials are involved: Binance's streams are public and need no key.
