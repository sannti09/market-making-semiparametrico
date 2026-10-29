#!/usr/bin/env python3
"""v111: simulación 21 sep–26 oct con los modelos finales congelados (v108) y la política de v110. Ver PLAN_V111.md.
Reutiliza sin cambios las funciones de v110 (economía) y la evaluación diaria de v109 (predicción); solo cambia el guarda de fechas."""
import hashlib, json, sys, time
from datetime import date
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V111.md").read_bytes()).hexdigest() == (R / "PLAN_V111.sha256").read_text().split()[0], "PLAN_V111 modificado"
sys.path.insert(0, str(RR / "18_hjb_curva_interpolada" / "codigo"))
import econ_v110 as E  # noqa: E402  (verifica plan v110, modelos v108 y tablas; no ejecuta el test al importarse)
T, W, MOD, deltas, cols, MODELOS, FKX = E.T, E.W, E.MOD, E.deltas, E.cols, E.MODELOS, E.FKX
T.SAL = SAL
NOMS = ["E3-fkX+B", "E3", "E3-fkX", "E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S", "E1", "E2+h-f", "E2+S"]
JD = int(np.where(deltas == 2.0)[0][0]); LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "sim_v111.log").write_text("\n".join(LOG))

def pred_dia(d):
    """Evaluación predictiva de un día (idéntica a test_v109.fase_B)."""
    b = T.dia_test(d, deltas, MOD)
    trd = T.pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    Tev, _, Cev = T.eventos_agresor(trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    b["lam1"] = T.M.lambda_bins(MOD["H1"], {"fecha": d, "t_ms": b["t_ms"], "T_us": Tev.astype(np.int64), "tipo": np.where(Cev, 0, 1).astype(np.int8)})
    r = {"fecha": str(d), "n": len(b["t_ms"])}; L2 = {}
    for lado in ("ask", "bid"):
        L = W.lls(MOD, b, lado, cols, deltas); y = b["conteos"][lado]
        for m in NOMS:
            r[f"ll_{m}_{lado}"] = float((y * L[m] - np.exp(L[m])).sum()); r[f"auc_{m}_{lado}"] = float(roc_auc_score(y[:, JD] > 0, L[m][:, JD]))
            r[f"O_{lado}"] = float(y[:, JD].sum()); r[f"E_{m}_{lado}"] = float(np.exp(L[m][:, JD]).sum()); L2[(m, lado)] = L[m][:, JD]
    i = b["barr_i"]
    ev = np.column_stack([b["barr_s"], b["conteos"]["ask"][i, JD], b["conteos"]["bid"][i, JD], b["S"][i, -1]] + [L2[(m, l)][i] for m in NOMS for l in ("ask", "bid")])
    return r, ev

def control_4sep():
    """Con el guarda original, el día 4 sep debe reproducir v109 (predicción) y v110 (economía)."""
    d = date(2026, 9, 4); r, _ = pred_dia(d); ref9 = {x["fecha"]: x for x in json.loads((RR / "17_test_predictivo" / "salida" / "por_dia_test_v109.json").read_text())}[str(d)]
    dp = max(abs(r[k] - ref9[k]) / max(abs(ref9[k]), 1e-12) for k in r if k.startswith("ll_"))
    e = E.dia(d); ref10 = json.loads((RR / "18_hjb_curva_interpolada" / "salida" / "por_dia_v110.json").read_text())[str(d)]
    de = max(max(abs(e[k]["n"] - ref10[k]["n"]), abs(e[k]["pnl"] - ref10[k]["pnl"])) for k in e if not k.startswith("_"))
    log(f"control 4 sep: predicción dif. relativa máx {dp:.2e}; economía dif. máx (ejecuciones/PnL) {de:.2e}")
    return dp < 1e-9 and de < 1e-9, {"pred_dif_rel_max": dp, "econ_dif_max": de}

def guarda_sim(d):
    if not (date(2026, 9, 20) <= d <= date(2026, 10, 26)):
        raise PermissionError(f"v111: {d} fuera de la simulación (21 sep–26 oct; 20 sep solo para la tendencia)")

def bootstrap(num, den, IDX):
    return [float(num.sum() / den.sum()), *map(float, np.percentile(num[IDX].sum(1) / den[IDX].sum(1), [2.5, 97.5]))]

if __name__ == "__main__":
    t_ini = time.time(); ok, ctrl = control_4sep()
    (SAL / "control_v111.json").write_text(json.dumps(ctrl, indent=1))
    if not ok:
        log("CONTROL FALLIDO: no se abre la simulación"); sys.exit(1)
    T.T0, T.T1, T.guardia_test = date(2026, 9, 21), date(2026, 10, 26), guarda_sim   # único cambio: el guarda de fechas
    por_pred, evs, por_econ = [], [], {}
    for d in T.fechas("2026-09-21", "2026-10-26"):
        t = time.time(); r, ev = pred_dia(d); por_pred.append(r); evs.append(ev); e = por_econ[str(d)] = E.dia(d)
        log(f"{d} ({time.time() - t:.0f} s): AUC E3 ask {r['auc_E3-fkX+B_ask']:.3f} | HJB E3 {1e4 * e['E3-fkX+B|HJBx']['pnl'] / max(e['E3-fkX+B|HJBx']['nocional'], 1e-9):+.2f} bps, {e['E3-fkX+B|HJBx']['n']} ejec.")
        (SAL / "por_dia_pred_v111.json").write_text(json.dumps(por_pred, indent=1)); (SAL / "por_dia_econ_v111.json").write_text(json.dumps(por_econ, indent=1))
    Ev = np.vstack(evs); np.save(SAL / "eventos_v111.npy", Ev)
    # ---------------- predicción
    nd = len(por_pred); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd)); n = np.array([x["n"] for x in por_pred], float)
    REF = "E3-fkX+B"; pred = {}
    for l in ("ask", "bid"):
        e1 = sum(x[f"ll_{REF}_{l}"] - x[f"ll_E1_{l}"] for x in por_pred)
        for m in NOMS[1:]:
            dif = np.array([x[f"ll_{REF}_{l}"] - x[f"ll_{m}_{l}"] for x in por_pred])
            pred[f"{m}_{l}"] = {"dll": bootstrap(dif, n, IDX), "dias": int((dif > 0).sum()), "auc": float(np.mean([x[f"auc_{m}_{l}"] for x in por_pred])),
                                "parte_vs_AS": float(1 - dif.sum() / e1) if m != "E1" else 0.0}
        pred[f"auc_{REF}_{l}"] = float(np.mean([x[f"auc_{REF}_{l}"] for x in por_pred]))
    s, sube, nan = Ev[:, 0], Ev[:, 3] > 0, np.isnan(Ev[:, 3]); brechas = {}
    for k, m in enumerate(NOMS):
        la, lb = np.exp(Ev[:, 4 + 2 * k]), np.exp(Ev[:, 5 + 2 * k])
        ba = sum(x["O_ask"] for x in por_pred) / sum(x[f"E_{m}_ask"] for x in por_pred); bb = sum(x["O_bid"] for x in por_pred) / sum(x[f"E_{m}_bid"] for x in por_pred)
        cel = {"vend": s < 0, "comp": s > 0, "vend_sube": (s < 0) & sube, "vend_baja": (s < 0) & ~sube & ~nan, "comp_sube": (s > 0) & sube, "comp_baja": (s > 0) & ~sube & ~nan}
        brechas[m] = {c: float((Ev[mm, 1].sum() / la[mm].sum() - ba) if c.startswith("vend") else (Ev[mm, 2].sum() / lb[mm].sum() - bb)) for c, mm in cel.items()}
    otros = ["E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S"]
    crit = {"C1_jerarquia": all(pred[f"{m}_{l}"]["dll"][1] > 0 for m in otros for l in ("ask", "bid")),
            "C2_dias_vs_E2m+S_>=30de36": all(pred[f"E2m+S_{l}"]["dias"] >= 30 for l in ("ask", "bid")),
            "C3_auc>=0,80": all(pred[f"auc_{REF}_{l}"] >= 0.80 for l in ("ask", "bid")),
            "C4_rebote<=0,15": abs(brechas[REF]["vend"]) <= 0.15 and abs(brechas[REF]["comp"]) <= 0.15}
    # ---------------- economía
    dias = list(por_econ); S = lambda k, c: np.array([por_econ[d][k][c] for d in dias], float); econ = {}
    for pol in ("MIOPE", "HJBx", "GLFT", "HJBa"):
        for m in MODELOS + (list(E.FIJOS) if pol == "MIOPE" else []):
            k = f"{m}|{pol}"; ref = f"{REF}|{pol}"; pa, pn = 1e4 * S(k, "pnl"), S(k, "nocional"); ra, rn = 1e4 * S(ref, "pnl"), S(ref, "nocional")
            dif = ra[IDX].sum(1) / rn[IDX].sum(1) - pa[IDX].sum(1) / pn[IDX].sum(1)
            econ[k] = {"ejec_dia": float(S(k, "n").mean()), "q_abs": float(S(k, "q_abs_medio").mean()), "pnl_usdt_dia": float(S(k, "pnl").mean()), "dias_pos": int((S(k, "pnl") > 0).sum()),
                       "bps": bootstrap(pa, pn, IDX), "mk10": bootstrap(S(k, "s10"), S(k, "n10"), IDX), "da0": float(S(k, "da0_med").mean()),
                       "neto_7.5": float(pa.sum() / pn.sum() - 7.5), "neto_10": float(pa.sum() / pn.sum() - 10.0),
                       "usdt_dia_neto_7.5": float((S(k, "pnl") - 7.5e-4 * pn).mean()), "dif_E3": [float(ra.sum() / rn.sum() - pa.sum() / pn.sum()), *map(float, np.percentile(dif, [2.5, 97.5]))]}
    # ---------------- por semana
    semanas = [("21–27 sep", "2026-09-21", "2026-09-27"), ("28 sep–4 oct", "2026-09-28", "2026-10-04"), ("5–11 oct", "2026-10-05", "2026-10-11"), ("12–18 oct", "2026-10-12", "2026-10-18"), ("19–26 oct", "2026-10-19", "2026-10-26")]
    sem = {}
    for nom, a, b_ in semanas:
        P = [x for x in por_pred if a <= x["fecha"] <= b_]; nn = sum(x["n"] for x in P); w = {}
        for l in ("ask", "bid"):
            w[f"auc_E3_{l}"] = float(np.mean([x[f"auc_{REF}_{l}"] for x in P]))
            for m in ("E1", "E2m+S", "E1+X49"): w[f"E3_menos_{m}_{l}"] = float(sum(x[f"ll_{REF}_{l}"] - x[f"ll_{m}_{l}"] for x in P) / nn)
        ds = [d for d in dias if a <= d <= b_]; k = f"{REF}|HJBx"
        w["hjb_E3_bps"] = float(1e4 * sum(por_econ[d][k]["pnl"] for d in ds) / sum(por_econ[d][k]["nocional"] for d in ds)); w["hjb_E3_ejec_dia"] = float(np.mean([por_econ[d][k]["n"] for d in ds])); w["dias"] = len(ds)
        sem[nom] = w
    fuera = {m: {kk: {"media": float(np.mean([por_econ[d]["_info"][m][kk] for d in dias])), "max_dia": float(np.max([por_econ[d]["_info"][m][kk] for d in dias]))}
                 for kk in por_econ[dias[0]]["_info"][m] if kk.startswith("frac")} for m in MODELOS}
    res = {"control_4sep": ctrl, "criterios": {k: bool(v) for k, v in crit.items()}, "prediccion": pred, "brechas": brechas, "economia": econ, "semanas": sem, "fuera_de_rango": fuera,
           "dias": nd, "segundos": round(time.time() - t_ini)}
    (SAL / "resultados_v111.json").write_text(json.dumps(res, indent=1)); log(f"criterios: {res['criterios']}"); log(f"FIN ({res['segundos']} s)")
