# 00 · Canonical data

The single data folder every script reads from: BTC/USDT on Binance Spot, **29 Jun – 26 Oct 2026 (120 days)**, one file per day and layer. The data themselves are not in Git (~45 GB); see the main README for how to obtain and place them.

## Contents

| File | What it is |
|---|---|
| `market_features_100ms/…_AAAA-MM-DD.parquet` | Reconstructed order book every 100 ms plus causal features: 864,000 rows × 202 columns per day |
| `trades_event/…_AAAA-MM-DD.parquet` | Official Binance Vision trades, one row per trade (337 M in total) |
| `CATALOGO.json` | For each day and layer: rows, SHA-256, bytes, share of valid rows and clock continuity |
| `organiza_datos.py` | Script that assembled the folder |

## Checks

- The 100 ms clock is continuous on all 120 days and every day starts at 00:00 UTC.
- Valid rows (`state_valid = True`) are at least 99.95 % on every day.
- The SHA-256 of all 240 files can be verified against `CATALOGO.json` (command in the main README).

## Caveats for any loader

- Rows with `state_valid = False` (order-book resynchronisations) must be dropped, never interpolated.
- `past_*` variables exclude the current interval; the book at time `t` is the state known at `t`.
- Depth is measured in BTC; with the 19–27 Aug rally it roughly halves, so normalise it (USD or rolling windows).

Original Spanish notes on how each date range was built and cross-checked: `NOTA_DATOS.md`.

---
Protocols (`PLAN_*`, `ENMIENDA_*`) and run notes (`NOTA_*`) are kept in Spanish, exactly as they were sealed and executed.
