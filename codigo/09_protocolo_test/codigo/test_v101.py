#!/usr/bin/env python3
"""v101: congelar modelos (ajuste 29 jun–31 jul), compuerta de reproducción, y evaluación única en el test 4–20 sep. Ver PREREGISTRO_TEST_V101.md."""
import hashlib, json, pickle, sys, time
from datetime import date, timedelta
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent; R = AQUI.parent; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PREREGISTRO_TEST_V101.md").read_bytes()).hexdigest() == (R / "PREREGISTRO_TEST_V101.sha256").read_text().split()[0]
assert hashlib.sha256((R / "ENMIENDA_V101B.md").read_bytes()).hexdigest() == (R / "ENMIENDA_V101B.sha256").read_text().split()[0]
for p in ("03_cargador_datos/codigo", "04_covariables_barrido/codigo", "07_modelos_as_hawkes/paquete"):
    sys.path.insert(0, str(RR / p))
import cargador_v98 as N  # noqa: E402
import corrida_v97 as C97  # noqa: E402
import e12_colab as M  # noqa: E402
C94 = C97.C94; V, FB = C94.V, C94.FB
from datos_capa_100ms import eventos_agresor  # noqa: E402
from modelo_e3_semiparametrico import ModeloE3Semiparametrico  # noqa: E402
from modelo_f import ModeloF, ModeloFKX  # noqa: E402
LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "test_v101.log").write_text("\n".join(LOG))
def fechas(a, b):
    d, o = date.fromisoformat(a), []
    while d <= date.fromisoformat(b): o.append(d); d += timedelta(days=1)
    return o
DEL = V.DISTANCIAS_BPS_DEF

# ------------------------------------------------------------ fase A: ajuste y congelación (solo ≤ 3 sep, cachés de v98/v94)
def dia_aj(d):
    b = N.bins(d, DEL); t = b["t_ms"]; B5 = FB.feats_dia(d, t); T2 = C97.tend_dia(d, t)
    b["X49"] = np.hstack([b["X"].astype(float), B5]); b["S"] = np.hstack([B5, T2]); return b
def aj_glm(Lam, y, hora, Z, deltas, n_it=3):
    mu, sd = np.nanmean(Z, 0), np.nanstd(Z, 0); sd = np.where(sd > 0, sd, 1.0); Zs = np.clip(np.nan_to_num((Z - mu) / sd), -5, 5)
    eta = np.zeros(len(y)); Y = y.sum(1)
    for _ in range(n_it):
        p = M.ajustar_nivel_forma(Lam * np.exp(eta), y, hora, deltas, "f", True)
        w = Lam * np.exp(p["niv"][hora] + np.log(np.exp(p["sh"]).sum()))
        g = PoissonRegressor(alpha=1e-6, max_iter=300).fit(Zs, Y / w, sample_weight=w); eta = Zs @ g.coef_ + g.intercept_
    return {"p": M.ajustar_nivel_forma(Lam * np.exp(eta), y, hora, deltas, "f", True), "g": g, "mu": mu, "sd": sd}
def L_glm(m, Lam, hora, Z):
    return M.log_lam(m["p"], Lam * np.exp(np.clip(np.nan_to_num((Z - m["mu"]) / m["sd"]), -5, 5) @ m["g"].coef_ + m["g"].intercept_), hora)

def log_lams(MOD, b, lado, cols, deltas):
    """log λ (n, 9) de todos los modelos para un día ya preparado (claves X49, S, XT, hora, t_ms, lam2)."""
    i = M.LADOS[lado]; h = b["hora_utc"].astype(int); out = {}
    Z = V.est(V.covariables(b["X49"][:, :44], cols, lado), MOD["mu"][lado], MOD["sd"][lado])
    out["E3"] = MOD["E3"][lado].eta(b["X49"][:, :44], h)[:, None] - MOD["E3"][lado].k * deltas[None, :]
    out["E3-fkX"] = MOD["E3-fkX"][lado].log_lam(b["X49"][:, :44], h, deltas, Z)
    out["E3-fkX+B"] = MOD["E3-fkX+B"][lado].log_lam(b["X49"], h, deltas, Z)
    one = np.ones(len(h)); lam2 = b["lam2"][:, i]
    out["E1+h-f"] = M.log_lam(MOD["E1+h-f"][lado], one, h); out["E2m+h-f"] = M.log_lam(MOD["E2m+h-f"][lado], lam2, h)
    out["E1+S"] = L_glm(MOD["E1+S"][lado], one, h, b["S"]); out["E2m+S"] = L_glm(MOD["E2m+S"][lado], lam2, h, b["S"])
    out["E1+X49"] = L_glm(MOD["E1+X49"][lado], one, h, b["X49"])
    return out

