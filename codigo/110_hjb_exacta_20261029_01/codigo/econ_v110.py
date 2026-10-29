#!/usr/bin/env python3
"""v110: test 4–20 sep con los modelos v108: miope, HJB exacta, GLFT (+ HJB aproximada de control). Plan: PLAN_V110.md + ENMIENDA_V110B.md."""
import hashlib, json, math, pickle, sys, time
import numpy as np, pyarrow.parquet as pq
import datos_v110 as D                       # verifica sha de plan, enmienda y modelos v108
import hjb_general as HG
from verif_v110 import exp_local
from datos_v110 import T, W, MOD, MODELOS, FKX, deltas, cols, G, Q, UNIDAD, HS, SAL, R, RR, log
HJB = HG.H49
V = json.loads((SAL / "verificacion_v110.json").read_text()); assert V["todas_ok"], "las verificaciones no pasaron"
pk = SAL / "tablas_v110.pkl"; assert hashlib.sha256(pk.read_bytes()).hexdigest() == V["tablas_sha256"], "tablas modificadas"
TB = pickle.load(open(pk, "rb")); TAB, ID = TB["tablas"], TB["id"]
RG = json.loads((SAL / "rangos_v110.json").read_text()); RANGO_M = RG["m"]; krango = (min(RG["k"][m][0] for m in FKX), max(RG["k"][m][1] for m in FKX))
FIJOS = {"δ fijo 0,5": 0.5, "δ fijo 2": 2.0, "δ fijo 5": 5.0}
# modelos v103 (solo para comparar predicciones)
_p3 = RR / "103_modelos_finales_20261029_01" / "modelos" / "modelos_finales_v103.pkl"
assert hashlib.sha256(_p3.read_bytes()).hexdigest() == json.loads((_p3.parent / "MANIFIESTO_v103.json").read_text())["pkl_sha256"]
MOD103 = pickle.load(open(_p3, "rb"))["MOD"]

# ---------------------------------------------------------------- formas (3 sep) y tablas aproximadas (v49)
d3 = D.dia_entrenamiento(); SH = {m: {l: D.forma_modelo(d3["L"], l, m) for l in ("ask", "bid")} for m in MODELOS}
TAP = {}
def tabla_ap(clave, ka=None, kb=None):
    if clave not in TAP:
        t = time.time()
        if clave == "4d":
            lk = np.linspace(math.log(krango[0]), math.log(krango[1]), 9); TAP[clave] = HJB.Tabla(G, Q, [np.linspace(-7, 4, 37), np.linspace(-5, 5, 21), lk, lk]).construir()
        else: TAP[clave] = HJB.Tabla(G, Q, [np.linspace(-7, 4, 74), np.linspace(-5, 5, 41)], ka, kb).construir()
        log(f"tabla aprox {clave} ({time.time() - t:.0f} s)")
    return TAP[clave]

def pol_exacta(m, L, sg):
    sa, sb = SH[m]["ask"], SH[m]["bid"]; La0, Lb0 = L["ask"][m][:, 0], L["bid"][m][:, 0]
    X = [2 * np.log(sg) - La0, Lb0 - La0]; info = {}
    if m in FKX:
        ma = (L["ask"][m][:, -1] - La0) / sa["f"][-1]; mb = (L["bid"][m][:, -1] - Lb0) / sb["f"][-1]; X += [ma, mb]
        Fa, Fb = HG.forma_por_fila(sa["f"], ma, deltas), HG.forma_por_fila(sb["f"], mb, deltas)
        ra, rb = RANGO_M[f"{m}|ask"], RANGO_M[f"{m}|bid"]
        info = {"frac_m_ask_fuera": float(((ma < ra[0]) | (ma > ra[1])).mean()), "frac_m_bid_fuera": float(((mb < rb[0]) | (mb > rb[1])).mean()),
                "frac_seg_k_corregido": float(((Fa["nflag"] > 0) | (Fb["nflag"] > 0)).mean()),
                "err_repr_m_f": float(max(np.abs(L["ask"][m] - La0[:, None] - ma[:, None] * sa["f"][None]).max(), np.abs(L["bid"][m] - Lb0[:, None] - mb[:, None] * sb["f"][None]).max()))}
    else:
        Fa, Fb = HG.forma(sa["g"], deltas), HG.forma(sb["g"], deltas)
        info = {"dev_forma_vs_3sep": float(max(np.abs(L["ask"][m] - La0[:, None] - sa["g"][None]).max(), np.abs(L["bid"][m] - Lb0[:, None] - sb["g"][None]).max()))}
    Da, Db, rec = TAB[ID[m]].deltas_exactos(np.column_stack(X), Fa, Fb); info["frac_tabla_recortada"] = rec
    return Da, Db, info

