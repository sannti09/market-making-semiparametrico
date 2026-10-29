#!/usr/bin/env python3
"""v97: E3-fkX+B (49) frente a E3-fkX+BT (51 = 49 + dmid_15m, dmid_1h). Plan: PLAN_V97.md."""
import hashlib, json, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score
AQUI = Path(__file__).resolve().parent; R94 = AQUI.parent
assert hashlib.sha256((R94 / "PLAN_V97.md").read_bytes()).hexdigest() == (R94 / "PLAN_V97.sha256").read_text().split()[0]
sys.path.insert(0, str(AQUI))
import corrida_v94 as C94  # noqa: E402
V, FB = C94.V, C94.FB
from modelo_f import ModeloF, ModeloFKX  # noqa: E402
SAL = R94 / "salida"; CAC = SAL / "cache"; CAC.mkdir(parents=True, exist_ok=True)


def mids(d):
    if not (date(2026, 6, 29) <= d <= date(2026, 9, 3)):
        return np.array([], np.int64), np.array([])
    fe = pq.read_table(FB.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "mid"])
    sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool); m = fe["mid"].to_numpy(zero_copy_only=False).astype(float)
    return fe["ts_ms"].to_numpy(), np.where(sv & np.isfinite(m), m, np.nan)


def tendencia(t_ms, ts, mid):
    """Cambio del mid (bps) entre la última fila con ts ≤ t − w y la última con ts ≤ t."""
    out = []
    r = np.searchsorted(ts, t_ms, side="right") - 1
    for w in (900_000, 3_600_000):
        r0 = np.searchsorted(ts, t_ms - w, side="right") - 1; ok = (r >= 0) & (r0 >= 0)
        out.append(np.where(ok, (mid[np.maximum(r, 0)] / mid[np.maximum(r0, 0)] - 1) * 1e4, np.nan))
    return np.column_stack(out)


def tend_dia(d, t_ms):
    p = CAC / f"tend_{d}.npy"
    if p.exists():
        return np.load(p)
    ta, ma = mids(d - timedelta(days=1)); tb, mb = mids(d)
    T = tendencia(np.asarray(t_ms, np.int64), np.concatenate([ta, tb]), np.concatenate([ma, mb])); np.save(p, T); return T