def fase_A(fin):
    aj = [dia_aj(d) for d in fechas("2026-06-29", fin)]
    deltas, cols = np.asarray(aj[0]["deltas_bps"], float), aj[0]["columnas_x"]
    hora = np.concatenate([b["hora_utc"] for b in aj]).astype(int); e = np.concatenate([b["exposicion_s"] for b in aj])
    X49 = np.vstack([b["X49"] for b in aj]); S = np.vstack([b["S"] for b in aj]); log(f"ajuste cargado: {len(hora)} bins")
    MOD = {k: {} for k in ("E3", "E3-fkX", "E3-fkX+B", "E1+h-f", "E2m+h-f", "E1+S", "E2m+S", "E1+X49", "mu", "sd")}
    # Hawkes de 2 escalas (como v100b): eventos del paquete (mismos archivos canónicos)
    pk = [M.cargar(str(RR / "07_modelos_as_hawkes" / "paquete"), d) for d in fechas("2026-06-29", fin)]
    H2 = M.ajustar_hawkes(M.intervalos(pk[::3]), [(bl, br) for bl in (0.05, 0.2, 1.0) for br in (20.0, 80.0, 300.0, 1000.0)], log=log)
    MOD["H2"] = H2; LAM2 = np.vstack([M.lambda_bins(H2, b) for b in pk]); del pk
    for lado in ("ask", "bid"):
        i = M.LADOS[lado]; c = np.vstack([b["conteos"][lado] for b in aj]); Za = V.covariables(X49[:, :44], cols, lado)
        mu, sd = np.nanmean(Za, 0), np.nanstd(Za, 0); sd = np.where(sd > 0, sd, 1.0); Zs = V.est(Za, mu, sd); MOD["mu"][lado], MOD["sd"][lado] = mu, sd
        kw = dict(estimador="gbm", usar_h=V.USAR_H[lado], n_backfit=3, params_gbm=V.PARAMS)
        MOD["E3"][lado] = ModeloE3Semiparametrico(**kw).ajustar(X49[:, :44], hora, c, e, deltas)
        for nom, X in (("E3-fkX", np.ascontiguousarray(X49[:, :44])), ("E3-fkX+B", X49)):
            ef = ModeloF(**kw).ajustar(X, hora, c, e, deltas); MOD[nom][lado] = ModeloFKX(f_ini=ef.f, **kw).ajustar(X, Zs, hora, c, e, deltas)
        y = c.astype(float); one = np.ones(len(y))
        MOD["E1+h-f"][lado] = M.ajustar_nivel_forma(one, y, hora, deltas, "f", True)
        MOD["E2m+h-f"][lado] = M.ajustar_nivel_forma(LAM2[:, i], y, hora, deltas, "f", True)
        MOD["E1+S"][lado] = aj_glm(one, y, hora, S, deltas); MOD["E2m+S"][lado] = aj_glm(LAM2[:, i], y, hora, S, deltas)
        MOD["E1+X49"][lado] = aj_glm(one, y, hora, X49, deltas); log(f"{lado}: modelos ajustados")
    return MOD, deltas, cols

def compuerta(MOD, deltas, cols):
    d = date(2026, 8, 1); b = dia_aj(d); pk = M.cargar(str(RR / "07_modelos_as_hawkes" / "paquete"), d); b["lam2"] = M.lambda_bins(MOD["H2"], pk)
    ref98 = {r["fecha"]: r for r in json.loads((RR / "03_cargador_datos" / "salida" / "por_dia_v98.json").read_text())}[str(d)]
    ref100 = {r["fecha"]: r for r in json.loads((RR / "07_modelos_as_hawkes" / "por_dia_v100.json").read_text())}[str(d)]
    ok = True
    for lado in ("ask", "bid"):
        L = log_lams(MOD, b, lado, cols, deltas); y = b["conteos"][lado]
        for m, ref in (("E3-fkX+B", ref98), ("E2m+S", ref100), ("E1+X49", ref100)):
            v = float((y * L[m] - np.exp(L[m])).sum()); r = ref[f"ll_{m}_{lado}"]; dr = abs(v - r) / abs(r); ok &= dr < 1e-9
            log(f"compuerta {m} {lado}: {v:.4f} vs {r:.4f} (dif rel {dr:.2e})")
    return ok

# ------------------------------------------------------------ fase B: test (4–20 sep), acceso explícito
T0, T1 = date(2026, 9, 4), date(2026, 9, 20)
def guardia_test(d):
    if not (date(2026, 9, 3) <= d <= T1):
        raise PermissionError(f"v101: {d} fuera del test (4–20 sep; 3 sep solo para la tendencia)")
