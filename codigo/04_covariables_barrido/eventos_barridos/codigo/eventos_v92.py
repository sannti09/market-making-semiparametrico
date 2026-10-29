#!/usr/bin/env python3
"""v92: eventos y ejecucion taker. Guarda por celda las filas por evento. pyarrow+numpy."""
import sys, pickle, datetime as dt
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from multiprocessing import Pool

RAIZ = Path(__file__).resolve().parents[3] / "00_datos_canonicos"
SAL = Path(__file__).resolve().parents[1] / "salida"
THS = [0.5, 1.0, 2.0]; LS = [1, 2, 3]; HS = {10: 100, 30: 300, 60: 600, 300: 3000}
COLS = ["ts_ms", "state_valid", "best_bid", "best_ask", "mid", "spread_bps", "ask_qty_01", "bid_qty_01"]
F0, F1 = dt.date(2026, 6, 29), dt.date(2026, 9, 3)

def guardia(f):
    d = dt.date.fromisoformat(f)
    if d < F0 or d > F1: raise PermissionError(f"fecha fuera de entrenamiento: {f}")

def fechas():
    d, o = F0, []
    while d <= F1: o.append(d.isoformat()); d += dt.timedelta(1)
    return o

def dia(f):
    guardia(f)
    t = pq.read_table(RAIZ/"market_features_100ms"/f"binance_market_features_100ms_BTCUSDT_{f}.parquet", columns=COLS)
    d = {c: t[c].to_numpy(zero_copy_only=False) for c in COLS}
    ts = d["ts_ms"].astype(float); n = len(ts); bid, ask, mid = d["best_bid"], d["best_ask"], d["mid"]
    valid = d["state_valid"].astype(bool) & np.isfinite(bid) & np.isfinite(ask) & np.isfinite(mid)
    bps = np.where(valid, d["spread_bps"], np.nan)
    tr = pq.read_table(RAIZ/"trades_event"/f"binance_trades_events_BTCUSDT_{f}.parquet", columns=["event_time_us", "price", "qty", "aggressor_buy"])
    tt = tr["event_time_us"].to_numpy()/1000.0; tp = tr["price"].to_numpy(); tq = tr["qty"].to_numpy(); ta = tr["aggressor_buy"].to_numpy().astype(bool)
    trig = {}
    # A) spread (mismo detector v91, solo barridos)
    for th in THS:
        cond = valid & (bps >= th); pv = np.concatenate([[False], cond[:-1]])
        out = []
        for i0 in np.where(cond & ~pv)[0]:
            if i0 < 700 or i0 >= n-4000 or not valid[i0-1]: continue
            pa, pb = ask[i0-1], bid[i0-1]
            dA = ask[i0]-pa; dB = pb-bid[i0]; W = dA+dB
            if W <= 0: continue
            if dA >= 0.75*W: lado = 1
            elif dB >= 0.75*W: lado = -1
            else: continue
            a, b = np.searchsorted(tt, ts[i0-2], "right"), np.searchsorted(tt, ts[i0], "right")
            qa, pr, ag = tq[a:b], tp[a:b], ta[a:b]
            if lado == 1: v = qa[ag & (pr >= pa)].sum(); t1 = d["ask_qty_01"][i0-1]
            else: v = qa[~ag & (pr <= pb)].sum(); t1 = d["bid_qty_01"][i0-1]
            if not (t1 > 0 and v/t1 >= 0.5): continue
            out.append((i0, lado, float(bps[i0]), float(v)))
        trig[("S", th)] = out
    # B) trades: evento = mismo tiempo y mismo lado consecutivos
    key_new = np.ones(len(tt), bool); key_new[1:] = (tt[1:] != tt[:-1]) | (ta[1:] != ta[:-1])
    st = np.where(key_new)[0]; en = np.concatenate([st[1:], [len(tt)]])-1
    p0, p1 = tp[st], tp[en]; sd = np.where(ta[st], 1, -1)
    rec = sd*(p1-p0)/p0*1e4   # recorrido en la direccion del agresor
    vol = np.add.reduceat(tq, st)
    rows = np.searchsorted(ts, tt[en], "left")
    for th in THS:
        m = (rec >= th) & (rows >= 700) & (rows < n-4000)
        out, last = [], -1
        for r, s, rc, v in zip(rows[m], sd[m], rec[m], vol[m]):
            if r == last: continue
            if not valid[r]: continue
            last = r; out.append((int(r), int(s), float(rc), float(v)))
        trig[("T", th)] = out
    # ejecucion
    res = {}
    for key, ev in trig.items():
        for L in LS:
            for H, hr in HS.items():
                rowsx = []; last_exit = -1
                for (t0, s, sz, v) in ev:
                    if t0 < last_exit: continue
                    ie, ix = t0+L, t0+L+hr
                    if ix >= n or not (valid[ie] and valid[ix]): continue
                    last_exit = ix
                    gl = (bid[ix]-ask[ie])/ask[ie]*1e4      # largo
                    gs = (bid[ie]-ask[ix])/bid[ie]*1e4      # corto
                    tre = np.sign(mid[t0]/mid[t0-600]-1) if valid[t0-600] else 0
                    rowsx.append((t0, s, gl, gs, tre, sz, v))
                res[(key[0], key[1], L, H)] = np.array(rowsx, float).reshape(-1, 7)
    return f, res, {k: len(v) for k, v in trig.items()}

if __name__ == "__main__":
    fs = fechas()
    with Pool(4) as p: R = p.map(dia, fs)
    pickle.dump({f: r for f, r, _ in R}, open(SAL/"eventos_v92.pkl", "wb"))
    print("ok", len(R)); print({k: sum(c[k] for _, _, c in R) for k in R[0][2]})
