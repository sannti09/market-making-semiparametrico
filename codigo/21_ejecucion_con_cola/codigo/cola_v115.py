#!/usr/bin/env python3
"""v115: ejecución con cola aproximada sobre las cotizaciones congeladas de v110 (R0 cruce estricto, R1 toque sin cola, R2 FIFO con cola imputada).
Plan: PLAN_V115.md. Reutiliza econ_v110.dia sin editarlo: solo sustituye la función de ejecución. Uso: python cola_v115.py test|sim"""
import hashlib, json, sys, time
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"; SAL.mkdir(parents=True, exist_ok=True)
assert hashlib.sha256((R / "PLAN_V115.md").read_bytes()).hexdigest() == (R / "PLAN_V115.sha256").read_text().split()[0], "PLAN_V115 modificado"
sys.path.insert(0, str(RR / "19_simulacion" / "codigo"))
import sim_v111 as S11  # noqa: E402  (importa econ_v110: verifica planes v110/v111, modelos v108 y tablas; no ejecuta nada)
E = S11.E; T = E.T; Q, UNIDAD, HS = E.Q, E.UNIDAD, E.HS
REGLAS = ("R0", "R1", "R2"); LOG = []
def log(m, f=None):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / f"log_v115_{PERIODO}.txt").write_text("\n".join(LOG))
E.log = log; T.SAL = SAL   # que nada escriba en las salidas de v110/v111/v101

# ---------------------------------------------------------------- datos del día: transacciones con cantidad y libro visible al inicio de cada segundo
DIA = {}
_dia_test = T.dia_test
def dia_test(d, deltas, MOD):
    b = _dia_test(d, deltas, MOD); DIA.clear(); DIA["d"], DIA["t0"] = d, np.asarray(b["t_ms"], np.int64); return b
T.dia_test = dia_test