def mids_test(d):
    guardia_test(d)
    fe = pq.read_table(N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "mid"])
    sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool); m = fe["mid"].to_numpy(zero_copy_only=False).astype(float)
    return fe["ts_ms"].to_numpy(), np.where(sv & np.isfinite(m), m, np.nan)
def dia_test(d, deltas, MOD):
    assert T0 <= d <= T1; guardia_test(d)
    N.guardia = guardia_test; FB.guardia = guardia_test          # el cargador y las covariables leen con la guardia del test
    b = N.construir(d, DEL); t = b["t_ms"]
    tr, fe = FB.leer(d); B5 = FB.calcular(np.asarray(t, np.int64), tr, fe)
    ta, ma = mids_test(d - timedelta(days=1)); tb_, mb = mids_test(d); T2 = C97.tendencia(np.asarray(t, np.int64), np.concatenate([ta, tb_]), np.concatenate([ma, mb]))
    b["X49"] = np.hstack([b["X"].astype(float), B5]); b["S"] = np.hstack([B5, T2])
    trd = pq.read_table(N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "qty", "aggressor_buy"])
    tt, tp, ta_ = trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool)
    Tev, _, Cev = eventos_agresor(tt, tp, ta_)
    b["lam2"] = M.lambda_bins(MOD["H2"], {"fecha": d, "t_ms": t, "T_us": Tev.astype(np.int64), "tipo": np.where(Cev, 0, 1).astype(np.int8)})
    # barridos (definición de v92: mismo instante y lado, recorrido ≥ 0,5 bps; separación ≥ 10,1 s)
    nuevo = np.ones(len(tt), bool); nuevo[1:] = (tt[1:] != tt[:-1]) | (ta_[1:] != ta_[:-1]); st = np.nonzero(nuevo)[0]; en = np.concatenate([st[1:], [len(tt)]]) - 1
    sd = np.where(ta_[st], 1, -1); rec = sd * (tp[en] - tp[st]) / tp[st] * 1e4; m = rec >= 0.5; tev, sev = tt[en][m] / 1000.0, sd[m]
    keep, last = [], -1e18
    for k in range(len(tev)):
        if tev[k] >= last + 10100:
            keep.append(k); last = tev[k]
    tev, sev = tev[keep], sev[keep]; j = np.searchsorted(t, tev, side="right"); ok = j < len(t); j2 = np.minimum(j, len(t) - 1); ok &= (t[j2] - tev) <= 1000
    b["barr_i"], b["barr_s"] = j2[ok], sev[ok]; return b

def fase_B(MOD, deltas, cols):
    jd = int(np.where(deltas == 2.0)[0][0]); por_dia, evs = [], []
    nombres = ["E3-fkX+B", "E3", "E3-fkX", "E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S"]
    for d in fechas("2026-09-04", "2026-09-20"):
        b = dia_test(d, deltas, MOD); r = {"fecha": str(d), "n": len(b["t_ms"])}; L2 = {}
        for lado in ("ask", "bid"):
            L = log_lams(MOD, b, lado, cols, deltas); y = b["conteos"][lado]
            for m in nombres:
                r[f"ll_{m}_{lado}"] = float((y * L[m] - np.exp(L[m])).sum()); r[f"auc_{m}_{lado}"] = float(roc_auc_score(y[:, jd] > 0, L[m][:, jd]))
                r[f"O_{lado}"] = float(y[:, jd].sum()); r[f"E_{m}_{lado}"] = float(np.exp(L[m][:, jd]).sum()); L2[(m, lado)] = L[m][:, jd]
        por_dia.append(r); i = b["barr_i"]
        evs.append(np.column_stack([b["barr_s"], b["conteos"]["ask"][i, jd], b["conteos"]["bid"][i, jd], b["S"][i, -1]] + [L2[(m, l)][i] for m in nombres for l in ("ask", "bid")]))
        log(f"test {d}: {r['n']} bins, {len(i)} barridos")
    (SAL / "por_dia_test_v101.json").write_text(json.dumps(por_dia, indent=1)); E = np.vstack(evs); np.save(SAL / "eventos_test_v101.npy", E)
    return por_dia, E, nombres