def politicas_ap(L, sg):
    out = {}
    for m in MODELOS:
        la, ka = exp_local(L["ask"][m]); lb, kb = exp_local(L["bid"][m]); Aa, Ab = np.exp(la), np.exp(lb)
        var_k = np.ptp(ka) > 1e-6 or np.ptp(kb) > 1e-6
        if var_k:
            ka, kb = np.clip(ka, *krango), np.clip(kb, *krango)
            Da, Db, r = tabla_ap("4d").deltas(np.column_stack([np.log(sg ** 2 / Aa), np.log(Ab / Aa), np.log(ka), np.log(kb)]), ka, kb)
        else:
            ka, kb = float(ka[0]), float(kb[0]); Da, Db, r = tabla_ap(("2d", round(ka, 6), round(kb, 6)), ka, kb).deltas(np.column_stack([np.log(sg ** 2 / Aa), np.log(Ab / Aa)]), ka, kb)
        qs = np.arange(-Q, Q + 1)
        ga, gb = HJB.glft(qs[None, :], G, np.reshape(ka, (-1, 1)), np.reshape(kb, (-1, 1)), Aa[:, None], Ab[:, None], sg[:, None])
        ga, gb = np.array(ga, float), np.array(gb, float); ga[:, 0] = np.nan; gb[:, -1] = np.nan
        out[(m, "HJBa")], out[(m, "GLFT")] = (Da, Db), (ga, gb)
    return out

def miope(L, n):
    out = {}
    for m in MODELOS + list(FIJOS):
        d = {}
        for lado in ("ask", "bid"):
            d[lado] = deltas[np.argmax(np.exp(L[lado][m]) * deltas[None, :], 1)] if m in MODELOS else np.full(n, FIJOS[m])
        Da, Db = np.repeat(d["ask"][:, None], 2 * Q + 1, 1).astype(float), np.repeat(d["bid"][:, None], 2 * Q + 1, 1).astype(float); Da[:, 0] = np.nan; Db[:, -1] = np.nan
        out[(m, "MIOPE")] = (Da, Db)
    return out

# ---------------------------------------------------------------- simulador (copia de v106 con cotizaciones separadas)
def cotizaciones(Da, Db, ctx):
    m0, bbt, bat = ctx["m0"], ctx["bbt"], ctx["bat"]
    QA = np.maximum(np.ceil(np.nan_to_num(m0[:, None] * (1 + Da / 1e4) * 100, nan=9e15) - 1e-6), bbt[:, None] + 1)
    QB = np.minimum(np.floor(np.nan_to_num(m0[:, None] * (1 - Db / 1e4) * 100, nan=-9e15) + 1e-6), bat[:, None] - 1)
    QA[np.isnan(Da)] = np.inf; QB[np.isnan(Db)] = -np.inf
    return QA, QB

def simular(Da, Db, QA, QB, ctx):
    m0, ok, mxb, mns, ev, ts, mid, mid_end = (ctx[k] for k in ("m0", "ok", "mxb", "mns", "ev", "ts", "mid", "mid_end"))
    cand = np.nonzero(ok & ((mxb > QA.min(1)) | (mns < QB.max(1))))[0].tolist()
    mxb_l, mns_l = mxb.tolist(), mns.tolist()
    q, caja, F, absq, ult = 0, 0.0, [], 0.0, 0
    for i in cand:
        absq += abs(q) * (i - ult); ult = i
        qa, qb = QA[i, q + Q], QB[i, q + Q]
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
    dqa = np.median((QA[ok, Q] / 100 / m0[ok] - 1) * 1e4); dqb = np.median(-(QB[ok, Q] / 100 / m0[ok] - 1) * 1e4)
    return {"n": n, "pnl": float(pnl), "nocional": float((F[:, 1] * UNIDAD).sum()), "s10": float(np.nansum(mk[0])), "n10": int(np.isfinite(mk[0]).sum()),
            "s60": float(np.nansum(mk[1])), "n60": int(np.isfinite(mk[1]).sum()), "q_abs_medio": absq / len(m0), "q_fin": q,
            "da0_med": float(np.nanmedian(Da[ok, Q])), "db0_med": float(np.nanmedian(Db[ok, Q])), "dq_ask_med": float(dqa), "dq_bid_med": float(dqb)}

