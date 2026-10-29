#!/usr/bin/env python3
"""v102: walk-forward semanal dentro del entrenamiento. Plan: PLAN_V102.md. Reutiliza las funciones de v101 (importadas, sin editar)."""
import hashlib, json, sys, time
from datetime import date, timedelta
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
AQUI = Path(__file__).resolve().parent; R = AQUI.parent; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V102.md").read_bytes()).hexdigest() == (R / "PLAN_V102.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "101_test_p1_20261029_01" / "codigo"))
import test_v101 as T  # noqa: E402  (solo funciones; no ejecuta nada al importar)
M, V, C94 = T.M, T.V, T.C94
PAQ = str(RR / "99_colab_e1_e2_20261029_01" / "paquete")
FOLDS = [("2026-07-31", "2026-08-01", "2026-08-07"), ("2026-08-07", "2026-08-08", "2026-08-14"), ("2026-08-14", "2026-08-15", "2026-08-21"),
         ("2026-08-21", "2026-08-22", "2026-08-28"), ("2026-08-28", "2026-08-29", "2026-09-03")]
NOMS = ["E3-fkX+B", "E3-fkX", "E3", "E1", "E1+h-f", "E1+S", "E1+X49", "E2+h-f", "E2+S", "E2m+h-f", "E2m+S"]
LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "wf_v102.log").write_text("\n".join(LOG))

def f_cerrada(c):
    """f inicial de E3-fkX = la que devuelve ModeloF (f_j = log N_j/N_1, monótona): solo depende de los conteos, no del GBM."""
    N = np.maximum(c.sum(0).astype(float), 0.5); return np.minimum.accumulate(np.log(N / N[0]))

def ajustar(fin):
    aj = [T.dia_aj(d) for d in T.fechas("2026-06-29", fin)]
    deltas, cols = np.asarray(aj[0]["deltas_bps"], float), aj[0]["columnas_x"]
    hora = np.concatenate([b["hora_utc"] for b in aj]).astype(int); e = np.concatenate([b["exposicion_s"] for b in aj])
    X49 = np.vstack([b["X49"] for b in aj]); S = np.vstack([b["S"] for b in aj])
    pk = [M.cargar(PAQ, d) for d in T.fechas("2026-06-29", fin)]
    H2 = M.ajustar_hawkes(M.intervalos(pk[::3]), [(bl, br) for bl in (0.05, 0.2, 1.0) for br in (20.0, 80.0, 300.0, 1000.0)], log=lambda s: None)
    H1 = M.ajustar_hawkes(M.intervalos(pk[::3]), [(b,) for b in (0.05, 0.2, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)], log=lambda s: None)
    LAM2 = np.vstack([M.lambda_bins(H2, b) for b in pk]); LAM1 = np.vstack([M.lambda_bins(H1, b) for b in pk]); del pk
    MOD = {k: {} for k in NOMS + ["mu", "sd"]}; MOD["H2"], MOD["H1"] = H2, H1
    for lado in ("ask", "bid"):
        i = M.LADOS[lado]; c = np.vstack([b["conteos"][lado] for b in aj]); Za = V.covariables(X49[:, :44], cols, lado)
        mu, sd = np.nanmean(Za, 0), np.nanstd(Za, 0); sd = np.where(sd > 0, sd, 1.0); MOD["mu"][lado], MOD["sd"][lado] = mu, sd
        kw = dict(estimador="gbm", usar_h=V.USAR_H[lado], n_backfit=3, params_gbm=V.PARAMS)
        MOD["E3-fkX+B"][lado] = T.ModeloFKX(f_ini=f_cerrada(c), **kw).ajustar(X49, V.est(Za, mu, sd), hora, c, e, deltas)
        X44 = np.ascontiguousarray(X49[:, :44]); MOD["E3-fkX"][lado] = T.ModeloFKX(f_ini=f_cerrada(c), **kw).ajustar(X44, V.est(Za, mu, sd), hora, c, e, deltas)
        MOD["E3"][lado] = T.ModeloE3Semiparametrico(**kw).ajustar(X44, hora, c, e, deltas); del X44
        y = c.astype(float); one = np.ones(len(y))
        MOD["E1+h-f"][lado] = M.ajustar_nivel_forma(one, y, hora, deltas, "f", True); MOD["E2m+h-f"][lado] = M.ajustar_nivel_forma(LAM2[:, i], y, hora, deltas, "f", True)
        MOD["E1"][lado] = M.ajustar_nivel_forma(one, y, hora, deltas, "k", False); MOD["E2+h-f"][lado] = M.ajustar_nivel_forma(LAM1[:, i], y, hora, deltas, "f", True)
        MOD["E2+S"][lado] = T.aj_glm(LAM1[:, i], y, hora, S, deltas)
        MOD["E1+S"][lado] = T.aj_glm(one, y, hora, S, deltas); MOD["E2m+S"][lado] = T.aj_glm(LAM2[:, i], y, hora, S, deltas); MOD["E1+X49"][lado] = T.aj_glm(one, y, hora, X49, deltas)
    return MOD, deltas, cols