def analisis(por_dia, E, nombres):
    nd = len(por_dia); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd)); n = np.array([r["n"] for r in por_dia], float)
    REF = "E3-fkX+B"; out, lin = {}, [f"TEST 4–20 sep: {nd} días"]
    for l in ("ask", "bid"):
        tot = sum(r[f"ll_{REF}_{l}"] - r[f"ll_E1+h-f_{l}"] for r in por_dia); lin.append(f"\n=== {l} === (parte = % de la mejora de {REF} sobre E1+h-f)")
        for m in nombres[1:]:
            dif = np.array([r[f"ll_{REF}_{l}"] - r[f"ll_{m}_{l}"] for r in por_dia]); bs = dif[IDX].sum(1) / n[IDX].sum(1); lo, hi = np.percentile(bs, [2.5, 97.5])
            parte = sum(r[f"ll_{m}_{l}"] - r[f"ll_E1+h-f_{l}"] for r in por_dia) / tot
            out[f"{m}_{l}"] = {"dll": float(dif.sum() / n.sum()), "ic": [float(lo), float(hi)], "dias": int((dif > 0).sum()), "parte": float(parte),
                               "auc": float(np.mean([r[f"auc_{m}_{l}"] for r in por_dia]))}
            x = out[f"{m}_{l}"]; lin.append(f"{m:9} E3 − m {x['dll']:+.4f} [{lo:+.4f}; {hi:+.4f}] gana {x['dias']}/{nd} | parte {100 * parte:6.1f} % | AUC {x['auc']:.4f}")
        out[f"auc_{REF}_{l}"] = float(np.mean([r[f"auc_{REF}_{l}"] for r in por_dia])); lin.append(f"AUC {REF} {out[f'auc_{REF}_{l}']:.4f}")
    s, sube, nan = E[:, 0], E[:, 3] > 0, np.isnan(E[:, 3])
    cel = {"vend": s < 0, "comp": s > 0, "vend_sube": (s < 0) & sube, "vend_baja": (s < 0) & ~sube & ~nan, "comp_sube": (s > 0) & sube, "comp_baja": (s > 0) & ~sube & ~nan}
    for k, m in enumerate(nombres):
        la, lb = np.exp(E[:, 4 + 2 * k]), np.exp(E[:, 5 + 2 * k])
        ba = sum(r["O_ask"] for r in por_dia) / sum(r[f"E_{m}_ask"] for r in por_dia); bb = sum(r["O_bid"] for r in por_dia) / sum(r[f"E_{m}_bid"] for r in por_dia)
        br = {c: float((E[mm, 1].sum() / la[mm].sum() - ba) if c.startswith("vend") else (E[mm, 2].sum() / lb[mm].sum() - bb)) for c, mm in cel.items()}
        out[f"brechas_{m}"] = br; lin.append(f"brechas {m}: " + " | ".join(f"{c} {v:+.3f}" for c, v in br.items()))
    otros = ["E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S"]
    crit = {"C1_jerarquia": all(out[f"{m}_{l}"]["ic"][0] > 0 for m in otros for l in ("ask", "bid")),
            "C2_consistencia_vs_E2m+S": all(out[f"E2m+S_{l}"]["dias"] >= 14 for l in ("ask", "bid")),
            "C3_auc>=0,80": all(out[f"auc_{REF}_{l}"] >= 0.80 for l in ("ask", "bid")),
            "C4_rebote<=0,15": abs(out[f"brechas_{REF}"]["vend"]) <= 0.15 and abs(out[f"brechas_{REF}"]["comp"]) <= 0.15}
    out["criterios"] = {k: bool(v) for k, v in crit.items()}; lin.append(f"\nCRITERIOS PRERREGISTRADOS: {out['criterios']}")
    (SAL / "resultados_test_v101.json").write_text(json.dumps(out, indent=1)); (SAL / "tablas_test_v101.md").write_text("\n".join(lin)); log("\n".join(lin))

if __name__ == "__main__":
    MOD, deltas, cols = fase_A("2026-07-31")
    if not compuerta(MOD, deltas, cols):
        log("COMPUERTA FALLIDA: no se abre el test"); sys.exit(1)
    log("compuerta superada; reajuste final con 29 jun–3 sep (enmienda v101b)"); del MOD
    MOD, deltas, cols = fase_A("2026-09-03")
    p = SAL / "modelos" / "modelos_congelados_v101.pkl"; pickle.dump({"MOD": MOD, "deltas": deltas, "cols": cols}, open(p, "wb"))
    man = {"hora_congelacion": time.strftime("%Y-%m-%d %H:%M:%S %z"), "pkl_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "preregistro_sha256": (R / "PREREGISTRO_TEST_V101.sha256").read_text().split()[0], "enmienda_v101b_sha256": (R / "ENMIENDA_V101B.sha256").read_text().split()[0], "ventana_ajuste": "2026-06-29..2026-09-03"}
    (SAL / "modelos" / "MANIFIESTO_CONGELACION.json").write_text(json.dumps(man, indent=1)); log(f"CONGELADO: {man}")
    log("abriendo el test (primera lectura de 4–20 sep)")
    analisis(*fase_B(MOD, deltas, cols))
