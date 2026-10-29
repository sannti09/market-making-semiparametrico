#!/usr/bin/env python3
"""v112: descomposición de la pérdida por ejecución (distancia capturada + movimiento posterior) con los modelos v108 y las políticas de v110,
en el test (4–20 sep) y en la simulación (21 sep–26 oct). Descriptivo. Ver PLAN_V112.md."""
import hashlib, json, sys, time
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V112.md").read_bytes()).hexdigest() == (R / "PLAN_V112.sha256").read_text().split()[0], "PLAN_V112 modificado"
sys.path.insert(0, str(RR / "18_hjb_curva_interpolada" / "codigo")); sys.path.insert(0, str(RR / "19_simulacion" / "codigo"))
import econ_v110 as E  # noqa: E402  (modelos v108, tablas y simulador de v110, sin cambios)
T, W, MOD, deltas, cols, Q, UNIDAD = E.T, E.W, E.MOD, E.deltas, E.cols, E.Q, E.UNIDAD
T.SAL = SAL
MODS = ["E3-fkX+B", "E2m+S", "E1+X49", "E1+h-f", "E1"]; POLS = ["MIOPE", "HJBx", "GLFT"]; HS = (1, 10, 60)
JD = int(np.where(deltas == 2.0)[0][0]); LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "sa_v112.log").write_text("\n".join(LOG))

def guarda_sim(d):
    if not (date(2026, 9, 20) <= d <= date(2026, 10, 26)):
        raise PermissionError(f"v112: {d} fuera de 20 sep–26 oct")

def ejecuciones(QA, QB, ctx):
    """Mismo bucle que E.simular, pero devuelve cada ejecución: (segundo i, t_ejec ms, precio, s)."""
    ok, mxb, mns, ev = ctx["ok"], ctx["mxb"], ctx["mns"], ctx["ev"]
    cand = np.nonzero(ok & ((mxb > QA.min(1)) | (mns < QB.max(1))))[0].tolist(); q, out = 0, []
    for i in cand:
        qa, qb = QA[i, q + Q], QB[i, q + Q]
        if mxb[i] > qa:
            tl, pl = ev["ask"][i]; out.append((i, int(tl[np.argmax(pl > qa)]), qa / 100, 1)); q -= 1
        if mns[i] < qb:
            tl, pl = ev["bid"][i]; out.append((i, int(tl[np.argmax(pl < qb)]), qb / 100, -1)); q += 1
    return np.array(out, float).reshape(-1, 4), q

def dia(d):
    """Reconstruye ctx y políticas como E.dia y devuelve, por combinación, la descomposición de cada ejecución."""
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
    ok = np.isfinite(m0) & (bbt > 0) & (bat > bbt); sg = E.D.sigma_causal(t0, m0)
    ev, mxb, mns = {}, np.full(len(t0), -np.inf), np.full(len(t0), np.inf)
    for lado, sel in (("ask", ce), ("bid", ~ce)):
        tl, pl = te[sel] // 1000, np.round(pe[sel] * 100); j = np.searchsorted(t0, tl, side="right") - 1; vv = (j >= 0) & (tl < t0[np.maximum(j, 0)] + 1000)
        j, tl, pl = j[vv], tl[vv], pl[vv]; ini = np.searchsorted(j, np.arange(len(t0))); fin = np.searchsorted(j, np.arange(len(t0)), side="right")
        ev[lado] = {i: (tl[ini[i]:fin[i]], pl[ini[i]:fin[i]]) for i in np.nonzero(fin > ini)[0].tolist()}
        if lado == "ask": np.maximum.at(mxb, j, pl)
        else: np.minimum.at(mns, j, pl)
    ctx = {"m0": m0, "bbt": bbt, "bat": bat, "ok": ok, "mxb": mxb, "mns": mns, "ev": ev, "ts": ts, "mid": mid, "mid_end": mid[np.nonzero(np.isfinite(mid))[0][-1]]}
    POL = E.miope(L, len(t0)); POL.update(E.politicas_ap(L, sg))
    for m in MODS: POL[(m, "HJBx")] = E.pol_exacta(m, L, sg)[:2]
    lam_e3 = {1: L["ask"]["E3-fkX+B"][:, JD], -1: L["bid"]["E3-fkX+B"][:, JD]}
    out = {}
    for m in MODS:
        for p in POLS:
            Da, Db = POL[(m, p)]; QA, QB = E.cotizaciones(Da, Db, ctx); ref = E.simular(Da, Db, QA, QB, ctx)
            F, qf = ejecuciones(QA, QB, ctx); i = F[:, 0].astype(int); tf = F[:, 1].astype(np.int64); pr = F[:, 2]; s = F[:, 3]
            pnl = float(UNIDAD * (s * pr).sum() + qf * ctx["mid_end"] * UNIDAD)
            assert len(F) == ref["n"] and abs(pnl - ref["pnl"]) < 1e-6, f"{d} {m} {p}: no coincide con el simulador"
            cap = s * (pr - m0[i]) / pr * 1e4; mov = {}
            for H in HS:
                k = (tf - ts[0]) // 100 + 10 * H; mh = np.where(k < len(mid), mid[np.minimum(k, len(mid) - 1)], np.nan); mov[H] = s * (m0[i] - mh) / pr * 1e4
            lam = np.where(s > 0, lam_e3[1][i], lam_e3[-1][i])
            out[f"{m}|{p}"] = {"cap": cap.astype(np.float32), **{f"mov{H}": mov[H].astype(np.float32) for H in HS}, "lam_e3": lam.astype(np.float32)}
    return out

