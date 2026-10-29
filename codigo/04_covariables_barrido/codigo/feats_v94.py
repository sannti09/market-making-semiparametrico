"""v94: 5 covariables de barrido por inicio de bin t (ms), solo con información anterior a t. Ver PLAN_V94.md."""
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq

RR = Path(__file__).resolve().parents[2]
DAT = RR / "00_datos_canonicos"
CAC = Path(__file__).resolve().parents[1] / "salida" / "cache"; CAC.mkdir(parents=True, exist_ok=True)
NOMBRES = ["barr_rec_signo", "barr_vol", "barr_t", "spread_max_1s", "dmid_1s"]
TH, VENT_S = 0.5, 60.0


def guardia(d: date):
    if not (date(2026, 6, 29) <= d <= date(2026, 9, 3)):
        raise PermissionError(f"v94: {d} fuera del entrenamiento")


def leer(d):
    guardia(d)
    tr = pq.read_table(DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet",
                       columns=["event_time_us", "price", "qty", "aggressor_buy"])
    fe = pq.read_table(DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet",
                       columns=["ts_ms", "state_valid", "spread_bps", "mid"])
    return ({"t": tr["event_time_us"].to_numpy(), "p": tr["price"].to_numpy(), "q": tr["qty"].to_numpy(),
             "a": tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool)},
            {"ts": fe["ts_ms"].to_numpy(), "sv": fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool),
             "sp": fe["spread_bps"].to_numpy(zero_copy_only=False).astype(float), "mid": fe["mid"].to_numpy(zero_copy_only=False).astype(float)})


def calcular(t_ms, tr, fe):
    """t_ms: inicios de bin. Trades con event_time_us < t·1000; filas con ts ≤ t."""
    tt, tp, tq, ta = tr["t"], tr["p"], tr["q"], tr["a"]
    if len(tt):
        nuevo = np.ones(len(tt), bool); nuevo[1:] = (tt[1:] != tt[:-1]) | (ta[1:] != ta[:-1])
        st = np.nonzero(nuevo)[0]; en = np.concatenate([st[1:], [len(tt)]]) - 1
        sd = np.where(ta[st], 1.0, -1.0); rec = sd * (tp[en] - tp[st]) / tp[st] * 1e4
        m = rec >= TH; te, rs, vs = tt[en][m], (sd * rec)[m], np.add.reduceat(tq, st)[m]
    else:
        te = rs = vs = np.array([])
    k = np.searchsorted(te, t_ms * 1000, side="left") - 1          # último barrido con t_evento < t
    hay = k >= 0; kk = np.maximum(k, 0)
    dt = np.where(hay, (t_ms * 1000 - te[kk]) / 1e6, np.inf) if len(te) else np.full(len(t_ms), np.inf)
    dentro = dt <= VENT_S
    f1 = np.where(dentro, rs[kk] if len(te) else 0.0, 0.0)
    f2 = np.where(dentro, np.log1p(vs[kk]) if len(te) else 0.0, 0.0)
    f3 = np.log1p(np.minimum(dt, VENT_S))
    ts, sv, sp, mid = fe["ts"], fe["sv"], fe["sp"], fe["mid"]
    r = np.searchsorted(ts, t_ms, side="right") - 1                 # fila con ts ≤ t
    spv = np.where(sv & np.isfinite(sp), sp, -np.inf)
    W = np.lib.stride_tricks.sliding_window_view(np.concatenate([np.full(9, -np.inf), spv]), 10)
    f4 = W[np.maximum(r, 0)].max(1); f4 = np.where(np.isfinite(f4), f4, np.nan)
    r0 = np.searchsorted(ts, t_ms - 1000, side="right") - 1
    ok = (r >= 0) & (r0 >= 0)
    f5 = np.where(ok, (mid[np.maximum(r, 0)] / mid[np.maximum(r0, 0)] - 1) * 1e4, np.nan)
    return np.column_stack([f1, f2, f3, f4, f5])


def feats_dia(d, t_ms):
    p = CAC / f"barr_{d}.npy"
    if p.exists():
        F = np.load(p)
        if len(F) == len(t_ms):
            return F
    tr, fe = leer(d); F = calcular(np.asarray(t_ms, np.int64), tr, fe); np.save(p, F); return F


def test_no_fuga(d, t_ms):
    """Corta trades y filas en el bin del medio; las covariables de bins con t ≤ corte no deben cambiar."""
    tr, fe = leer(d); t_ms = np.asarray(t_ms, np.int64); corte = t_ms[len(t_ms) // 2]
    A = calcular(t_ms, tr, fe)
    mt = tr["t"] < corte * 1000; mf = fe["ts"] <= corte
    B = calcular(t_ms, {k: v[mt] for k, v in tr.items()}, {k: v[mf] for k, v in fe.items()})
    sel = t_ms <= corte
    return bool(np.array_equal(np.nan_to_num(A[sel], nan=-9), np.nan_to_num(B[sel], nan=-9))), int(sel.sum())
