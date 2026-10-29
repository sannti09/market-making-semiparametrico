#!/usr/bin/env python3
"""v106: PnL con la política HJB (y GLFT) en el test 4–20 sep, intensidades de los 11 modelos congelados v103. Ver PLAN_V106.md."""
import hashlib, json, math, sys, time
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V106.md").read_bytes()).hexdigest() == (R / "PLAN_V106.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "12_test_predictivo_ajuste_original" / "codigo")); sys.path.insert(0, str(RR / "08_hjb_exponencial"))
import test_v104 as V4  # noqa: E402  (modelos v103 verificados por sha)
import hjb_numerico as HJB  # noqa: E402  (solver v49, sin editar)
T, W, MOD, deltas, cols = V4.T, V4.W, V4.MOD, V4.deltas, V4.cols
MODELOS = ["E3-fkX+B", "E3-fkX", "E3", "E1+X49", "E2m+S", "E2m+h-f", "E2+S", "E1+S", "E2+h-f", "E1+h-f", "E1"]
G, Q, UNIDAD, HS = 0.01, 10, 0.01, (10, 60)
DJ = np.nonzero(np.isin(deltas, [0.5, 1.0, 2.0, 3.0, 5.0]))[0]
LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "hjb_v106.log").write_text("\n".join(LOG))

def exp_local(L):
    """log λ̂(δ) ≈ log A − kδ por mínimos cuadrados sobre δ ∈ {0,5; 1; 2; 3; 5}."""
    x = deltas[DJ]; xc = x - x.mean(); y = L[:, DJ]; s = (y - y.mean(1, keepdims=True)) @ xc / (xc @ xc)
    return y.mean(1) - s * x.mean(), -s

# ---- ejes de la tabla 4D con un día de ENTRENAMIENTO (3 sep), no con el test
from datetime import date  # noqa: E402
def ejes_4d():
    d = date(2026, 9, 3); b = T.dia_aj(d); pk = T.M.cargar(str(RR / "07_modelos_as_hawkes" / "paquete"), d)
    b["lam2"] = T.M.lambda_bins(MOD["H2"], pk); b["lam1"] = T.M.lambda_bins(MOD["H1"], pk)
    L = {l: W.lls(MOD, b, l, cols, deltas) for l in ("ask", "bid")}
    ks = np.concatenate([exp_local(L[l][m])[1] for l in L for m in ("E3-fkX+B", "E3-fkX")])
    lo, hi = np.percentile(ks, [0.1, 99.9]); lo, hi = max(lo * 0.9, 0.05), hi * 1.1
    log(f"ejes 4D (3 sep, entrenamiento): k ∈ [{lo:.3f}; {hi:.3f}]"); return lo, hi

TAB = {}
def tabla(clave, ka=None, kb=None, krango=None):
    if clave not in TAB:
        t = time.time(); u, v = np.linspace(-7, 4, 74), np.linspace(-5, 5, 41)
        if clave == "4d":
            lk = np.linspace(math.log(krango[0]), math.log(krango[1]), 9); TAB[clave] = HJB.Tabla(G, Q, [np.linspace(-7, 4, 37), np.linspace(-5, 5, 21), lk, lk]).construir()
        else:
            TAB[clave] = HJB.Tabla(G, Q, [u, v], ka, kb).construir()
        log(f"tabla {clave} construida ({time.time() - t:.0f} s)")
    return TAB[clave]

def politicas(L, sg, krango):
    """Para cada modelo: (Da, Db) HJB y GLFT de forma (n, 2Q+1) en bps; NaN donde no se cotiza."""
    out, rec = {}, {}
    for m in MODELOS:
        la, ka = exp_local(L["ask"][m]); lb, kb = exp_local(L["bid"][m]); Aa, Ab = np.exp(la), np.exp(lb)
        var_k = np.ptp(ka) > 1e-6 or np.ptp(kb) > 1e-6
        if var_k:
            ka, kb = np.clip(ka, *krango), np.clip(kb, *krango)
            X = np.column_stack([np.log(sg ** 2 / Aa), np.log(Ab / Aa), np.log(ka), np.log(kb)])
            Da, Db, r = tabla("4d", krango=krango).deltas(X, ka, kb)
        else:
            ka, kb = float(ka[0]), float(kb[0])
            Da, Db, r = tabla(("2d", m, round(ka, 6), round(kb, 6)), ka, kb).deltas(np.column_stack([np.log(sg ** 2 / Aa), np.log(Ab / Aa)]), ka, kb)
        qs = np.arange(-Q, Q + 1)
        ga, gb = HJB.glft(qs[None, :], G, np.reshape(ka, (-1, 1)), np.reshape(kb, (-1, 1)), Aa[:, None], Ab[:, None], sg[:, None])
        ga, gb = np.array(ga, float), np.array(gb, float); ga[:, 0] = np.nan; gb[:, -1] = np.nan
        out[(m, "HJB")], out[(m, "GLFT")] = (Da, Db), (ga, gb); rec[m] = r
    return out, rec