def resumen(por_dia):
    dias = list(por_dia); nd = len(dias); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd)); res = {}
    for k in por_dia[dias[0]]:
        cat = {c: np.concatenate([por_dia[d][k][c] for d in dias]).astype(np.float64) for c in por_dia[dias[0]][k]}
        mk10 = cat["cap"] + cat["mov10"]; v = np.isfinite(mk10)
        def ic(col):   # media por ejecución con IC95 por días
            num = np.array([np.nansum(por_dia[d][k][col] if col != "mk10" else por_dia[d][k]["cap"] + por_dia[d][k]["mov10"]) for d in dias])
            den = np.array([np.isfinite(por_dia[d][k][col] if col != "mk10" else por_dia[d][k]["cap"] + por_dia[d][k]["mov10"]).sum() for d in dias], float)
            return [float(num.sum() / den.sum()), *map(float, np.percentile(num[IDX].sum(1) / den[IDX].sum(1), [2.5, 97.5]))]
        r = {"ejecuciones": int(len(mk10)), "ejec_dia": float(len(mk10) / nd), "capturada": ic("cap"), "mov1": ic("mov1"), "mov10": ic("mov10"), "mov60": ic("mov60"),
             "markout10": ic("mk10"), "frac_markout10_pos": float((mk10[v] > 0).mean())}
        if k.startswith("E3-fkX+B|"):
            lam = cat["lam_e3"][v]; cortes = np.quantile(lam, np.linspace(0, 1, 11)); dec = np.clip(np.searchsorted(cortes, lam, side="right") - 1, 0, 9)
            r["deciles_lambda_E3"] = [{"decil": int(j + 1), "markout10": float(mk10[v][dec == j].mean()), "capturada": float(cat["cap"][v][dec == j].mean()),
                                       "mov10": float(cat["mov10"][v][dec == j].mean()), "frac_pos": float((mk10[v][dec == j] > 0).mean())} for j in range(10)]
        res[k] = r
    return res

if __name__ == "__main__":
    t_ini = time.time(); salida = {}
    for nombre, a, b_, sim in (("test", "2026-09-04", "2026-09-20", False), ("simulacion", "2026-09-21", "2026-10-26", True)):
        if sim: T.T0, T.T1, T.guardia_test = date(2026, 9, 21), date(2026, 10, 26), guarda_sim
        por_dia = {}
        for d in T.fechas(a, b_):
            t = time.time(); por_dia[str(d)] = dia(d); log(f"{nombre} {d} ({time.time() - t:.0f} s)")
        salida[nombre] = resumen(por_dia); (SAL / "resultados_v112.json").write_text(json.dumps(salida, indent=1))
    log(f"FIN ({round(time.time() - t_ini)} s)")
