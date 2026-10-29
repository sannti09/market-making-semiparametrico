#!/usr/bin/env python3
"""Exporta el paquete para Colab: por día (29 jun–3 sep) bins de 1 s (t_ms, hora, conteos ask/bid por δ) desde la caché de v98
(cargador sobre la carpeta unificada) y eventos agresor (T_us, tipo 0=compra/ask, 1=venta/bid) desde 00_DATOS. Sin covariables."""
import json, shutil, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parent; RR = R.parent
sys.path.insert(0, str(RR / "03_cargador_datos" / "codigo"))
import cargador_v98 as N  # noqa: E402
from datos_capa_100ms import eventos_agresor  # noqa: E402
from convenciones import DISTANCIAS_BPS_DEF  # noqa: E402
P = R / "paquete"; d = date(2026, 6, 29); tot = 0
while d <= date(2026, 9, 3):
    b = N.bins(d, DISTANCIAS_BPS_DEF)
    tr = pq.read_table(N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    T, _, C = eventos_agresor(tr["event_time_us"].to_numpy(), tr["price"].to_numpy(), tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    f = P / "dias" / f"{d}.npz"
    np.savez_compressed(f, t_ms=b["t_ms"], hora=b["hora_utc"].astype(np.int8), c_ask=b["conteos"]["ask"].astype(np.int16), c_bid=b["conteos"]["bid"].astype(np.int16),
                        deltas=b["deltas_bps"], T_us=T.astype(np.int64), tipo=np.where(C, 0, 1).astype(np.int8))
    tot += f.stat().st_size; print(d, len(b["t_ms"]), len(T), f"{f.stat().st_size / 1e6:.1f} MB", flush=True); d += timedelta(days=1)
shutil.copy(RR / "03_cargador_datos" / "salida" / "por_dia_v98.json", P / "por_dia_v98_E3.json")
# ESPECIFICACION_E2_v46.json (especificación de E2 de la fase de desarrollo) ya está incluida en paquete/
print(f"total {tot / 1e6:.0f} MB")