def test_no_fuga(d, t_ms):
    ta, ma = mids(d - timedelta(days=1)); tb, mb = mids(d); ts, mid = np.concatenate([ta, tb]), np.concatenate([ma, mb])
    t_ms = np.asarray(t_ms, np.int64); corte = t_ms[len(t_ms) // 2]; A = tendencia(t_ms, ts, mid); k = ts <= corte
    B = tendencia(t_ms, ts[k], mid[k]); s = t_ms <= corte
    return bool(np.array_equal(np.nan_to_num(A[s], nan=-9), np.nan_to_num(B[s], nan=-9)))


def dia(d):
    b = C94.dia(d); b["XT"] = np.hstack([b["XB"], tend_dia(d, b["t_ms"])]); return b


if __name__ == "__main__":
    for d in (date(2026, 7, 3), date(2026, 8, 27)):
        assert test_no_fuga(d, C94.dia(d)["t_ms"]), d
    print("no fuga OK", flush=True)
    aj = [dia(d) for d in V.C.fechas("2026-06-29", "2026-07-12")]
    deltas, cols = np.asarray(aj[0]["deltas_bps"], float), aj[0]["columnas_x"]; jd = int(np.where(deltas == 2.0)[0][0])
    hora = np.concatenate([d["hora_utc"] for d in aj]).astype(int); e = np.concatenate([d["exposicion_s"] for d in aj])
    XS = {"B": np.vstack([d["XB"] for d in aj]), "BT": np.vstack([d["XT"] for d in aj])}; M = {}
    for lado in ("ask", "bid"):
        c = np.vstack([d["conteos"][lado] for d in aj]); Za = V.covariables(XS["B"][:, :44], cols, lado)
        mu, sd = np.nanmean(Za, 0), np.nanstd(Za, 0); sd = np.where(sd > 0, sd, 1.0); kw = dict(estimador="gbm", usar_h=V.USAR_H[lado], n_backfit=3, params_gbm=V.PARAMS)
        M[lado] = {"mu": mu, "sd": sd}
        for k, X in XS.items():
            ef = ModeloF(**kw).ajustar(X, hora, c, e, deltas); M[lado][k] = ModeloFKX(f_ini=ef.f, **kw).ajustar(X, V.est(Za, mu, sd), hora, c, e, deltas)
            print(lado, k, flush=True)
    dias = [d for d in V.C.fechas("2026-07-17", "2026-09-03") if not (date(2026, 8, 22) <= d <= date(2026, 8, 25))]
    porD, evs = [], []
    for d in dias:
        b = dia(d); h, ex = b["hora_utc"].astype(int), b["exposicion_s"]; r = {"fecha": str(d), "n": len(h)}; LL = {}
        for lado in ("ask", "bid"):
            Z = V.est(V.covariables(b["XB"][:, :44], cols, lado), M[lado]["mu"], M[lado]["sd"]); cc = b["conteos"][lado]
            for k, X in (("B", b["XB"]), ("BT", b["XT"])):
                L = M[lado][k].log_lam(X, h, deltas, Z); lam = np.exp(L) * ex[:, None]; LL[(k, lado)] = L[:, jd]
                r[f"ll_{k}_{lado}"] = float((cc * L - lam).sum()); r[f"O_{lado}"] = float(cc[:, jd].sum()); r[f"E_{k}_{lado}"] = float(lam[:, jd].sum())
                r[f"auc_{k}_{lado}"] = float(roc_auc_score(cc[:, jd] > 0, lam[:, jd]))
        porD.append(r)
        ev = C94.EV.get(d.isoformat(), {}).get(C94.CLAVE)
        ts00 = pq.read_table(FB.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms"])["ts_ms"].to_numpy()
        t_ev = ts00[ev[:, 0].astype(int)]; tb = b["t_ms"]; j = np.searchsorted(tb, t_ev, side="right"); ok = j < len(tb); j2 = np.minimum(j, len(tb) - 1); ok &= (tb[j2] - t_ev) <= 1000; i = j2[ok]
        evs.append(np.column_stack([ev[ok, 1], b["conteos"]["ask"][i, jd], b["conteos"]["bid"][i, jd], ex[i], b["XT"][i, -1]] + [LL[(k, l)][i] for k in ("B", "BT") for l in ("ask", "bid")]))
        print(d, flush=True)
    E = np.vstack(evs); nd = len(porD); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd)); n = np.array([p["n"] for p in porD], float)
    lin, out = [f"{nd} días"], {}
    for lado in ("ask", "bid"):
        dif = np.array([p[f"ll_BT_{lado}"] - p[f"ll_B_{lado}"] for p in porD]); bs = dif[IDX].sum(1) / n[IDX].sum(1); lo, hi = np.percentile(bs, [2.5, 97.5])
        aB, aT = np.mean([p[f"auc_B_{lado}"] for p in porD]), np.mean([p[f"auc_BT_{lado}"] for p in porD])
        out[lado] = {"dll": [dif.sum() / n.sum(), lo, hi, int((dif > 0).sum())], "auc": [aB, aT]}
        lin.append(f"{lado}: Δll (BT−B) {dif.sum() / n.sum():+.4f} [{lo:+.4f}; {hi:+.4f}] por bin, BT gana {int((dif > 0).sum())}/{nd}; AUC {aB:.4f} → {aT:.4f}")
    s, sube = E[:, 0], E[:, 4] > 0
    for k, (ia, ib) in (("B", (5, 6)), ("BT", (7, 8))):
        la, lb = np.exp(E[:, ia]) * E[:, 3], np.exp(E[:, ib]) * E[:, 3]
        ba = sum(p["O_ask"] for p in porD) / sum(p[f"E_{k}_ask"] for p in porD); bb = sum(p["O_bid"] for p in porD) / sum(p[f"E_{k}_bid"] for p in porD)
        g = lambda m, O, lam, base: O[m].sum() / lam[m].sum() - base
        r = {"venta": g(s < 0, E[:, 1], la, ba), "compra": g(s > 0, E[:, 2], lb, bb),
             "venta_alza1h": g((s < 0) & sube, E[:, 1], la, ba), "venta_baja1h": g((s < 0) & ~sube, E[:, 1], la, ba),
             "compra_alza1h": g((s > 0) & sube, E[:, 2], lb, bb), "compra_baja1h": g((s > 0) & ~sube, E[:, 2], lb, bb)}
        out[f"brechas_{k}"] = r; lin.append(f"{k}: brechas " + " | ".join(f"{a} {v:+.3f}" for a, v in r.items()))
    c1 = out["brechas_BT"]["venta"] < out["brechas_B"]["venta"] and abs(out["brechas_BT"]["compra"]) <= abs(out["brechas_B"]["compra"]) + 0.02
    c2 = all(out[l]["dll"][1] >= 0 for l in ("ask", "bid")); c3 = all(out[l]["auc"][1] >= out[l]["auc"][0] - 0.005 for l in ("ask", "bid"))
    out["criterios"] = {"C1_rebote": bool(c1), "C2_ll": bool(c2), "C3_auc": bool(c3)}; lin.append(f"CRITERIOS: {out['criterios']}")
    (SAL / "resultados_v97.json").write_text(json.dumps(out, indent=1)); (SAL / "tablas_v97.md").write_text("\n".join(lin)); print("\n".join(lin))
