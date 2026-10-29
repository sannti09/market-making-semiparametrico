#!/usr/bin/env python3
"""v94 paso 1: E3-fkX (44 covariables) frente a E3-fkX+B (44 + 5 de barrido). Plan: PLAN_V94.md."""
import hashlib, json, pickle, sys
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent; R94 = AQUI.parent; RR = R94.parent
assert hashlib.sha256((R94 / "PLAN_V94.md").read_bytes()).hexdigest() == (R94 / "PLAN_V94.sha256").read_text().split()[0]
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RR / "05_curva_distancia" / "codigo"))
import corrida_v90 as V  # noqa: E402
import feats_v94 as FB  # noqa: E402
from modelo_f import ModeloF, ModeloFKX  # noqa: E402

EV = pickle.load(open(RR / "04_covariables_barrido" / "eventos_barridos" / "salida" / "eventos_v92.pkl", "rb")); CLAVE = ("T", 0.5, 1, 10)
TCAC = R94 / "salida" / "cache"; TCAC.mkdir(parents=True, exist_ok=True)
SAL = R94 / "salida"


def dia(d):
    b = V.bins(d); p = TCAC / f"tms_{d}.npy"
    t = np.load(p) if p.exists() else V.C.construir_bins_v58(d, V.DISTANCIAS_BPS_DEF)["t_ms"]
    np.save(p, t); assert len(t) == len(b["hora_utc"])
    b["t_ms"] = t; b["XB"] = np.hstack([b["X"].astype(float), FB.feats_dia(d, t)]); return b


def main():
    aj = [dia(d) for d in V.C.fechas("2026-06-29", "2026-07-12")]
    deltas, cols = np.asarray(aj[0]["deltas_bps"], float), aj[0]["columnas_x"]; jd = int(np.where(deltas == 2.0)[0][0])
    hora = np.concatenate([d["hora_utc"] for d in aj]).astype(int); e = np.concatenate([d["exposicion_s"] for d in aj])
    XA = {"E3-fkX": np.vstack([d["X"] for d in aj]).astype(float), "E3-fkX+B": np.vstack([d["XB"] for d in aj])}
    M = {}
    for lado in ("ask", "bid"):
        c = np.vstack([d["conteos"][lado] for d in aj])
        Za = V.covariables(XA["E3-fkX"], cols, lado); mu, sd = np.nanmean(Za, 0), np.nanstd(Za, 0); sd = np.where(sd > 0, sd, 1.0)
        kw = dict(estimador="gbm", usar_h=V.USAR_H[lado], n_backfit=3, params_gbm=V.PARAMS)
        M[lado] = {"mu": mu, "sd": sd}
        for nom, X in XA.items():
            ef = ModeloF(**kw).ajustar(X, hora, c, e, deltas)
            M[lado][nom] = ModeloFKX(f_ini=ef.f, **kw).ajustar(X, V.est(Za, mu, sd), hora, c, e, deltas)
            print(lado, nom, "ll ajuste", round(M[lado][nom].historial[-1]["ll_pp"]), flush=True)
    dias = [d for d in V.C.fechas("2026-07-17", "2026-09-03") if not (date(2026, 8, 22) <= d <= date(2026, 8, 25))]
    porD, evs = [], []
    for d in dias:
        b = dia(d); X44, h, ex = b["X"].astype(float), b["hora_utc"].astype(int), b["exposicion_s"]
        LL = {}
        for lado in ("ask", "bid"):
            Z = V.est(V.covariables(X44, cols, lado), M[lado]["mu"], M[lado]["sd"])
            for nom in XA:
                LL[(nom, lado)] = M[lado][nom].log_lam(X44 if nom == "E3-fkX" else b["XB"], h, deltas, Z)
        r = {"fecha": str(d), "n": len(h)}
        for nom in XA:
            for lado in ("ask", "bid"):
                L = LL[(nom, lado)]; c = b["conteos"][lado]; lam = np.exp(L) * ex[:, None]
                r[f"ll_{nom}_{lado}"] = float((c * L - lam).sum()); r[f"ll2_{nom}_{lado}"] = float((c[:, jd] * L[:, jd] - lam[:, jd]).sum())
                r[f"O_{lado}"] = float(c[:, jd].sum()); r[f"E_{nom}_{lado}"] = float(lam[:, jd].sum())
                r[f"auc_{nom}_{lado}"] = float(roc_auc_score(c[:, jd] > 0, lam[:, jd]))
        porD.append(r)
        ev = EV.get(d.isoformat(), {}).get(CLAVE)
        ts00 = pq.read_table(FB.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms"])["ts_ms"].to_numpy()
        t_ev = ts00[ev[:, 0].astype(int)]; tb = b["t_ms"]
        j = np.searchsorted(tb, t_ev, side="right"); ok = j < len(tb); j2 = np.minimum(j, len(tb) - 1); ok &= (tb[j2] - t_ev) <= 1000
        i = j2[ok]
        fila = [np.full(len(i), d.toordinal()), ev[ok, 1], ev[ok, 2] - ev[ok, 3], b["conteos"]["ask"][i, jd], b["conteos"]["bid"][i, jd], ex[i]]
        for nom in XA:
            fila += [LL[(nom, "ask")][i, jd], LL[(nom, "bid")][i, jd]]
        evs.append(np.column_stack(fila)); print(d, len(i), flush=True)
    (SAL / "por_dia_v94.json").write_text(json.dumps(porD, indent=1)); np.save(SAL / "eventos_v94.npy", np.vstack(evs))


if __name__ == "__main__":
    main()