def simular(Da, Db, ctx):
    m0, bbt, bat, ok, mxb, mns, ev, ts, mid, mid_end, t0 = (ctx[k] for k in ("m0", "bbt", "bat", "ok", "mxb", "mns", "ev", "ts", "mid", "mid_end", "t0"))
    QA = np.maximum(np.ceil(np.nan_to_num(m0[:, None] * (1 + Da / 1e4) * 100, nan=9e15) - 1e-6), bbt[:, None] + 1)
    QB = np.minimum(np.floor(np.nan_to_num(m0[:, None] * (1 - Db / 1e4) * 100, nan=-9e15) + 1e-6), bat[:, None] - 1)
    QA[np.isnan(Da)] = np.inf; QB[np.isnan(Db)] = -np.inf
    cand = np.nonzero(ok & ((mxb > QA.min(1)) | (mns < QB.max(1))))[0].tolist()
    QA_l, QB_l, mxb_l, mns_l = QA, QB, mxb.tolist(), mns.tolist()
    q, caja, F, absq, ult = 0, 0.0, [], 0.0, 0
    for i in cand:
        absq += abs(q) * (i - ult); ult = i
        qa, qb = QA_l[i, q + Q], QB_l[i, q + Q]
        if mxb_l[i] > qa:
            tl, pl = ev["ask"][i]; F.append((int(tl[np.argmax(pl > qa)]), qa / 100, 1)); q -= 1; caja += qa / 100 * UNIDAD
        if mns_l[i] < qb:
            tl, pl = ev["bid"][i]; F.append((int(tl[np.argmax(pl < qb)]), qb / 100, -1)); q += 1; caja -= qb / 100 * UNIDAD
    absq += abs(q) * (len(m0) - ult)
    F = np.array(F, float).reshape(-1, 3); n = len(F); pnl = caja + q * mid_end * UNIDAD
    mk = []
    for H in HS:
        k = (F[:, 0].astype(np.int64) - ts[0]) // 100 + 10 * H; mh = np.where(k < len(mid), mid[np.minimum(k, len(mid) - 1)], np.nan)
        mk.append(F[:, 2] * (F[:, 1] - mh) / F[:, 1] * 1e4)
    return {"n": n, "pnl": float(pnl), "nocional": float((F[:, 1] * UNIDAD).sum()), "s10": float(np.nansum(mk[0])), "n10": int(np.isfinite(mk[0]).sum()),
            "s60": float(np.nansum(mk[1])), "n60": int(np.isfinite(mk[1]).sum()), "q_abs_medio": absq / len(m0), "q_fin": q,
            "da0_med": float(np.nanmedian(Da[ok, Q])), "db0_med": float(np.nanmedian(Db[ok, Q]))}