def lls(MOD, b, lado, cols, deltas):
    i = M.LADOS[lado]; h = b["hora_utc"].astype(int); one = np.ones(len(h)); lam2 = b["lam2"][:, i]; lam1 = b["lam1"][:, i]
    Z = V.est(V.covariables(b["X49"][:, :44], cols, lado), MOD["mu"][lado], MOD["sd"][lado])
    X44 = b["X49"][:, :44]
    return {"E3-fkX+B": MOD["E3-fkX+B"][lado].log_lam(b["X49"], h, deltas, Z), "E3-fkX": MOD["E3-fkX"][lado].log_lam(X44, h, deltas, Z),
            "E3": MOD["E3"][lado].eta(X44, h)[:, None] - MOD["E3"][lado].k * deltas[None, :], "E1": M.log_lam(MOD["E1"][lado], one, h),
            "E2+h-f": M.log_lam(MOD["E2+h-f"][lado], lam1, h), "E2+S": T.L_glm(MOD["E2+S"][lado], lam1, h, b["S"]), "E1+h-f": M.log_lam(MOD["E1+h-f"][lado], one, h),
            "E2m+h-f": M.log_lam(MOD["E2m+h-f"][lado], lam2, h), "E1+S": T.L_glm(MOD["E1+S"][lado], one, h, b["S"]),
            "E2m+S": T.L_glm(MOD["E2m+S"][lado], lam2, h, b["S"]), "E1+X49": T.L_glm(MOD["E1+X49"][lado], one, h, b["X49"])}

def evaluar(MOD, deltas, cols, dias, k, tipo, evs):
    jd = int(np.where(deltas == 2.0)[0][0]); out = []
    for d in dias:
        b = T.dia_aj(d); pkd = M.cargar(PAQ, d); b["lam2"] = M.lambda_bins(MOD["H2"], pkd); b["lam1"] = M.lambda_bins(MOD["H1"], pkd); r = {"fecha": str(d), "n": len(b["t_ms"]), "fold": k, "tipo": tipo}; L2 = {}
        for lado in ("ask", "bid"):
            L = lls(MOD, b, lado, cols, deltas); y = b["conteos"][lado]
            for m in NOMS:
                r[f"ll_{m}_{lado}"] = float((y * L[m] - np.exp(L[m])).sum()); r[f"auc_{m}_{lado}"] = float(roc_auc_score(y[:, jd] > 0, L[m][:, jd]))
                r[f"O_{lado}"] = float(y[:, jd].sum()); r[f"E_{m}_{lado}"] = float(np.exp(L[m][:, jd]).sum()); L2[(m, lado)] = L[m][:, jd]
        out.append(r)
        if evs is not None:
            ev = C94.EV.get(d.isoformat(), {}).get(C94.CLAVE)
            import pyarrow.parquet as pq
            ts00 = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms"])["ts_ms"].to_numpy()
            t_ev = ts00[ev[:, 0].astype(int)]; tb = b["t_ms"]; j = np.searchsorted(tb, t_ev, side="right"); ok = j < len(tb); j2 = np.minimum(j, len(tb) - 1); ok &= (tb[j2] - t_ev) <= 1000; i = j2[ok]
            evs.append(np.column_stack([np.full(len(i), k), ev[ok, 1], b["conteos"]["ask"][i, jd], b["conteos"]["bid"][i, jd], b["S"][i, -1]] + [L2[(m, l)][i] for m in NOMS for l in ("ask", "bid")]))
    return out

if __name__ == "__main__":
    filas, evs = [], []
    for k, (fin, e0, e1) in enumerate(FOLDS, 1):
        if (SAL / f"fold{k}.json").exists():
            filas += json.loads((SAL / f"fold{k}.json").read_text()); evs.append(np.load(SAL / f"fold{k}_ev.npy")); continue
        t0 = time.time(); MOD, deltas, cols = ajustar(fin); log(f"ventana {k}: ajuste hasta {fin} ({time.time() - t0:.0f} s)")
        fd = date.fromisoformat(fin); ins = T.fechas((fd - timedelta(days=6)).isoformat(), fin)
        filas += evaluar(MOD, deltas, cols, T.fechas(e0, e1), k, "fuera", evs) + evaluar(MOD, deltas, cols, ins, k, "dentro", None)
        nuevas = [r for r in filas if r["fold"] == k]; (SAL / f"fold{k}.json").write_text(json.dumps(nuevas)); np.save(SAL / f"fold{k}_ev.npy", evs[-1])
        (SAL / "por_dia_v102.json").write_text(json.dumps(filas, indent=1)); log(f"ventana {k}: evaluada {e0}–{e1} y dentro de muestra {ins[0]}–{ins[-1]}")
        del MOD
    np.save(SAL / "eventos_v102.npy", np.vstack(evs)); log("FIN")