def preparar():
    d, t0 = DIA["d"], DIA["t0"]; n = len(t0)
    tr = pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "qty", "aggressor_buy"])
    tl_all, pl_all = tr["event_time_us"].to_numpy() // 1000, np.round(tr["price"].to_numpy() * 100); ql_all = tr["qty"].to_numpy().astype(float)
    compra = tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool)
    for lado, sel in (("ask", compra), ("bid", ~compra)):
        tl, pl, ql = tl_all[sel], pl_all[sel], ql_all[sel]
        j = np.searchsorted(t0, tl, side="right") - 1; vv = (j >= 0) & (tl < t0[np.maximum(j, 0)] + 1000)
        j, tl, pl, ql = j[vv], tl[vv], pl[vv], ql[vv]
        ext = np.full(n, -np.inf if lado == "ask" else np.inf)
        (np.maximum if lado == "ask" else np.minimum).at(ext, j, pl)
        DIA[lado] = {"ini": np.searchsorted(j, np.arange(n)), "fin": np.searchsorted(j, np.arange(n), side="right"), "tl": tl, "pl": pl, "ql": ql, "ext": ext}
    cols = ["ts_ms"] + [f"{l}_{c}_{k:02d}" for l in ("ask", "bid") for c in ("px", "qty") for k in range(1, 21)]
    fe = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=cols)
    ts = fe["ts_ms"].to_numpy(); r0 = ((t0 - ts[0]) // 100).astype(np.int64)
    for lado in ("ask", "bid"):
        px = np.column_stack([fe[f"{lado}_px_{k:02d}"].to_numpy(zero_copy_only=False).astype(float)[r0] for k in range(1, 21)])
        qt = np.column_stack([fe[f"{lado}_qty_{k:02d}"].to_numpy(zero_copy_only=False).astype(float)[r0] for k in range(1, 21)])
        DIA[lado].update(px=np.round(px * 100), qt=qt, med=np.nanmedian(np.where(np.isfinite(px), qt, np.nan), 1))
    DIA["listo"] = True

def q_delante(lado, i, p):
    """Cantidad (BTC) delante de la orden en el precio p (ticks) al inicio del segundo i. Visible si p está dentro de los 20 niveles; si no, mediana de los 20."""
    X = DIA[lado]; px, qt = X["px"][i], X["qt"][i]; ult = px[-1]
    visible = np.isfinite(ult) and (p <= ult if lado == "ask" else p >= ult)
    if visible:
        k = np.nonzero(px == p)[0]; return float(qt[k[0]]) if len(k) else 0.0, True
    m = X["med"][i]; return (float(m) if np.isfinite(m) else np.inf), False

def ejecuta(lado, i, p, regla, cuenta):
    """Instante (ms) de la ejecución de la orden de precio p en el segundo i, o None."""
    X = DIA[lado]; a, b = X["ini"][i], X["fin"][i]
    if a == b or not np.isfinite(p): return None
    tl, pl, ql = X["tl"][a:b], X["pl"][a:b], X["ql"][a:b]; s = 1 if lado == "ask" else -1
    mas = s * (pl - p) > 0; al = pl == p
    if regla == "R0": ok = mas
    elif regla == "R1": ok = mas | al
    else:
        ok = mas.copy()
        if al.any():
            qd, vis = q_delante(lado, i, p); cuenta["at"] += 1; cuenta["vis"] += vis
            alc = np.cumsum(np.where(al, ql, 0.0)) >= qd + UNIDAD - 1e-12; ok |= alc; cuenta["at_ok"] += bool(alc.any() and not mas.any())
    if not ok.any(): return None
    return int(tl[np.argmax(ok)])

def simular_regla(Da, Db, QA, QB, ctx, regla):
    """Copia de econ_v110.simular con la condición de ejecución de la regla (mismas cotizaciones, inventario y métricas)."""
    m0, ok, ts, mid, mid_end = (ctx[k] for k in ("m0", "ok", "ts", "mid", "mid_end"))
    ea, eb = DIA["ask"]["ext"], DIA["bid"]["ext"]
    cand = np.nonzero(ok & (((ea > QA.min(1)) | (eb < QB.max(1))) if regla == "R0" else ((ea >= QA.min(1)) | (eb <= QB.max(1)))))[0].tolist()
    q, caja, F, absq, ult = 0, 0.0, [], 0.0, 0; cuenta = {"at": 0, "vis": 0, "at_ok": 0}
    for i in cand:
        absq += abs(q) * (i - ult); ult = i
        qa, qb = QA[i, q + Q], QB[i, q + Q]
        t = ejecuta("ask", i, qa, regla, cuenta)
        if t is not None: F.append((t, qa / 100, 1)); q -= 1; caja += qa / 100 * UNIDAD
        t = ejecuta("bid", i, qb, regla, cuenta)
        if t is not None: F.append((t, qb / 100, -1)); q += 1; caja -= qb / 100 * UNIDAD
    absq += abs(q) * (len(m0) - ult)
    F = np.array(F, float).reshape(-1, 3); n = len(F); pnl = caja + q * mid_end * UNIDAD
    mk = []
    for H in HS:
        k = (F[:, 0].astype(np.int64) - ts[0]) // 100 + 10 * H; mh = np.where(k < len(mid), mid[np.minimum(k, len(mid) - 1)], np.nan)
        mk.append(F[:, 2] * (F[:, 1] - mh) / F[:, 1] * 1e4)
    return {"n": n, "pnl": float(pnl), "nocional": float((F[:, 1] * UNIDAD).sum()), "s10": float(np.nansum(mk[0])), "n10": int(np.isfinite(mk[0]).sum()),
            "s60": float(np.nansum(mk[1])), "n60": int(np.isfinite(mk[1]).sum()), "q_abs_medio": absq / len(m0), "q_fin": q,
            "da0_med": float(np.nanmedian(Da[ok, Q])), "segundos_al_precio": cuenta["at"], "frac_cola_visible": cuenta["vis"] / max(cuenta["at"], 1),
            "ejec_solo_al_precio": cuenta["at_ok"]}

_simular = E.simular
def simular(Da, Db, QA, QB, ctx):
    if not DIA.get("listo"): preparar()
    out = dict(_simular(Da, Db, QA, QB, ctx))   # original de v110 (control)
    for rg in REGLAS: out[rg] = simular_regla(Da, Db, QA, QB, ctx, rg)
    return out
E.simular = simular

# ---------------------------------------------------------------- resumen
def ficha(por_dia, k, rg, ref, IDX):
    dias = list(por_dia); S = lambda kk, c, r=rg: np.array([por_dia[d][kk][r][c] for d in dias], float)
    pa, pn = 1e4 * S(k, "pnl"), S(k, "nocional"); bps = pa.sum() / pn.sum(); ic = np.percentile(pa[IDX].sum(1) / pn[IDX].sum(1), [2.5, 97.5])
    out = {"ejec_dia": float(S(k, "n").mean()), "q_abs": float(S(k, "q_abs_medio").mean()), "pnl_usdt_dia": float(S(k, "pnl").mean()), "dias_pos": int((S(k, "pnl") > 0).sum()),
           "bps": [float(bps), *map(float, ic)], "frac_cola_visible": float(S(k, "frac_cola_visible").mean())}
    for H, (s, n_) in {"mk10": ("s10", "n10"), "mk60": ("s60", "n60")}.items():
        num, den = S(k, s), S(k, n_); out[H] = [float(num.sum() / den.sum()), *map(float, np.percentile(num[IDX].sum(1) / den[IDX].sum(1), [2.5, 97.5]))]
    ra, rn = 1e4 * S(ref, "pnl"), S(ref, "nocional"); dif = ra[IDX].sum(1) / rn[IDX].sum(1) - pa[IDX].sum(1) / pn[IDX].sum(1)
    out["dif_E3"] = [float(ra.sum() / rn.sum() - bps), *map(float, np.percentile(dif, [2.5, 97.5]))]
    p0, n0 = 1e4 * S(k, "pnl", "R0"), S(k, "nocional", "R0"); dr = pa[IDX].sum(1) / pn[IDX].sum(1) - p0[IDX].sum(1) / n0[IDX].sum(1)
    out["dif_vs_R0"] = [float(bps - p0.sum() / n0.sum()), *map(float, np.percentile(dr, [2.5, 97.5]))]
    return out

POLS = {"HJBx": "HJB exacta", "GLFT": "GLFT", "MIOPE": "Miope", "HJBa": "HJB aprox."}
AS_HAWKES = ["E1", "E1+h-f", "E1+S", "E2+h-f", "E2+S", "E2m+h-f", "E2m+S"]
def resumir(por_dia, nombre):
    dias = list(por_dia); nd = len(dias); IDX = np.random.default_rng(20261030).integers(0, nd, size=(2000, nd)); res = {}
    lin = [f"### Ejecución con cola aproximada, {nombre} ({nd} días; bruto, sin comisiones; modelos v108 y políticas de v110 congelados)", "",
           "R0 = cruce estricto (tesis); R1 = toque sin cola (cota optimista); R2 = cola FIFO, cola delante visible o imputada (mediana de los 20 niveles).", "",
           "| Política | Modelo | Regla | Ejec./día | \\|q\\| medio | PnL/día (USDT) | Días > 0 | PnL por ejec. (bps) [IC95] | Cambio vs R0 (bps) [IC95] | Markout 10 s | Markout 60 s | E3 tesis − modelo [IC95] |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pol in POLS:
        for m in E.MODELOS + (list(E.FIJOS) if pol == "MIOPE" else []):
            for rg in REGLAS:
                f = ficha(por_dia, f"{m}|{pol}", rg, f"E3-fkX+B|{pol}", IDX); res[f"{m}|{pol}|{rg}"] = f
                if pol == "HJBa": continue
                lin.append(f"| {POLS[pol]} | {m} | {rg} | {f['ejec_dia']:.0f} | {f['q_abs']:.1f} | {f['pnl_usdt_dia']:+.2f} | {f['dias_pos']}/{nd} | {f['bps'][0]:+.2f} [{f['bps'][1]:+.2f}; {f['bps'][2]:+.2f}] | "
                           + ("—" if rg == "R0" else f"{f['dif_vs_R0'][0]:+.2f} [{f['dif_vs_R0'][1]:+.2f}; {f['dif_vs_R0'][2]:+.2f}]") + f" | {f['mk10'][0]:+.2f} | {f['mk60'][0]:+.2f} | "
                           + ("—" if m == "E3-fkX+B" else f"{f['dif_E3'][0]:+.3f} [{f['dif_E3'][1]:+.3f}; {f['dif_E3'][2]:+.3f}]") + " |")
    lect = {}
    for rg in REGLAS:
        claves = [k for k in res if k.endswith("|" + rg) and k.split("|")[1] in ("HJBx", "GLFT", "MIOPE")]
        lect[rg] = {"conclusion_economica_se_mantiene": all(res[k]["bps"][2] < 0 for k in claves), "max_ic_sup_bps": max(res[k]["bps"][2] for k in claves),
                    "E3_gana_HJBx": all(res[f"{m}|HJBx|{rg}"]["dif_E3"][1] > 0 for m in AS_HAWKES)}
        if rg != "R0": lect[rg]["max_abs_cambio_vs_R0_HJBx"] = max(abs(res[f"{m}|HJBx|{rg}"]["dif_vs_R0"][0]) for m in E.MODELOS)
    lect["poco_sensible_a_la_cola"] = all(lect[rg]["max_abs_cambio_vs_R0_HJBx"] < 0.2 for rg in ("R1", "R2"))
    lin += ["", "Lectura fijada en el plan: " + json.dumps(lect, ensure_ascii=False)]
    (SAL / f"resumen_v115_{nombre}.json").write_text(json.dumps({"fichas": res, "lectura": lect}, indent=1)); (SAL / f"tabla_v115_{nombre}.md").write_text("\n".join(lin) + "\n")
    return lect

PERIODO = sys.argv[1] if len(sys.argv) > 1 else "test"
if __name__ == "__main__":
    assert PERIODO in ("test", "sim")
    if PERIODO == "test":
        fechas, ref = T.fechas("2026-09-04", "2026-09-20"), json.loads((RR / "18_hjb_curva_interpolada" / "salida" / "por_dia_v110.json").read_text())
    else:
        T.T0, T.T1, T.guardia_test = date(2026, 9, 21), date(2026, 10, 26), S11.guarda_sim   # el mismo cambio de guarda que v111
        fechas, ref = T.fechas("2026-09-21", "2026-10-26"), json.loads((RR / "19_simulacion" / "salida" / "por_dia_econ_v111.json").read_text())
    t_ini = time.time(); por_dia = {}
    for d in fechas:
        t = time.time(); r = E.dia(d)
        for k in E.PRED: E.PRED[k].clear()
        claves = [k for k in r if not k.startswith("_")]
        c_ref = max(max(abs(r[k]["n"] - ref[str(d)][k]["n"]), abs(r[k]["pnl"] - ref[str(d)][k]["pnl"])) for k in claves)
        c_r0 = max(max(abs(r[k]["R0"]["n"] - r[k]["n"]), abs(r[k]["R0"]["pnl"] - r[k]["pnl"])) for k in claves)
        if c_ref > 1e-9 or c_r0 > 1e-9:
            log(f"CONTROL FALLIDO {d}: v110/v111 dif {c_ref:.2e}; R0 vs original dif {c_r0:.2e}"); sys.exit(1)
        por_dia[str(d)] = {k: {rg: r[k][rg] for rg in REGLAS} for k in claves}
        k = "E3-fkX+B|HJBx"; x = por_dia[str(d)][k]
        log(f"{d} ({time.time() - t:.0f} s) control ok | HJB E3: " + " | ".join(f"{rg} {x[rg]['n']} ej {1e4 * x[rg]['pnl'] / max(x[rg]['nocional'], 1e-9):+.2f} bps" for rg in REGLAS))
        (SAL / f"por_dia_v115_{PERIODO}.json").write_text(json.dumps(por_dia))
    lect = resumir(por_dia, PERIODO); log(f"lectura: {json.dumps(lect, ensure_ascii=False)}"); log(f"FIN ({time.time() - t_ini:.0f} s)")