PRED = {(m, l): [] for m in FKX for l in ("ask", "bid")}
def dia(d):
    b = T.dia_test(d, deltas, MOD); t0 = np.asarray(b["t_ms"], np.int64)
    trd = pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    te, pe, ce = T.eventos_agresor(trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    b["lam1"] = T.M.lambda_bins(MOD["H1"], {"fecha": d, "t_ms": t0, "T_us": te.astype(np.int64), "tipo": np.where(ce, 0, 1).astype(np.int8)})
    L = {l: W.lls(MOD, b, l, cols, deltas) for l in ("ask", "bid")}
    L3 = {l: W.lls(MOD103, b, l, cols, deltas) for l in ("ask", "bid")}
    for m in FKX:
        for l in ("ask", "bid"): PRED[(m, l)].append((L[l][m] - L3[l][m]).astype(np.float32))
    T.guardia_test(d); fe = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "best_bid", "best_ask", "mid"])
    ts = fe["ts_ms"].to_numpy(); sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool)
    mid = np.where(sv, fe["mid"].to_numpy(zero_copy_only=False).astype(float), np.nan)
    r0 = ((t0 - ts[0]) // 100).astype(np.int64); m0 = mid[r0]
    bbt = np.round(np.nan_to_num(fe["best_bid"].to_numpy(zero_copy_only=False).astype(float)[r0]) * 100); bat = np.round(np.nan_to_num(fe["best_ask"].to_numpy(zero_copy_only=False).astype(float)[r0]) * 100)
    ok = np.isfinite(m0) & (bbt > 0) & (bat > bbt)
    sg = D.sigma_causal(t0, m0)
    ev, mxb, mns = {}, np.full(len(t0), -np.inf), np.full(len(t0), np.inf)
    for lado, sel in (("ask", ce), ("bid", ~ce)):
        tl, pl = te[sel] // 1000, np.round(pe[sel] * 100); j = np.searchsorted(t0, tl, side="right") - 1; vv = (j >= 0) & (tl < t0[np.maximum(j, 0)] + 1000)
        j, tl, pl = j[vv], tl[vv], pl[vv]; ini = np.searchsorted(j, np.arange(len(t0))); fin = np.searchsorted(j, np.arange(len(t0)), side="right")
        ev[lado] = {i: (tl[ini[i]:fin[i]], pl[ini[i]:fin[i]]) for i in np.nonzero(fin > ini)[0].tolist()}
        if lado == "ask": np.maximum.at(mxb, j, pl)
        else: np.minimum.at(mns, j, pl)
    ctx = {"m0": m0, "bbt": bbt, "bat": bat, "ok": ok, "mxb": mxb, "mns": mns, "ev": ev, "ts": ts, "mid": mid, "mid_end": mid[np.nonzero(np.isfinite(mid))[0][-1]]}
    POL = miope(L, len(t0)); POL.update(politicas_ap(L, sg)); infos = {}
    for m in MODELOS:
        Da, Db, infos[m] = pol_exacta(m, L, sg); POL[(m, "HJBx")] = (Da, Db)
        w = ok[:, None]; na = np.isfinite(Da) & w; nb = np.isfinite(Db) & w
        infos[m]["frac_delta_en_borde_dominio"] = float((np.sum(na & ((Da <= -5 + 1e-9) | (Da >= 40 - 1e-9))) + np.sum(nb & ((Db <= -5 + 1e-9) | (Db >= 40 - 1e-9)))) / (na.sum() + nb.sum()))
    res, QS = {}, {}
    for (m, p), (Da, Db) in POL.items():
        QA, QB = cotizaciones(Da, Db, ctx); QS[(m, p)] = (QA, QB); res[f"{m}|{p}"] = simular(Da, Db, QA, QB, ctx)
    cmp_ = {}
    for m in MODELOS:   # precio cotizado distinto tras redondear al tick: exacta vs aproximada
        (Ax, Bx), (Aa, Ba) = QS[(m, "HJBx")], QS[(m, "HJBa")]
        da, db = np.isfinite(Ax) & np.isfinite(Aa) & ok[:, None], np.isfinite(Bx) & np.isfinite(Ba) & ok[:, None]
        dif_a, dif_b = (Ax != Aa) & da, (Bx != Ba) & db
        cmp_[m] = {"n_dec": int(da.sum() + db.sum()), "n_dif": int(dif_a.sum() + dif_b.sum()), "n_dec_q0": int(da[:, Q].sum() + db[:, Q].sum()), "n_dif_q0": int(dif_a[:, Q].sum() + dif_b[:, Q].sum())}
    res["_info"] = infos; res["_cmp"] = cmp_; res["_sigma_med"] = float(np.median(sg))
    return res

def fm(x): return f"{x[0]:+.2f} [{x[1]:+.2f}; {x[2]:+.2f}]"
if __name__ == "__main__":
    t_ini = time.time(); por_dia = {}
    for d in T.fechas("2026-09-04", "2026-09-20"):
        t = time.time(); r = por_dia[str(d)] = dia(d)
        log(f"{d} ({time.time() - t:.0f} s): " + " | ".join(f"{k}: {r[k]['n']} ej, {1e4 * r[k]['pnl'] / max(r[k]['nocional'], 1e-9):+.2f} bps" for k in ("E3-fkX+B|HJBx", "E3-fkX+B|HJBa", "E1|HJBx", "E1|MIOPE")), "log_econ_v110.txt")
        (SAL / "por_dia_v110.json").write_text(json.dumps(por_dia, indent=1))
    dias = list(por_dia); nd = len(dias); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd))
    S = lambda k, c: np.array([por_dia[d][k][c] for d in dias], float)
    def ficha(k, ref):
        pa, pn = 1e4 * S(k, "pnl"), S(k, "nocional"); bps = pa.sum() / pn.sum(); ic = np.percentile(pa[IDX].sum(1) / pn[IDX].sum(1), [2.5, 97.5])
        out = {"ejec_dia": float(S(k, "n").mean()), "q_abs": float(S(k, "q_abs_medio").mean()), "pnl_usdt_dia": float(S(k, "pnl").mean()), "dias_pos": int((S(k, "pnl") > 0).sum()), "bps": [float(bps), *map(float, ic)],
               "da0": float(S(k, "da0_med").mean()), "dq_ask": float(S(k, "dq_ask_med").mean()), "dq_bid": float(S(k, "dq_bid_med").mean())}
        for H, (s, n_) in {"mk10": ("s10", "n10"), "mk60": ("s60", "n60")}.items():
            num, den = S(k, s), S(k, n_); out[H] = [float(num.sum() / den.sum()), *map(float, np.percentile(num[IDX].sum(1) / den[IDX].sum(1), [2.5, 97.5]))]
        ra, rn = 1e4 * S(ref, "pnl"), S(ref, "nocional"); dif = ra[IDX].sum(1) / rn[IDX].sum(1) - pa[IDX].sum(1) / pn[IDX].sum(1)
        out["dif_E3"] = [float(ra.sum() / rn.sum() - bps), *map(float, np.percentile(dif, [2.5, 97.5]))]
        return out
    filas, lin = [], ["### PnL con la política HJB exacta y GLFT en el test (4–20 sep, 17 días; γ = 0,01, Q = 10; 0,01 BTC por orden; bruto, sin comisiones; modelos v108)", "",
                      "| Modelo | Política | δ_a en q=0 (bps, mediana) | Ejec./día | \\|q\\| medio | PnL/día (USDT) | Días > 0 | PnL por ejec. (bps) [IC95] | Markout 10 s (bps) | E3 tesis − modelo (bps/ejec.) [IC95] |", "|---|---|---|---|---|---|---|---|---|---|"]
    NOMP = {"HJBx": "HJB exacta", "GLFT": "GLFT", "HJBa": "HJB aprox. (exp. local, v108)", "MIOPE": "Miope"}
    for pol in ("HJBx", "GLFT", "HJBa"):
        for m in MODELOS:
            f = ficha(f"{m}|{pol}", f"E3-fkX+B|{pol}"); f.update(modelo=m, politica=NOMP[pol]); filas.append(f)
            lin.append(f"| {m} | {NOMP[pol]} | {f['da0']:.2f} | {f['ejec_dia']:.0f} | {f['q_abs']:.1f} | {f['pnl_usdt_dia']:+.1f} | {f['dias_pos']}/17 | {fm(f['bps'])} | {f['mk10'][0]:+.2f} | "
                       + ("—" if m == "E3-fkX+B" else f"{f['dif_E3'][0]:+.3f} [{f['dif_E3'][1]:+.3f}; {f['dif_E3'][2]:+.3f}]") + " |")
    lin += ["", "HJB exacta: curva log λ̂(δ) lineal a trozos en los 9 nodos, dominio δ ∈ [−5; 40] bps, k_s ≥ 0,01. HJB aprox.: exponencial local de v106 (control). Comisión maker no incluida."]
    (SAL / "resumen_v110.json").write_text(json.dumps({"politicas": filas}, indent=1)); (R / "tablas_tesis" / "T7_hjb_test.md").write_text("\n".join(lin) + "\n")
    # T6 (miope)
    f6, l6 = [], ["### PnL de market making en el test (4–20 sep, 17 días; AS miope δ* = argmax λ̂(δ)·δ; modelos v108; 0,01 BTC por orden; |q| ≤ 10; bruto, sin comisiones)", "",
                  "| Política | δ mediana (bps) | Ejec./día | PnL/día (USDT) | Días > 0 | PnL por ejec. (bps) [IC95] | Markout 10 s (bps) [IC95] | Markout 60 s (bps) [IC95] |", "|---|---|---|---|---|---|---|---|"]
    for m in MODELOS + list(FIJOS):
        f = ficha(f"{m}|MIOPE", "E3-fkX+B|MIOPE"); f["politica"] = m; f6.append(f)
        l6.append(f"| {m} | {f['dq_ask']:.2f} | {f['ejec_dia']:.0f} | {f['pnl_usdt_dia']:+.2f} | {f['dias_pos']}/17 | {fm(f['bps'])} | {fm(f['mk10'])} | {fm(f['mk60'])} |")
    l6 += ["", "Comisión maker Binance spot: 10 bps (VIP0) o 7,5 bps (con BNB) por ejecución; el PnL neto = bruto − comisión."]
    (R / "tablas_tesis" / "T6_pnl_test.md").write_text("\n".join(l6) + "\n")
    # exacta vs aproximada
    cmpf = {}
    for m in MODELOS:
        kx, ka = f"{m}|HJBx", f"{m}|HJBa"; px, pa_ = 1e4 * S(kx, "pnl"), 1e4 * S(ka, "pnl"); nx, na_ = S(kx, "nocional"), S(ka, "nocional")
        c = {"pct_dec_dif": 100 * sum(por_dia[d]["_cmp"][m]["n_dif"] for d in dias) / sum(por_dia[d]["_cmp"][m]["n_dec"] for d in dias),
             "pct_dec_dif_q0": 100 * sum(por_dia[d]["_cmp"][m]["n_dif_q0"] for d in dias) / sum(por_dia[d]["_cmp"][m]["n_dec_q0"] for d in dias)}
        for nom, c_ in (("ejec_dia", "n"), ("q_abs", "q_abs_medio")):
            dd = S(kx, c_) - S(ka, c_); c[nom] = {"exacta": float(S(kx, c_).mean()), "aprox": float(S(ka, c_).mean()), "dif": [float(dd.mean()), *map(float, np.percentile(dd[IDX].mean(1), [2.5, 97.5]))]}
        dg = px[IDX].sum(1) / nx[IDX].sum(1) - pa_[IDX].sum(1) / na_[IDX].sum(1)
        c["bps_bruto"] = {"exacta": float(px.sum() / nx.sum()), "aprox": float(pa_.sum() / na_.sum()), "dif": [float(px.sum() / nx.sum() - pa_.sum() / na_.sum()), *map(float, np.percentile(dg, [2.5, 97.5]))]}
        for com in (7.5, 10.0):
            c[f"bps_neto_{com}"] = {"exacta": c["bps_bruto"]["exacta"] - com, "aprox": c["bps_bruto"]["aprox"] - com, "dif": c["bps_bruto"]["dif"]}   # comisión constante por ejecución: la diferencia por ejecución es la bruta
            ux, ua = S(kx, "pnl") - com * 1e-4 * nx, S(ka, "pnl") - com * 1e-4 * na_; dd = ux - ua
            c[f"usdt_dia_neto_{com}"] = {"exacta": float(ux.mean()), "aprox": float(ua.mean()), "dif": [float(dd.mean()), *map(float, np.percentile(dd[IDX].mean(1), [2.5, 97.5]))]}
        cmpf[m] = c
    # predicciones v103 vs v108
    pred = {}
    for m in FKX:
        for l in ("ask", "bid"):
            A = np.abs(np.vstack(PRED[(m, l)]).astype(np.float64)); r = {}
            for j, dl in enumerate(deltas): r[f"{dl:g}"] = {"max": float(A[:, j].max()), "p99": float(np.percentile(A[:, j], 99))}
            lo, hi = A[:, deltas <= 5], A[:, deltas >= 15]
            r["delta<=5"] = {"max": float(lo.max()), "p99": float(np.percentile(lo, 99))}; r["delta>=15"] = {"max": float(hi.max()), "p99": float(np.percentile(hi, 99))}
            pred[f"{m}|{l}"] = r
    # controles de reproducción frente a v105 / v106 (modelos idénticos a v103: los 9 sin E3-fkX)
    ctrl = {"miope_vs_v105": {}, "GLFT_vs_v106": {}, "HJBa_vs_v106": {}}
    p5 = json.loads((RR / "105_pnl_test_20261029_01" / "salida" / "por_dia_v105.json").read_text()); p6 = json.loads((RR / "106_hjb_test_20261029_01" / "salida" / "por_dia_v106.json").read_text())
    for m in MODELOS + list(FIJOS):
        if m in FKX: continue
        ctrl["miope_vs_v105"][m] = {"max_dif_n_dia": max(abs(por_dia[d][f"{m}|MIOPE"]["n"] - p5[d][m]["n"]) for d in dias), "max_dif_pnl_dia": max(abs(por_dia[d][f"{m}|MIOPE"]["pnl"] - p5[d][m]["pnl"]) for d in dias)}
        if m in FIJOS: continue
        for pol, pn in (("GLFT", "GLFT"), ("HJBa", "HJB")):
            ctrl[f"{pol}_vs_v106"][m] = {"max_dif_n_dia": max(abs(por_dia[d][f"{m}|{pol}"]["n"] - p6[d][f"{m}|{pn}"]["n"]) for d in dias), "max_dif_pnl_dia": max(abs(por_dia[d][f"{m}|{pol}"]["pnl"] - p6[d][f"{m}|{pn}"]["pnl"]) for d in dias)}
    info = {m: {k: float(np.mean([por_dia[d]["_info"][m][k] for d in dias])) for k in por_dia[dias[0]]["_info"][m]} for m in MODELOS}
    info_max = {m: {k: float(np.max([por_dia[d]["_info"][m][k] for d in dias])) for k in por_dia[dias[0]]["_info"][m]} for m in MODELOS}
    (SAL / "resumen_v110.json").write_text(json.dumps({"politicas": filas, "miope": f6, "exacta_vs_aprox": cmpf, "pred_v103_vs_v108": pred, "controles": ctrl, "info_media_dias": info, "info_max_dias": info_max, "segundos": round(time.time() - t_ini)}, indent=1))
    log("FIN " + str(round(time.time() - t_ini)) + " s", "log_econ_v110.txt")
