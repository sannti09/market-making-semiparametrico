"""v98: bins de 1 s para E3 leyendo SOLO la carpeta unificada 00_DATOS (README: todo el código nuevo lee de aquí).
Misma lógica que cargador_v58.construir_bins_v58 (copiada; v58 sin editar), salvo: una sola capa, sin fin_capa de v1, guardia 29 jun–3 sep."""
import sys, tempfile, zipfile
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
RR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RR / "01_nucleo_e3" / "01_pipeline"))
sys.path.insert(0, str(RR / "02_conteos_respuesta" / "01_codigo"))
from datos_capa_100ms import COLUMNAS_BASE, GRUPOS_X, eventos_agresor  # noqa: E402
from cargador_v58 import _conteos  # noqa: E402  (función pura)
DAT = RR / "00_datos_canonicos"; LAG_FILAS = 2
CAC = Path(__file__).resolve().parents[1] / "salida" / "cache"; CAC.mkdir(parents=True, exist_ok=True)


def guardia(d):
    if not (date(2026, 6, 29) <= d <= date(2026, 9, 3)):
        raise PermissionError(f"v98: {d} fuera del entrenamiento (29 jun–3 sep)")


def construir(d, deltas_bps, delta_s=1.0):
    guardia(d)
    cols_x = [c for g in GRUPOS_X for c in GRUPOS_X[g]]
    tb = pq.read_table(DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=COLUMNAS_BASE + cols_x)
    ts = tb["ts_ms"].to_numpy(); assert np.all(np.diff(ts) == 100)
    Xfull = np.column_stack([tb[c].to_numpy(zero_copy_only=False).astype(float) for c in cols_x])
    ofi_nulo = np.isnan(Xfull[:, [cols_x.index(c) for c in GRUPOS_X["ofi"]]]).any(1)
    if d == date(2026, 6, 29):
        ofi_nulo[0] = False
    valido = tb["state_valid"].to_numpy(zero_copy_only=False).astype(bool) & tb["target_trade_data_valid_next_100ms"].to_numpy(zero_copy_only=False).astype(bool) & ~ofi_nulo
    mid = tb["mid"].to_numpy(zero_copy_only=False).astype(float)
    n_sub = int(round(delta_s * 10)); cv = np.concatenate([[0], np.cumsum(~valido)])
    inicios = np.arange(0, len(ts) - n_sub + 1, 10)
    ok = ((cv[inicios + n_sub] - cv[inicios]) == 0) & np.isfinite(mid[inicios]); lag = np.maximum(inicios - LAG_FILAS, 0); ok &= ~ofi_nulo[lag]
    ini = inicios[ok]; t0 = ts[ini]
    tr = pq.read_table(DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    t_ev, p_ev, c_ev = eventos_agresor(tr["event_time_us"].to_numpy(), tr["price"].to_numpy(), tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    deltas = np.array(sorted(set(float(x) for x in deltas_bps)))
    return {"t_ms": t0, "X": Xfull[ini], "columnas_x": cols_x, "conteos": _conteos(t_ev, p_ev, c_ev, t0, mid[ini], deltas, delta_s),
            "deltas_bps": deltas, "exposicion_s": np.full(len(ini), delta_s), "hora_utc": ((t0 // 1000) % 86400) // 3600}


def bins(d, deltas_bps):
    deltas = np.array(sorted(set(float(x) for x in deltas_bps)))
    if not len(deltas) or not np.isfinite(deltas).all():
        raise ValueError("deltas_bps debe contener distancias finitas")
    p = CAC / f"bins_{d}.npz"
    if p.exists():
        try:
            with p.open("rb") as archivo, np.load(archivo, allow_pickle=False) as z:
                if np.array_equal(z["deltas_bps"], deltas):
                    b = {k: z[k] for k in ("t_ms", "X", "hora_utc", "exposicion_s", "deltas_bps")}
                    b |= {"conteos": {"ask": z["c_ask"], "bid": z["c_bid"]}, "columnas_x": list(z["cols"])}
                    n = len(b["t_ms"])
                    if (b["X"].shape == (n, len(b["columnas_x"])) and
                        b["hora_utc"].shape == b["exposicion_s"].shape == (n,) and
                        all(y.shape == (n, len(deltas)) for y in b["conteos"].values())):
                        return b
        except (OSError, ValueError, KeyError, EOFError, TypeError, zipfile.BadZipFile):
            pass  # Caché incompleta o incompatible: reconstruir desde la capa canónica.
    b = construir(d, deltas)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(dir=CAC, suffix=".tmp", delete=False) as f:
            temporal = Path(f.name)
            np.savez(f, t_ms=b["t_ms"], X=b["X"], hora_utc=b["hora_utc"], exposicion_s=b["exposicion_s"], deltas_bps=b["deltas_bps"],
                     c_ask=b["conteos"]["ask"], c_bid=b["conteos"]["bid"], cols=np.array(b["columnas_x"]))
        temporal.replace(p)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
    return b