def dia(d, krango):
    b = T.dia_test(d, deltas, MOD); t0 = np.asarray(b["t_ms"], np.int64)
    trd = pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    te, pe, ce = T.eventos_agresor(trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    b["lam1"] = T.M.lambda_bins(MOD["H1"], {"fecha": d, "t_ms": t0, "T_us": te.astype(np.int64), "tipo": np.where(ce, 0, 1).astype(np.int8)})
    L = {l: W.lls(MOD, b, l, cols, deltas) for l in ("ask", "bid")}
    T.guardia_test(d); fe = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "best_bid", "best_ask", "mid"])
    ts = fe["ts_ms"].to_numpy(); sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool)
    mid = np.where(sv, fe["mid"].to_numpy(zero_copy_only=False).astype(float), np.nan)
    r0 = ((t0 - ts[0]) // 100).astype(np.int64); m0 = mid[r0]
    bbt = np.round(np.nan_to_num(fe["best_bid"].to_numpy(zero_copy_only=False).astype(float)[r0]) * 100); bat = np.round(np.nan_to_num(fe["best_ask"].to_numpy(zero_copy_only=False).astype(float)[r0]) * 100)
    ok = np.isfinite(m0) & (bbt > 0) & (bat > bbt)
    # σ_t causal: EWMA (semivida 60 s) del cuadrado del retorno de 1 s del mid (bps), retornos hasta el inicio del bin
    r = np.zeros(len(t0)); seg = (np.diff(t0) == 1000) & np.isfinite(m0[1:]) & np.isfinite(m0[:-1]); r[1:][seg] = 1e4 * np.log(m0[1:][seg] / m0[:-1][seg])
    a = 1 - 0.5 ** (1 / 60); v = np.empty(len(r)); acc = 0.465 ** 2
    for i, x in enumerate(r.tolist()):
        acc = (1 - a) * acc + a * x * x; v[i] = acc
    sg = np.maximum(np.sqrt(v), 1e-3)
    ev, mxb, mns = {}, np.full(len(t0), -np.inf), np.full(len(t0), np.inf)
    for lado, sel in (("ask", ce), ("bid", ~ce)):
        tl, pl = te[sel] // 1000, np.round(pe[sel] * 100); j = np.searchsorted(t0, tl, side="right") - 1; vv = (j >= 0) & (tl < t0[np.maximum(j, 0)] + 1000)
        j, tl, pl = j[vv], tl[vv], pl[vv]; ini = np.searchsorted(j, np.arange(len(t0))); fin = np.searchsorted(j, np.arange(len(t0)), side="right")
        ev[lado] = {i: (tl[ini[i]:fin[i]], pl[ini[i]:fin[i]]) for i in np.nonzero(fin > ini)[0].tolist()}
        if lado == "ask": np.maximum.at(mxb, j, pl)
        else: np.minimum.at(mns, j, pl)
    ctx = {"m0": m0, "bbt": bbt, "bat": bat, "ok": ok, "mxb": mxb, "mns": mns, "ev": ev, "ts": ts, "mid": mid, "mid_end": mid[np.nonzero(np.isfinite(mid))[0][-1]], "t0": t0}
    POL, rec = politicas(L, sg, krango)
    res = {f"{m}|{p}": simular(Da, Db, ctx) for (m, p), (Da, Db) in POL.items()}
    res["_recorte"] = rec; res["_sigma_med"] = float(np.median(sg))
    return res

if __name__ == "__main__":
    krango = ejes_4d(); por_dia = {}
    for d in T.fechas("2026-09-04", "2026-09-20"):
        t = time.time(); r = por_dia[str(d)] = dia(d, krango)
        log(f"{d} ({time.time() - t:.0f} s): " + " | ".join(f"{k}: {r[k]['n']} ej, {1e4 * r[k]['pnl'] / max(r[k]['nocional'], 1e-9):+.2f} bps" for k in ("E3-fkX+B|HJB", "E2m+S|HJB", "E1|HJB")))
        (SAL / "por_dia_v106.json").write_text(json.dumps(por_dia, indent=1))
    dias = list(por_dia); nd = len(dias); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd))
    filas, lin = [], ["### PnL con la política HJB y GLFT en el test (4–20 sep, 17 días; γ = 0,01, Q = 10; 0,01 BTC por orden; bruto, sin comisiones)", "",
                      "| Modelo | Política | δ_a en q=0 (bps, mediana) | Ejec./día | \\|q\\| medio | PnL/día (USDT) | Días > 0 | PnL por ejec. (bps) [IC95] | Markout 10 s (bps) | E3 tesis − modelo (bps/ejec.) [IC95] |",
                      "|---|---|---|---|---|---|---|---|---|---|"]
    def serie(k, c): return np.array([por_dia[d][k][c] for d in dias], float)
    for pol in ("HJB", "GLFT"):
        ref = f"E3-fkX+B|{pol}"; ra, rn = 1e4 * serie(ref, "pnl"), serie(ref, "nocional")
        for m in MODELOS:
            k = f"{m}|{pol}"; pa, pn = 1e4 * serie(k, "pnl"), serie(k, "nocional")
            bps = pa.sum() / pn.sum(); ic = np.percentile(pa[IDX].sum(1) / pn[IDX].sum(1), [2.5, 97.5])
            dif = ra[IDX].sum(1) / rn[IDX].sum(1) - pa[IDX].sum(1) / pn[IDX].sum(1); dic = np.percentile(dif, [2.5, 97.5]); d0 = ra.sum() / rn.sum() - bps
            mk10 = serie(k, "s10").sum() / serie(k, "n10").sum()
            f = {"modelo": m, "politica": pol, "da0": float(np.mean(serie(k, "da0_med"))), "ejec_dia": float(serie(k, "n").mean()), "q_abs": float(serie(k, "q_abs_medio").mean()),
                 "pnl_usdt_dia": float(serie(k, "pnl").mean()), "dias_pos": int((serie(k, "pnl") > 0).sum()), "bps": [float(bps), *map(float, ic)], "mk10": float(mk10), "dif_E3": [float(d0), *map(float, dic)]}
            filas.append(f)
            lin.append(f"| {m} | {pol} | {f['da0']:.2f} | {f['ejec_dia']:.0f} | {f['q_abs']:.1f} | {f['pnl_usdt_dia']:+.1f} | {f['dias_pos']}/17 | {bps:+.2f} [{ic[0]:+.2f}; {ic[1]:+.2f}] | {mk10:+.2f} | "
                       + ("—" if m == "E3-fkX+B" else f"{d0:+.3f} [{dic[0]:+.3f}; {dic[1]:+.3f}]") + " |")
    lin += ["", "Intensidad exponencial local por segundo (exacta en E1 y E3; aproximación para las formas f(δ)). Comisión maker Binance spot 7,5–10 bps por ejecución no incluida."]
    (SAL / "resumen_v106.json").write_text(json.dumps(filas, indent=1)); (R / "tablas_tesis" / "T7_hjb_test.md").write_text("\n".join(lin) + "\n"); log("\n".join(lin)); log("FIN")
